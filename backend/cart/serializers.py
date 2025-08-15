from django.contrib.auth import get_user_model
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer
from rest_framework import serializers
from .models import Cart,CartItem

User=get_user_model()
# Create your models here.


class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model=Cart
        fields=['id','created_at']
        read_only_fields = ['id', 'created_at']

class CartItemSerializer(serializers.ModelSerializer):
    product_variant_detail = ProductVariantSerializer(source='product_variant', read_only=True)
    product_variant=serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(),write_only=True)
    price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    class Meta:
        model=CartItem
        fields = [
            'id',
            'product_variant',
            'product_variant_detail',
            'quantity',
            'price',
            'subtotal',
            'added_at'
        ]
        read_only_fields = ['id', 'added_at', 'price', 'subtotal']
        
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    def get_price(self, obj):
        variant = getattr(obj, 'product_variant', None)
        return variant.final_price if variant else 0

    def get_subtotal(self, obj):
        variant = getattr(obj, 'product_variant', None)
        return obj.quantity * variant.final_price if variant else 0
    
class CartSummarySerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'items', 'total_quantity', 'total_price']

class CartItemInputSerializer(serializers.Serializer):
    product_variant_id = serializers.IntegerField()
    quantity=serializers.IntegerField(min_value=1)