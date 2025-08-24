from django.db import models
from django.contrib.auth import get_user_model
from products.models import ProductVariant
from promoter.models import Promoter
from delivery.models import DeliveryMan
from decimal import Decimal


User = get_user_model()

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=50)
    address = models.TextField()

    # Location fields
    locality = models.CharField(max_length=100, blank=True, null=True)# User-selected from dropdown
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50,blank=True,null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promoter = models.ForeignKey(Promoter, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    commission = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
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
    refund_status = models.CharField(max_length=50, blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)

    # Razorpay
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    # Delivery
    delivered_by = models.ForeignKey(DeliveryMan, on_delete=models.CASCADE, null=True, blank=True, related_name='orders_delivered')

    def __str__(self):
        return f"Order #{self.id} ({self.user.email} — {self.status})"

    def restock_items(self):
        if self.status == OrderStatus.CANCELLED and not self.is_restocked:
            for item in self.orderitem_set.all():
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save()
            self.is_restocked = True

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
