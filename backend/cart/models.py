from django.db import models
from django.contrib.auth import get_user_model
from products.models import ProductVariant
User=get_user_model()
# Create your models here.
class Cart(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email
    

class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE)
    product_variant=models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity=models.IntegerField(default=1)
    added_at=models.DateTimeField( auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product_variant')