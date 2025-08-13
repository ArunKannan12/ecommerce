from .models import Order,OrderItem,ShippingAddress
from rest_framework import serializers
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant
from promoter.serializers import PromoterSerializer
from promoter.models import Promoter

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model=ShippingAddress
        fields=['id','user','full_name','phone_number','address','city','postal_code','country']   
        read_only_fields=['user']

class OrderSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all(),
        write_only=True,required=False,allow_null=True
    )
    promoter=PromoterSerializer(read_only=True)
    promoter_id=serializers.PrimaryKeyRelatedField(queryset=Promoter.objects.all(),
                                                   write_only=True,required=False,allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id','shipping_address','shipping_address_id',
            'status','total','payment_method','is_paid',
            'tracking_number','shipped_at','delivered_at','paid_at',
            'created_at','updated_at','promoter','promoter_id'
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
        fields = [
            'id', 'order', 'order_id', 'product_variant', 'product_variant_id',
            'quantity', 'price', 'status', 'packed_at', 'shipped_at'
        ]
        
class ShippingAddressInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    city = serializers.CharField(max_length=50)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=50)

class CartCheckoutInputSerializer(serializers.Serializer):
    shipping_address_id = serializers.IntegerField(required=False)
    shipping_address = ShippingAddressInputSerializer(required=False)
    payment_method = serializers.ChoiceField(choices=['Cash on Delivery', 'Razorpay'])
    
    
    def validate(self, data):
        has_id = data.get('shipping_address_id')
        shipping_data = data.get('shipping_address')

        if not has_id and not shipping_data:
            raise serializers.ValidationError({
                "shipping_address": {
                    "full_name": ["This field is required."],
                    "phone_number": ["This field is required."],
                    "address": ["This field is required."],
                    "city": ["This field is required."],
                    "postal_code": ["This field is required."],
                    "country": ["This field is required."]
                }
            })

        if has_id and shipping_data:
            raise serializers.ValidationError({
                "non_field_errors": [
                    "Provide either 'shipping_address_id' or 'shipping_address', not both."
                ]
            })

        # ✅ Validate nested shipping_address fields manually if provided
        if shipping_data:
            nested_serializer = ShippingAddressInputSerializer(data=shipping_data)
            if not nested_serializer.is_valid():
                raise serializers.ValidationError({"shipping_address": nested_serializer.errors})

        return data
    
class CheckoutItemInputSerializer(serializers.Serializer):
    product_variant_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

class ReferralCheckoutInputSerializer(CartCheckoutInputSerializer):
    items = CheckoutItemInputSerializer(many=True, required=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("This field cannot be empty.")
        return value
    
    
class OrderItemStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['picked', 'packed', 'shipped'])

    def validate_status(self, value):
        if value not in ['picked', 'packed', 'shipped']:
            raise serializers.ValidationError("Invalid status update.")
        return value



class OrderPaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(choices=['Cash on Delivery', 'razorpay'])
    razorpay_order_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_signature = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        order_id = attrs.get('order_id')
        payment_method = attrs.get('payment_method')

        try:
            order = Order.objects.get(id=order_id, user=self.context['request'].user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")

        if order.is_paid:
            raise serializers.ValidationError("Order is already paid.")

        if payment_method == 'razorpay':
            if not (attrs.get('razorpay_order_id') and attrs.get('razorpay_payment_id') and attrs.get('razorpay_signature')):
                raise serializers.ValidationError("Razorpay payment details are required.")

        attrs['order'] = order
        return attrs 