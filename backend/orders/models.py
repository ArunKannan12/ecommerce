from django.db import models
from django.contrib.auth import get_user_model
from products.models import ProductVariant
from promoter.models import Promoter
from delivery.models import DeliveryMan
from decimal import Decimal
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

User = get_user_model()
phone_regex = RegexValidator(regex=r'^[6-9]\d{9}$', message="Enter a valid 10-digit phone number")
pin_regex = RegexValidator(regex=r'^\d{6}$', message="Enter a valid 6-digit postal code")

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, validators=[phone_regex])
    address = models.TextField()

    # Location fields
    locality = models.CharField(max_length=100, blank=True, null=True)# User-selected from dropdown
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50,blank=True,null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=6, validators=[pin_regex])
    country = models.CharField(max_length=50, default="India")
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    def __str__(self):
        return f"{self.full_name} ({self.locality}, {self.city}, {self.state})"


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentMethod(models.TextChoices):
    COD = 'Cash on Delivery', 'Cash on Delivery'
    RAZORPAY = 'Razorpay', 'Razorpay'


class Order(models.Model):
    REFUND_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("initiated", "Initiated"),
        ("processed", "Processed"),
        ("failed", "Failed"),
        ("not_applicable", "Not Applicable"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promoter = models.ForeignKey(Promoter, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commission_applied = models.BooleanField(default=False)

    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    status = models.CharField(choices=OrderStatus.choices, default=OrderStatus.PENDING, max_length=20)

    subtotal=models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    delivery_charge=models.DecimalField( max_digits=10, decimal_places=2,default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    is_paid = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)
    is_restocked = models.BooleanField(default=False)

    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cancellation & Refund
    cancel_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_orders')
    cancelled_by_role = models.CharField(max_length=20, blank=True, null=True)
    refund_id = models.CharField(max_length=100, blank=True, null=True)
    refund_status = models.CharField(max_length=50, choices=REFUND_STATUS_CHOICES,default='not_applicable')
    refunded_at = models.DateTimeField(blank=True, null=True)
    
    refund_finalized = models.BooleanField(default=False)
    # Razorpay
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    # Delivery
    delivered_by = models.ForeignKey(DeliveryMan, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_delivered')

    def __str__(self):
        return f"Order #{self.id} ({self.user.email} — {self.status})"

    def restock_items(self):
        if self.status == OrderStatus.CANCELLED and not self.is_restocked:
            for item in self.orderitem_set.all():
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save()
            self.is_restocked = True
            self.save(update_fields=['is_restocked'])

    def save(self, *args, **kwargs):
        if self.pk:
            old = Order.objects.get(pk=self.pk)
            if old.status != OrderStatus.CANCELLED and self.status == OrderStatus.CANCELLED:
                self.restock_items()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),

        ]


class OrderItemStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PICKED = 'picked', 'Picked'
    PACKED = 'packed', 'Packed'
    SHIPPED = 'shipped', 'Shipped'
    CANCELLED = 'cancelled', 'Cancelled'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=OrderItemStatus.choices, default=OrderItemStatus.PENDING)
    packed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} × {self.product_variant} (Order #{self.order.id})"


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('refunded', 'Refunded'),
    ]

    REFUND_METHOD_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
        ('manual', 'Manual'),
    ]

    PICKUP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('rejected_pickup', 'Rejected at pickup'),
        ('damaged', 'Rejected - Damaged'),
    ]
    
    DECISION_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("escalated", "Escalated"),
    ]

    # Links
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, null=True, blank=True, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')

    reason = models.TextField()

    # High-level return flow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Refund
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES, default='razorpay')
    user_upi = models.CharField(max_length=100,blank=True,default='')

    # Pickup by deliveryman
    pickup_status = models.CharField(max_length=20, choices=PICKUP_STATUS_CHOICES, default='pending')
    pickup_verified_by = models.ForeignKey(DeliveryMan, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_returns')
    pickup_comment = models.TextField(blank=True, null=True)

    # Warehouse decision
    warehouse_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default="pending")
    warehouse_comment = models.TextField(blank=True, null=True)

    # Admin decision
    admin_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default="pending")
    admin_comment = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order_item'],
                condition=~models.Q(status='refunded'),
                name='unique_active_return_per_item'
            )
        ]

    def mark_refunded(self, amount=None):
        if amount:
            self.refund_amount = amount
        self.status = 'refunded'
        self.refunded_at = timezone.now()
        self.save(update_fields=['status', 'refunded_at', 'refund_amount'])

    def clean(self):
        # Only one active return request per item
        if self.order_item:
            exists = ReturnRequest.objects.filter(
                order_item=self.order_item
            ).exclude(pk=self.pk).exclude(status='refunded').exists()
            if exists:
                raise ValidationError("A return is already in progress for this item.")

        # Max refundable amount
        max_refund = (
            (self.order_item.price or Decimal('0.00')) * self.order_item.quantity
            if self.order_item else self.order.total or Decimal('0.00')
        )
        if self.order_item and hasattr(self.order, "delivery_charge") and self.order.delivery_charge:
            total_items_price = sum(item.price * item.quantity for item in self.order.orderitem_set.all())
            if total_items_price > 0:
                item_share_of_delivery = (self.order_item.price * self.order_item.quantity / total_items_price) * self.order.delivery_charge
                max_refund += item_share_of_delivery

        # Require UPI for COD/manual/wallet refunds
        if self.refund_method in ['upi', 'manual', 'wallet']:
            if self.order.payment_method == 'Cash on Delivery' and not self.user_upi:
                raise ValidationError({"user_upi": "UPI ID is required for COD/manual refunds."})
        else:
            # Clear UPI if refund method does not require it
            self.user_upi = ""

        super().clean()

    def __str__(self):
        if self.order_item:
            return f"ReturnRequest for Item #{self.order_item.id} in Order #{self.order.id}"
        return f"ReturnRequest for Order #{self.order.id}"
