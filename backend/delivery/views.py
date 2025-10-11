# delivery/views.py
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from rest_framework.exceptions import ValidationError, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import DeliveryMan, DeliveryManRequest
from .serializers import DeliveryManSerializer, DeliveryManRequestSerializer
from delivery.permissions import IsDeliveryMan, IsDeliveryManOrAdmin
from orders.models import Order, OrderItem, Notification, OrderItemStatus
from promoter.utils import apply_promoter_commission
from orders.signals import send_multichannel_notification
from .utils import build_orders_dict

def send_otp_notification(item, force_new=False):
    """
    Send or resend OTP for a single order item (Out-for-Delivery only).
    The notification will include only this item.
    """

    # Get active (unverified) OTP notifications for this item
    notifs = Notification.objects.filter(
        order_item=item, event="otp_delivery", otp_verified=False
    ).order_by("-created_at")

    # Reuse existing OTP if still valid
    if not force_new and notifs.exists():
        latest_notif = notifs.first()
        otp_age = (timezone.now() - latest_notif.created_at).total_seconds()
        if otp_age < 300:  # 5 minutes
            return False  # OTP already sent recently

    # Expire old OTPs
    if notifs.exists():
        notifs.update(otp_verified=True)

    # Create new notification for this specific item
    new_notif = Notification.objects.create(
        user=item.order.user,
        order=item.order,
        order_item=item,
        event="otp_delivery",
        message="",  # will be updated below
        channel="email",  # OTP via email only for now
        payload={},
    )

    # Generate OTP (stored internally in Notification)
    otp_code = new_notif.generate_otp(ttl_seconds=300, force_new=True)

    # Update message — only reference this single item
    new_notif.message = (
        f"🔐 Your OTP for '{item.product_variant.product.name}' in order {item.order.order_number} "
        f"is {otp_code}. It expires in 5 minutes."
    )
    new_notif.save(update_fields=["message", "updated_at"])

    # Send notification
    new_notif.send_notification()

    return True

def mark_item_delivered(item):
    """Mark a single item as delivered"""
    if item.status == OrderItemStatus.DELIVERED:
        return
    item.status = OrderItemStatus.DELIVERED
    item.delivered_at = timezone.now()
    item.save(update_fields=["status","delivered_at"])

    order = item.order
    # Mark order delivered if all items delivered
    if not order.orderitem_set.exclude(status=OrderItemStatus.DELIVERED).exists():
        order.status = "delivered"
        order.delivered_at = timezone.now()
        order.save(update_fields=["status","delivered_at"])
        apply_promoter_commission(order)

    send_multichannel_notification(
        user=item.order.user,
        order=order,
        order_item=item,
        event="delivered",
        message=f"📦 Your item '{item.product_variant.product.name}' in order {order.order_number} has been delivered.",
        channels="email"
    )


# -------------------------
# Unified Delivery Actions
# -------------------------
class DeliveryActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryMan]

    @transaction.atomic
    def post(self, request):
        action = request.data.get("action")
        order_number = request.data.get("order_number")
        order_item_id = request.data.get("order_item_id")
        otp = request.data.get("otp")
        user = request.user

        deliveryman = get_object_or_404(DeliveryMan, user=user)
        # SEND OTP
        if action in ["send_otp", "resend_otp"]:
            if not order_item_id:
                return Response({"error": "order_item_id required"}, status=400)
            item = get_object_or_404(OrderItem, id=order_item_id)
          
            if action == "send_otp" and item.status != OrderItemStatus.OUT_FOR_DELIVERY:
                return Response({"error": "OTP can only be sent for out-for-delivery items"}, status=400)
            if action == "resend_otp" and item.status == OrderItemStatus.DELIVERED:
                return Response({"error": "Cannot resend OTP for delivered items"}, status=400)

            sent = send_otp_notification(item, force_new=(action=="resend_otp"))
            return Response({"success": "OTP sent successfully" if sent else "OTP already sent"}, status=200)

        # VERIFY OTP
        if action == "verify_otp":
            if not order_item_id or not otp:
                return Response({"error": "order_item_id and otp required"}, status=400)

            try:
                notif = Notification.objects.filter(
                    order_item_id=order_item_id, event="otp_delivery"
                ).latest("created_at")
            except Notification.DoesNotExist:
                return Response({"error": "No OTP found for this item"}, status=404)

            item = notif.order_item

            if item.status == OrderItemStatus.DELIVERED:
                return Response({"error": "Item already delivered"}, status=400)

            # Check if OTP is already used or expired
            if notif.otp_verified:
                return Response({"error": "OTP already used or expired"}, status=400)

            if hasattr(notif, "otp_expires_at") and notif.otp_expires_at and notif.otp_expires_at < timezone.now():
                notif.otp_verified = True  # mark it expired so it can't be reused
                notif.save(update_fields=["otp_verified", "updated_at"])
                return Response({"error": "OTP expired, please request a new one"}, status=400)

            # Verify OTP
            if notif.verify_otp(otp):
                mark_item_delivered(item)
                return Response({"success": "OTP verified and item delivered"}, status=200)

            return Response({"error": "Invalid OTP"}, status=400)


        # MARK ORDER FAILED
        if action == "mark_failed":
            if not order_number:
                return Response({"error": "order_number required"}, status=400)

            order = get_object_or_404(Order, order_number=order_number)

            # Check deliveryman assignment
            if order.delivered_by_id != deliveryman.id:
                return Response({"error": "Order assigned to another deliveryman"}, status=403)

            # Filter items currently out-for-delivery
            out_for_delivery_items = order.orderitem_set.filter(status=OrderItemStatus.OUT_FOR_DELIVERY)
            if not out_for_delivery_items.exists():
                return Response({"error": "No out-for-delivery items to mark failed"}, status=400)

            # Mark all out-for-delivery items as FAILED
            out_for_delivery_items.update(status=OrderItemStatus.FAILED)

            # Optional: you can mark delivered_by=None to indicate it needs rescheduling
            order.delivered_by = None
            order.save(update_fields=["delivered_by", "updated_at"])
            product_names = ", ".join([item.product_variant.product.name for item in order.orderitem_set.all()])

            # Notify user
            send_multichannel_notification(
                user=order.user,
                order=order,
                event="delivery_failed", 
                message=f"📦 Your order {order.order_number} containing {product_names} has been rescheduled for delivery.",
                channels="email"
            )

            return Response({"success": "Order items marked as failed"}, status=200)


        # -------------------------
        # RESCHEDULE FAILED ORDER
        # -------------------------
        if action == "reschedule":
            if not order_number:
                return Response({"error": "order_number required"}, status=400)

            order = get_object_or_404(Order, order_number=order_number)

            # Only items that were FAILED can be rescheduled
            failed_items = order.orderitem_set.filter(status=OrderItemStatus.FAILED)
            if not failed_items.exists():
                return Response({"error": "No failed items to reschedule"}, status=400)

            # Reschedule the items
            failed_items.update(status=OrderItemStatus.OUT_FOR_DELIVERY)

            # Assign deliveryman
            order.delivered_by = deliveryman
            order.save(update_fields=["delivered_by", "updated_at"])
            product_names = ", ".join([item.product_variant.product.name for item in order.orderitem_set.all()])

            # Notify user
            send_multichannel_notification(
                user=order.user,
                order=order,
                event="delivery_rescheduled",
                message=f"📦 Your order {order.order_number} containing {product_names} has been rescheduled for delivery.",
                channels="email"
            )

            return Response({"success": "Order items rescheduled for delivery"}, status=200)

        return Response({"error": "Invalid action"}, status=400)


