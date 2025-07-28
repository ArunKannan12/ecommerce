from django.contrib.auth import get_user_model
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer
from rest_framework import serializers
from .models import Cart,CartItem

User=get_user_model()
# Create your models here.


class CartSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Cart
        fields=['id','created_at']
        read_only_fields = ['id', 'created_at']

class CartItemSerializer(serializers.ModelSerializer):
    cart=CartSerializer(read_only=True)
    cart_id=serializers.PrimaryKeyRelatedField(queryset=Cart.objects.all(),write_only=True)
    product_variant=ProductVariantSerializer(read_only=True)
    product_variant_id=serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(),write_only=True)
    class Meta:
        model=CartItem
        fields=['id','cart','cart_id','product_variant','product_variant_id','quantity']
        read_only_fields = ['id']