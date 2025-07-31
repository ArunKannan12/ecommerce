from .models import Order,OrderItem,ShippingAddress
from rest_framework import serializers
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model=ShippingAddress
        fields=['id','user','full_name','phone_number','address','city','postal_code','country']   
        read_only_fields=['user']

class OrderSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all(),
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id','shipping_address','shipping_address_id',
            'status','total','payment_method','is_paid',
            'tracking_number','shipped_at','delivered_at','paid_at',
            'created_at','updated_at',
        ]
        read_only_fields = [
            'status','is_paid','tracking_number','shipped_at',
            'delivered_at','paid_at','created_at','updated_at',
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    order=OrderSerializer(read_only=True)
    order_id=serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(),write_only=True)
    product_variant=ProductVariantSerializer(read_only=True)
    product_variant_id=serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(),write_only=True)

    class Meta:
        model=OrderItem
        fields=['id','order',
                'order_id','product_variant',
                'product_variant_id','quantity','price']