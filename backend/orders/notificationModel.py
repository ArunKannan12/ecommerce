from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import pyotp
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import requests  # for WhatsApp API or other external services

User = get_user_model()


NOTIFICATION_TITLES = {
    "order_placed": "Order Placed ✅",
    "order_shipped": "Order Shipped 🚚",
    "out_for_delivery": "Out for Delivery 📦",
    "delivered": "Delivered ✅",
    "cancelled": "Order Cancelled ❌",
    "return_requested": "Return Requested 🔄",
    "replacement_requested": "Replacement Requested 🔁",
    "otp_delivery": "Your OTP for Delivery 🔐",
    "otp_return": "Your OTP for Pickup 🔐",
}
class Notification(models.Model):

    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
        ("sms", "SMS"),
    ]

    EVENT_CHOICES = [
        ("order_placed", "Order Placed"),
        ("order_shipped", "Order Shipped"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("return_requested", "Return Requested"),
        ("replacement_requested", "Replacement Requested"),
        ("otp_delivery", "OTP for Delivery"),
        ("otp_return", "OTP for Return/Replacement Pickup"),  # <-- new event
    ]


    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,null=True,blank=True,related_name='notifications')
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)

    message = models.TextField(
        blank=True,
        help_text="Rendered message, with placeholders replaced from payload",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dynamic data (order_id, OTP, tracking_id, etc.)",
    )

    # OTP fields (for otp_delivery event)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    otp_expires_at=models.DateTimeField(null=True,blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    retries = models.PositiveIntegerField(
        default=0, help_text="Number of retry attempts for sending"
    )
    scheduled_at = models.DateTimeField(
        null=True, blank=True, help_text="Optional future time for sending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["channel", "event"]),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.email} - {self.event} - {self.channel} - {self.status}"

    # ---------------------------
    # State helpers
    # ---------------------------
    def mark_sent(self):
        self.status = "sent"
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])

    def mark_failed(self):
        self.status = "failed"
        self.retries += 1
        self.save(update_fields=["status", "retries", "updated_at"])

    @property
    def is_due(self):
        """Check if notification is scheduled and ready to send."""
        return (
            (self.scheduled_at is None or self.scheduled_at <= timezone.now())
            and self.status == "pending"
        )

    # ---------------------------
    # OTP helpers (pyotp only)
    # ---------------------------
    def generate_otp(self, ttl_seconds=300, force_new=False):
        """Generate a secure OTP using pyotp."""
        if self.event != "otp_delivery":
            raise ValueError("OTP can only be generated for delivery notifications.")

        if force_new or not self.otp_secret:
            # reset secret → guarantees a new OTP
            self.otp_secret = pyotp.random_base32()

        totp = pyotp.TOTP(self.otp_secret, interval=ttl_seconds)
        otp_code = totp.now()

        self.payload["otp"] = otp_code
        self.otp_expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)  # <-- NEW
        if self.channel == "email":
            self.message = (
                f"🔐 Your OTP is {otp_code}. It will expire in {ttl_seconds//60} minutes."
            )
        self.save(update_fields=["payload", "message", "updated_at","otp_secret","otp_expires_at"])
        return otp_code

    def verify_otp(self, code, ttl_seconds=300):
        """Verify OTP using pyotp."""
        if self.event != "otp_delivery" or not self.otp_secret:
            return False
        if self.otp_expires_at and self.otp_expires_at < timezone.now():
            self.otp_verified = True  # mark expired as used
            self.save(update_fields=["otp_verified", "updated_at"])
            return False
        totp = pyotp.TOTP(self.otp_secret, interval=ttl_seconds)
        is_valid = totp.verify(str(code), valid_window=1)

        if is_valid:
            self.otp_verified = True
            self.save(update_fields=["otp_verified", "updated_at"])

        return is_valid

    def send_notification(self):
        try:
            if self.channel == "email":
                self._send_email()
            else:
                raise ValueError("Unsupported channel")

            # Mark as sent
            self.mark_sent()

        except Exception as e:
            # Failed attempt
            self.mark_failed()
            # Optionally log error
            print(f"Failed to send notification {self.id}: {e}")
    def get_phone_number(self):
        if hasattr(self,'order_item') and self.order_item:
            return self.order_item.order.shipping_address.phone_number
        elif hasattr(self.user,'phone_number'):
            return self.user.phone_number
        else:
            return None
    # -------------------
    # Channel-specific sending
    # -------------------
    def _send_email(self):
        """
        Send email with HTML content and plain-text fallback.
        """
        subject = NOTIFICATION_TITLES.get(self.event, "Notification")
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [self.user.email]

        # Render HTML message from template
        html_content = render_to_string(
            "emails/notification.html",  # create this template
            {"notification": self}
        )

        # Fallback plain text
        text_content = self.message

        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

    # def _send_whatsapp(self):
    #     """Send notification via WhatsApp API (example)."""
    #     whatsapp_api_url = "https://api.whatsapp.com/send"
    #     phone = self.get_phone_number()  # assuming User model has phone_number
    #     if not phone:
    #         raise ValueError("No phone number available to send notification")
    #     payload = {
    #         "to": phone,
    #         "message": self.message,
    #     }
    #     # Replace this with actual WhatsApp API request
    #     response = requests.post(whatsapp_api_url, json=payload, timeout=5)
    #     if response.status_code != 200:
    #         raise Exception(f"WhatsApp send failed: {response.text}")

    # def _send_sms(self):
    #     """Send notification via SMS API (example)."""
    #     sms_api_url = "https://api.smsprovider.com/send"
    #     phone = self.user.phone_number
    #     payload = {"to": phone, "message": self.message}
    #     response = requests.post(sms_api_url, json=payload, timeout=5)
    #     if response.status_code != 200:
    #         raise Exception(f"SMS send failed: {response.text}")
        
