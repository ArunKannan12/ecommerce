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
    product_variant=ProductVariantSerializer(read_only=True)
    product_variant_id=serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(),write_only=True)
    class Meta:
        model=CartItem
        fields=['id','product_variant','product_variant_id','quantity','added_at']
        read_only_fields = ['id','added_at']
        
    def create(self, validated_data):
        # Convert product_variant_id into product_variant
        validated_data['product_variant'] = validated_data.pop('product_variant_id')
        return super().create(validated_data)