# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem, Notification, OrderItemStatus


def send_multichannel_notification(user, order=None, order_item=None, event=None, message=None, channels=["email", "whatsapp"]):
    """
    Create notifications for multiple channels (email, WhatsApp, SMS).
    Sends HTML emails for email channel.
    """
    for channel in channels:
        notif = Notification.objects.create(
            user=user,
            order=order,
            order_item=order_item,
            channel=channel,
            event=event,
            message=message,
        )
        notif.send_notification()
# -------------------------
# Order Placement
# -------------------------
@receiver(post_save, sender=Order)
def notify_order_placed(sender, instance, created, **kwargs):
    if created:
        if not Notification.objects.filter(order=instance, event="order_placed").exists():
            send_multichannel_notification(
                user=instance.user,
                order=instance,
                event="order_placed",
                message=f"✅ Your order {instance.order_number} has been placed successfully.",
                channels=["email"]
            )


# -------------------------
# Order Cancellation
# -------------------------
@receiver(post_save, sender=Order)
def notify_order_cancelled(sender, instance, created, **kwargs):
    if not created and instance.status == "cancelled":
        if not Notification.objects.filter(order=instance, event="order_cancelled").exists():
            send_multichannel_notification(
                user=instance.user,
                order=instance,
                event="order_cancelled",
                message=f"❌ Your order {instance.order_number} has been cancelled.",
                channels=["email"]
            )


# -------------------------
# Delivery Confirmation
# -------------------------
@receiver(post_save, sender=OrderItem)
def notify_item_delivered(sender, instance, created, **kwargs):
    if not created and instance.status == OrderItemStatus.DELIVERED:
        if not Notification.objects.filter(order_item=instance, event="delivered").exists():
            send_multichannel_notification(
                user=instance.order.user,
                order=instance.order,
                order_item=instance,
                event="delivered",
                message=f"📦 Your item {instance.id} has been delivered successfully.",
                channels=["email"]
            )


# -------------------------
# Refund / Replacement
# -------------------------
@receiver(post_save, sender=OrderItem)
def notify_item_refund_replace(sender, instance, created, **kwargs):
    if not created:
        if instance.status == "refunded" and not Notification.objects.filter(order_item=instance, event="refunded").exists():
            send_multichannel_notification(
                user=instance.order.user,
                order=instance.order,
                order_item=instance,
                event="refunded",
                message=f"💵 Your item {instance.id} has been refunded.",
                channels=["email"]
            )
        elif instance.status == "replaced" and not Notification.objects.filter(order_item=instance, event="replaced").exists():
            send_multichannel_notification(
                user=instance.order.user,
                order=instance.order,
                order_item=instance,
                event="replaced",
                message=f"🔄 Your item {instance.id} has been replaced with a new one.",
                channels=["email"]
            )


# -------------------------
# Return Pickup OTP
# -------------------------
def send_return_pickup_otp(order_item, channels=["email", "whatsapp"]):
    """Send OTP to customer for return/replacement pickup."""
    send_multichannel_notification(
        user=order_item.order.user,
        order=order_item.order,
        order_item=order_item,
        event="otp_return",
        message=f"🔐 Your OTP for pickup of item {order_item.id} is being generated.",
        channels=channels,
    )
