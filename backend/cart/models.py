from django.db import models
from django.contrib.auth import get_user_model
from products.models import ProductVariant
User=get_user_model()
# Create your models here.
class Cart(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.cartitem_set.all())

    @property
    def total_price(self):
        return sum(item.quantity * item.product_variant.price for item in self.cartitem_set.all())

    def __str__(self):
        return self.user.email
    

class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity=models.IntegerField(default=1)
    added_at=models.DateTimeField( auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product_variant')

    @property
    def price(self):
        return self.product_variant.price

    @property
    def subtotal(self):
        return self.quantity * self.price