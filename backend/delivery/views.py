# delivery/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import DeliveryManSerializer,DeliveryManRequestSerializer
from accounts.permissions import IsAdmin
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
from rest_framework.generics import ListAPIView
from warehouse.serializers import WarehouseOrderItemSerializer,WarehouseOrderSerializer
from delivery.models import DeliveryMan
from orders.filters import OrderFilter
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
        
        if order.status.lower() != 'shipped':
            return Response({'message': 'Only shipped orders can be marked as delivered'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        deliveryman = None
        if getattr(user, 'role', None) == 'deliveryman':
            try:
                deliveryman = DeliveryMan.objects.get(user=user)
            except DeliveryMan.DoesNotExist:
                raise NotFound("No deliveryMan profile found. Please contact admin.")

            # If order is unassigned, assign it to this deliveryman
            if order.delivered_by is None:
                order.delivered_by = deliveryman
            # If order is already assigned to another deliveryman, forbid action
            elif order.delivered_by != deliveryman:
                return Response({'message': 'This order is assigned to another deliveryman.'}, status=status.HTTP_403_FORBIDDEN)

        # COD: mark paid if not already
        if order.payment_method.lower() == 'cash on delivery' and not order.is_paid:
            order.is_paid = True
            order.paid_at = timezone.now()

        # Mark delivered
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        for item in order.orderitem_set.all():
            item.status='delivered'
            item.delivered_at=timezone.now()
            item.save(update_fields=['status','delivered_at'])
        order.save(update_fields=['status','delivered_at','is_paid','paid_at','updated_at'])

        # Apply promoter commission if applicable
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
        "status": ["exact"],                # order status
        "delivered_by": ["exact"],          # filter by deliveryman id
        "user": ["exact"],                  # customer id
        "assigned_at": ["gte", "lte"],      # assignment date range
    }
    ordering_fields = ['created_at', 'assigned_at']
    ordering = ['-assigned_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or getattr(user, 'role', '') == 'admin':
            # Admin/Warehouse → see all orders with shipped or out_for_delivery items
            return Order.objects.filter(
                Q(status='shipped') |
                Q(orderitem__status__in=['shipped', 'out_for_delivery'])
            ).select_related(
                "user", "delivered_by", "shipping_address"
            ).prefetch_related(
                Prefetch(
                    "orderitem_set",
                    queryset=OrderItem.objects.filter(status__in=['shipped','out_for_delivery'])
                )
            ).distinct().order_by('-created_at')

        # Deliveryman → only assigned orders with items out_for_delivery
        try:
            deliveryman = DeliveryMan.objects.get(user=user)
        except DeliveryMan.DoesNotExist:
            raise NotFound("No deliveryman profile found.")

        return Order.objects.filter(
            delivered_by=deliveryman,
            orderitem__status='out_for_delivery'

        ).filter(
            Q(status='shipped')
        ).select_related(
            "user", "delivered_by", "shipping_address"
        ).prefetch_related(
            Prefetch(
                "orderitem_set",
                queryset=OrderItem.objects.filter(status='out_for_delivery')
            )
        ).distinct().order_by('-assigned_at')



class DeliveryManRequestListCreateAPIView(ListAPIView,APIView):
    permission_classes=[IsAuthenticated]
    serializer_class=DeliveryManRequestSerializer

    def get_queryset(self):
        user=self.request.user

        if getattr(user,'role',None) == 'admin':
            return DeliveryManRequest.objects.all().order_by('-applied_at')
        return DeliveryManRequest.objects.filter(user=user).order_by('-applied_at')
    
    def post(self,request):
        serializer=DeliveryManRequestSerializer(data=request.data,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
class ApproveDeliveryManRequestAPIView(APIView):
    permission_classes=[IsAdmin]

    @transaction.atomic
    def post(self,request,request_id):
        try:
            dm_request=DeliveryManRequest.objects.get(id=request_id,status='pending')
        except DeliveryManRequest.DoesNotExist:
            raise NotFound("Deliveryman request not found or already reviewed")
        
        dm_request.status='approved'
        dm_request.reviewed_at=timezone.now()
        dm_request.save()

        DeliveryMan.objects.create(
            user=dm_request.user,
            phone=dm_request.phone,
            address=dm_request.address,
            vehicle_number=dm_request.vehicle_number
        )
        dm_request.user.role = 'deliveryman'
        dm_request.user.save()
        return Response({'message':'Deliveryman request approved and profile created'},status=status.HTTP_200_OK)
    

class RejectDeliveryManRequestAPIView(APIView):
    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request, request_id):
        try:
            dm_request = DeliveryManRequest.objects.get(id=request_id, status='pending')
        except DeliveryManRequest.DoesNotExist:
            raise NotFound("DeliveryMan request not found or already reviewed.")

        dm_request.status = 'rejected'
        dm_request.reviewed_at = timezone.now()
        dm_request.save()

        return Response({'message': 'DeliveryMan request rejected.'}, status=status.HTTP_200_OK)


class DeliveryManProfileUpdateAPIView(APIView):
    """
    Allows a deliveryman to update their own profile info (address, vehicle number, notes)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return DeliveryMan.objects.get(user=user)
        except DeliveryMan.DoesNotExist:
            raise NotFound("No deliveryman profile found. Please contact admin.")

    def get(self, request):
        deliveryman = self.get_object()
        serializer = DeliveryManSerializer(deliveryman)
        return Response(serializer.data)

    def patch(self, request):
        deliveryman = self.get_object()
        serializer = DeliveryManSerializer(deliveryman, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class MarkOrderDeliveryFailedAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryManOrAdmin]

    @transaction.atomic
    def post(self, request, id):
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Only allow if order is shipped or out_for_delivery
        if order.status.lower() not in ['out_for_delivery']:
            return Response({'message': 'Only shipped or out-for-delivery orders can be marked as failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        deliveryman = None
        if getattr(user, 'role', None) == 'deliveryman':
            try:
                deliveryman = DeliveryMan.objects.get(user=user)
            except DeliveryMan.DoesNotExist:
                raise NotFound("No deliveryman profile found.")

            # Check if assigned
            if order.delivered_by != deliveryman:
                return Response({'message': 'This order is assigned to another deliveryman.'},
                                status=status.HTTP_403_FORBIDDEN)

        order.status = 'failed'
        order.failed_at = timezone.now()
        order.save(update_fields=['status', 'failed_at', 'updated_at'])

        return Response({
            'message': 'Order marked as delivery failed.',
            'order_id': order.id,
            'failed_at':order.failed_at if order.failed_at else '',
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
