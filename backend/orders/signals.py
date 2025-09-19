# orders/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order, OrderItem, Notification,OrderItemStatus

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
        # For OTP delivery, generate OTP only once and attach to all channels
        if event == "otp_delivery":
            otp_code = notif.generate_otp(ttl_seconds=300)
            notif.message = f"🔐 Your OTP for item #{order_item.id} is {otp_code}. It will expire in 5 minutes."
        notif.send_notification()


# -------------------------
# Order Placement
# -------------------------
@receiver(post_save, sender=Order)
def notify_order_placed(sender, instance, created, **kwargs):
    if created:
        send_multichannel_notification(
            user=instance.user,
            order=instance,
            event="order_placed",
            message=f"✅ Your order #{instance.id} has been placed successfully.",
            channels=["email"]  # start with email, add WhatsApp later
        )


# -------------------------
# Order Cancellation
# -------------------------
@receiver(pre_save, sender=Order)
def notify_order_cancelled(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if old_order.status != "cancelled" and instance.status == "cancelled":
        send_multichannel_notification(
            user=instance.user,
            order=instance,
            event="order_cancelled",
            message=f"❌ Your order #{instance.id} has been cancelled.",
            channels=["email"]
        )


# -------------------------
# Out for Delivery (OTP)
# -------------------------
@receiver(post_save, sender=OrderItem)
def create_delivery_otp(sender, instance, created, **kwargs):
    if not created and instance.status == OrderItemStatus.OUT_FOR_DELIVERY:
        if Notification.objects.filter(order_item=instance, event="otp_delivery").exists():
            return
        send_multichannel_notification(
            user=instance.order.user,
            order=instance.order,
            order_item=instance,
            event="otp_delivery",
            message=f"🔐 Your OTP for item #{instance.id} is being generated.",
            channels=["email", "whatsapp"]
        )


# -------------------------
# Delivery Confirmation
# -------------------------
@receiver(post_save, sender=OrderItem)
def notify_item_delivered(sender, instance, created, **kwargs):
    if not created and instance.status == "delivered":
        send_multichannel_notification(
            user=instance.order.user,
            order=instance.order,
            order_item=instance,
            event="delivered",
            message=f"📦 Your item #{instance.id} has been delivered successfully.",
            channels=["email"]
        )


# -------------------------
# Refund / Replacement
# -------------------------
@receiver(post_save, sender=OrderItem)
def notify_item_refund_replace(sender, instance, created, **kwargs):
    if not created:
        if instance.status == "refunded":
            send_multichannel_notification(
                user=instance.order.user,
                order=instance.order,
                order_item=instance,
                event="refunded",
                message=f"💵 Your item #{instance.id} has been refunded.",
                channels=["email"]
            )
        elif instance.status == "replaced":
            send_multichannel_notification(
                user=instance.order.user,
                order=instance.order,
                order_item=instance,
                event="replaced",
                message=f"🔄 Your item #{instance.id} has been replaced with a new one.",
                channels=["email"]
            )

def send_return_pickup_otp(order_item, channels=["email", "whatsapp"]):
    """Send OTP to customer for return/replacement pickup."""
    send_multichannel_notification(
        user=order_item.order.user,
        order=order_item.order,
        order_item=order_item,
        event="otp_return",
        message=f"🔐 Your OTP for pickup of item #{order_item.id} is being generated.",
        channels=channels,
    )
