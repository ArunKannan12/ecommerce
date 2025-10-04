# delivery/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import DeliveryManSerializer,DeliveryManRequestSerializer
from rest_framework import status
from .models import DeliveryMan,DeliveryManRequest
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from orders.models import Order,OrderItem
from orders.models import Order
from promoter.utils import apply_promoter_commission
from delivery.permissions import IsDeliveryManOrAdmin,IsDeliveryMan
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView,ListCreateAPIView,RetrieveUpdateAPIView,RetrieveUpdateDestroyAPIView
from warehouse.serializers import WarehouseOrderSerializer
from delivery.models import DeliveryMan
from rest_framework.exceptions import NotFound
from orders.models import Notification,OrderItemStatus
from orders.signals import send_multichannel_notification

class MarkOrderDeliveredAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryManOrAdmin]

    @transaction.atomic
    def post(self, request, id):
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")
        
        if order.status.lower() == 'delivered':
            return Response({'message': 'Order is already marked as delivered.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.status.lower() != 'out_for_delivery':
            return Response({'message': 'Only out-for-delivery orders can be marked as delivered'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        deliveryman = None
        if getattr(user, 'role', None) == 'deliveryman':
            try:
                deliveryman = DeliveryMan.objects.get(user=user)
            except DeliveryMan.DoesNotExist:
                raise NotFound("No deliveryMan profile found. Please contact admin.")

            if order.delivered_by is None:
                order.delivered_by = deliveryman
            elif order.delivered_by != deliveryman:
                return Response({'message': 'This order is assigned to another deliveryman.'}, status=status.HTTP_403_FORBIDDEN)

        if order.payment_method.lower() == 'cash on delivery' and not order.is_paid:
            order.is_paid = True
            order.paid_at = timezone.now()

        order.status = 'delivered'
        order.delivered_at = timezone.now()
        for item in order.orderitem_set.all():
            item.status = 'delivered'
            item.delivered_at = timezone.now()
            item.save(update_fields=['status','delivered_at'])
        order.save(update_fields=['status','delivered_at','is_paid','paid_at','updated_at'])

        apply_promoter_commission(order)

        return Response({
            'message': 'Order marked as delivered.' + (' Payment marked as paid (COD).' if order.payment_method.lower() == 'cash on delivery' else ''),
            'order_id': order.id,
            'is_paid': order.is_paid,
            'commission': order.commission,
            'promoter': order.promoter.user.email if order.promoter else None,
            'delivered_by': deliveryman.user.email if deliveryman else None
        }, status=status.HTTP_200_OK)

class ShippedOrderForDeliveryAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDeliveryManOrAdmin]
    serializer_class = WarehouseOrderSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "delivered_by": ["exact"],
        "user": ["exact"],
        "assigned_at": ["gte", "lte"],
    }
    ordering_fields = ['created_at', 'assigned_at']
    ordering = ['-assigned_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return Order.objects.filter(
                status='out_for_delivery'
            ).select_related(
                "user", "delivered_by", "shipping_address"
            ).prefetch_related(
                Prefetch(
                    "orderitem_set",
                    queryset=OrderItem.objects.filter(status='out_for_delivery')
                )
            ).distinct().order_by('-created_at')

        try:
            deliveryman = DeliveryMan.objects.get(user=user)
        except DeliveryMan.DoesNotExist:
            raise NotFound("No deliveryman profile found.")

        return Order.objects.filter(
            delivered_by=deliveryman,
            status='out_for_delivery'
        ).select_related(
            "user", "delivered_by", "shipping_address"
        ).prefetch_related(
            Prefetch(
                "orderitem_set",
                queryset=OrderItem.objects.filter(status='out_for_delivery')
            )
        ).distinct().order_by('-assigned_at')
    
class DeliveryManRequestListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'admin':
            return DeliveryManRequest.objects.all().order_by('-applied_at')
        return DeliveryManRequest.objects.filter(user=user).order_by('-applied_at')
    
class DeliveryManRequestRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Allows the user to view, edit, or delete their pending deliveryman request.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManRequestSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'admin':
            return DeliveryManRequest.objects.all()
        return DeliveryManRequest.objects.filter(user=user, status='pending')

    def perform_update(self, serializer):
        request_obj = self.get_object()
        if request_obj.status != 'pending':
            raise ValidationError("Only pending requests can be edited.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != 'pending':
            raise ValidationError("Only pending requests can be deleted.")
        instance.delete()

class DeliveryManProfileUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManSerializer

    def get_object(self):
        user = self.request.user

        # Only approved deliverymen can access profile
        if getattr(user, 'role', '') != 'deliveryman':
            raise ValidationError("You are not approved as a deliveryman yet.")

        try:
            return DeliveryMan.objects.get(user=user)
        except DeliveryMan.DoesNotExist:
            raise NotFound("Deliveryman profile not found. Please contact admin.")



class MarkOrderDeliveryFailedAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryManOrAdmin]

    @transaction.atomic
    def post(self, request, id):
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        if order.status.lower() != 'out_for_delivery':
            return Response({'message': 'Only out-for-delivery orders can be marked as failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        deliveryman = None
        if getattr(user, 'role', None) == 'deliveryman':
            try:
                deliveryman = DeliveryMan.objects.get(user=user)
            except DeliveryMan.DoesNotExist:
                raise NotFound("No deliveryman profile found.")

            if order.delivered_by != deliveryman:
                return Response({'message': 'This order is assigned to another deliveryman.'},
                                status=status.HTTP_403_FORBIDDEN)

        order.status = 'failed'
        order.failed_at = timezone.now()
        order.save(update_fields=['status', 'failed_at', 'updated_at'])

        return Response({
            'message': 'Order marked as delivery failed.',
            'order_id': order.id,
            'failed_at': order.failed_at,
            'delivered_by': deliveryman.user.email if deliveryman else None
        }, status=status.HTTP_200_OK)


class SendDeliveryOTPAPIView(APIView):
    permission_classes = [IsDeliveryMan]

    def post(self, request, item_id):
        try:
            item = OrderItem.objects.get(id=item_id)
        except OrderItem.DoesNotExist:
            raise ValidationError("Invalid order item.")

        if item.status != OrderItemStatus.OUT_FOR_DELIVERY:
            raise ValidationError("OTP can only be sent when item is out for delivery.")

        # Only allow 2 OTP attempts total
        existing_otps = Notification.objects.filter(
            order_item=item, event="otp_delivery"
        ).order_by("-created_at")

        if existing_otps.count() >= 2:
            raise ValidationError("OTP has already been sent twice.")

        # Generate + send new OTP
        send_multichannel_notification(
            user=item.order.user,
            order=item.order,
            order_item=item,
            event="otp_delivery",
            message=f"🔐 Your OTP for item #{item.id} is being generated.",
            channels=["email", "whatsapp"],
        )

        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)


class ResendDeliveryOTPAPIView(APIView):
    permission_classes = [IsDeliveryMan]

    def post(self, request):
        order_item_id = request.data.get("order_item_id")
        if not order_item_id:
            return Response({"error": "order_item_id is required."}, status=400)

        try:
            order_item = OrderItem.objects.get(id=order_item_id)
        except OrderItem.DoesNotExist:
            return Response({"error": "Order item not found."}, status=404)

        # Prevent resending OTP if item is already delivered
        if order_item.status == OrderItemStatus.DELIVERED:
            return Response(
                {"error": "Cannot resend OTP. Item has already been delivered."},
                status=400,
            )

        # Fetch unverified notifications (email + whatsapp)
        notifs = Notification.objects.filter(
            order_item=order_item,
            event="otp_delivery",
            otp_verified=False,
        ).order_by("-created_at")

        if notifs.exists():
            # Always generate a new OTP (force new secret)
            otp_code = notifs.first().generate_otp(ttl_seconds=300, force_new=True)

            # Update all related notifs with the new OTP
            for notif in notifs:
                notif.payload['otp'] = otp_code
                notif.message = (
                    f"🔐 Your OTP for item #{order_item.id} is {otp_code}. "
                    f"It will expire in 5 minutes."
                )
                notif.save(update_fields=["message", "payload", "updated_at"])
                notif.send_notification()

            return Response({"success": "OTP resent successfully."}, status=200)

        # If no previous OTP → send a fresh one
        send_multichannel_notification(
            user=order_item.order.user,
            order=order_item.order,
            order_item=order_item,
            event="otp_delivery",
            message=f"🔐 Your OTP for item #{order_item.id} is being generated.",
            channels=["email", "whatsapp"],
        )
        return Response({"success": "OTP sent successfully."}, status=200)


class VerifyDeliveryOTPAPIView(APIView):
    permission_classes = [IsDeliveryMan]

    def post(self, request):
        order_item_id = request.data.get("order_item_id")
        otp = request.data.get("otp")

        if not order_item_id or not otp:
            raise ValidationError("Both order_item_id and otp are required.")

        try:
            notif = Notification.objects.filter(
                order_item_id=order_item_id,
                event="otp_delivery",
                otp_verified=False,
            ).latest("created_at")
        except Notification.DoesNotExist:
            return Response({"error": "No active OTP found for this item."}, status=404)

        order_item = notif.order_item
        if order_item.status == OrderItemStatus.DELIVERED:
            return Response({"error": "Item already delivered."}, status=400)

        if notif.verify_otp(otp):
            # OTP verification already marks otp_verified=True
            order_item.status = OrderItemStatus.DELIVERED
            order_item.delivered_at = timezone.now()
            order_item.save(update_fields=["status", "delivered_at"])

            # Update parent order if all items delivered
            order = order_item.order
            if not order.orderitem_set.exclude(status=OrderItemStatus.DELIVERED).exists():
                order.status = "delivered"
                order.delivered_at = timezone.now()
                order.save(update_fields=["status", "delivered_at"])

            return Response({"success": "OTP verified. Item marked as delivered."}, status=200)

        return Response({"error": "Invalid or expired OTP."}, status=400)
