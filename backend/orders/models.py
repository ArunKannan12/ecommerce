from django.db import models
from products.models import ProductVariant
from cart.models import CartItem
from django.contrib.auth import get_user_model
from promoter.models import Promoter
# Create your models here.
User=get_user_model()

class ShippingAddress(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    full_name=models.CharField( max_length=50)
    phone_number=models.CharField( max_length=50)
    address=models.TextField()
    city=models.CharField( max_length=50)
    postal_code=models.CharField( max_length=50)
    country=models.CharField( max_length=50)


    def __str__(self):
        return f" {self.full_name} ({self.city},{self.country})"

    
class Order(models.Model):
    STATUS_CHOICES=[
        ('pending','Pending'),
        ('processing','Processing'),
        ('shipped','Shipped'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled')
    ]

    user=models.ForeignKey(User, on_delete=models.CASCADE)
    promoter = models.ForeignKey(Promoter, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    commission=models.DecimalField( max_digits=5, decimal_places=2,default=0.0)
    commission_applied=models.BooleanField(default=False)
    shipping_address=models.ForeignKey(ShippingAddress,on_delete=models.CASCADE)
    status=models.CharField(choices=STATUS_CHOICES,default='pending',max_length=20)
    total=models.DecimalField( max_digits=10, decimal_places=2,default=0.00)
    payment_method=models.CharField( max_length=50,default='Cash on Delivery')
    is_paid=models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    cancel_reason = models.TextField(blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return f"{self.id} ({self.user.email}--{self.status})"
    
    def restock_items(self):
        if self.status == 'cancelled' and not hasattr(self, '_already_restocked'):
            for item in self.orderitem_set.all():
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save()
            self._already_restocked = True


    def save(self,*args,**kwargs):
        if self.pk:
            old=Order.objects.get(pk=self.pk)
            if old.status != 'cancelled' and self.status == 'cancelled':
                self.restock_items()
        super().save(*args,**kwargs)


class OrderItem(models.Model):
    order=models.ForeignKey(Order, on_delete=models.CASCADE)
    product_variant=models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=0)
    price=models.DecimalField( max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} X {self.product_variant}"
    

    