# -------------------------
# Deliveryman Requests
# -------------------------
class DeliveryManRequestListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'admin':
            return DeliveryManRequest.objects.all().order_by('-applied_at')
        return DeliveryManRequest.objects.filter(user=user).order_by('-applied_at')


class DeliveryManRequestRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManRequestSerializer
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == "admin":
            return DeliveryManRequest.objects.all()
        return DeliveryManRequest.objects.filter(user=user, status="pending")

    def perform_update(self, serializer):
        request_obj = self.get_object()
        if request_obj.status != "pending":
            raise ValidationError("Only pending requests can be edited.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != "pending":
            raise ValidationError("Only pending requests can be deleted.")
        instance.delete()


# -------------------------
# Profile
# -------------------------
class DeliveryManProfileUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryManSerializer

    def get_object(self):
        user = self.request.user
        if getattr(user, 'role', '') != 'deliveryman':
            raise ValidationError("You are not approved as a deliveryman yet.")
        return get_object_or_404(DeliveryMan, user=user)


# -------------------------
# Dashboard
# -------------------------
class DeliveryDashboardAPIView(APIView):
    permission_classes = [IsDeliveryMan]

    def get(self, request):
        deliveryman = get_object_or_404(DeliveryMan, user=request.user)

        active_deliveries = OrderItem.objects.filter(
            order__delivered_by=deliveryman,
            status='out_for_delivery'
        ).count()

        completed_deliveries = Order.objects.filter(delivered_by=deliveryman, status='delivered').count()
        failed_deliveries = Order.objects.filter(delivered_by=deliveryman, status='failed').count()

        pending_otp_verification = OrderItem.objects.filter(
            order__delivered_by=deliveryman,
            status='out_for_delivery',
            notifications__event='otp_delivery',
            notifications__otp_verified=False
        ).count()

        return Response({
            "profile": {
                "name": request.user.get_full_name(),
                "phone": deliveryman.phone,
                "vehicle_number": deliveryman.vehicle_number,
                "joined_at": deliveryman.joined_at,
                "total_deliveries": deliveryman.total_deliveries,
                "earnings": deliveryman.earnings
            },
            "stats": {
                "active_deliveries": active_deliveries,
                "completed_deliveries": completed_deliveries,
                "failed_deliveries": failed_deliveries,
                "pending_otp_verification": pending_otp_verification
            }
        })


# -------------------------
# Delivery Details
class DeliveryDetailAPIView(APIView):
    permission_classes = [IsDeliveryMan]

    def get(self, request):
        deliveryman = get_object_or_404(DeliveryMan, user=request.user)
        order_items_qs = OrderItem.objects.filter(
            order__delivered_by=deliveryman,
            status__in=['out_for_delivery', 'failed']
        ).select_related(
            'order', 'product_variant', 'order__user', 'order__shipping_address'
        ).prefetch_related(
            'notifications'
        ).order_by('-order__assigned_at')

        orders = build_orders_dict(order_items_qs)

        # Optional: add more info per item if needed
        for order in orders:
            for item in order['items']:
                item['can_send_otp'] = item['pending_otp']

        return Response({"orders": orders})

