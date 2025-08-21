from .models import Order,OrderItem,ShippingAddress
from rest_framework import serializers
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant
from promoter.serializers import PromoterSerializer
from rest_framework.validators import UniqueTogetherValidator
from promoter.models import Promoter
from .utils import get_pincode_details

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'user', 'full_name', 'phone_number',
            'address', 'locality', 'city', 'district', 'state',
            'region', 'postal_code', 'country'
        ]
        read_only_fields = ['user']
        validators = [
            UniqueTogetherValidator(
                queryset=ShippingAddress.objects.all(),
                fields=[
                     'full_name', 'phone_number',
                    'address', 'locality', 'city', 'postal_code', 'country'
                ],
                message="This address already exists for the user."
            )
        ]


    
    
class OrderSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(required=False)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingAddress.objects.all(),
        write_only=True, required=False, allow_null=True
    )
    cancelable = serializers.SerializerMethodField()
    promoter = PromoterSerializer(read_only=True)
    promoter_id = serializers.PrimaryKeyRelatedField(
        queryset=Promoter.objects.all(), write_only=True, required=False, allow_null=True
    )
    cancelled_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'shipping_address_id',
            'status', 'total', 'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'promoter_id',
            'cancel_reason', 'cancelled_at', 'cancelled_by', 'cancelled_by_role',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at', 'refund_reason',
            'is_restocked', 'cancelable'
        ]
        read_only_fields = [
            'status', 'is_paid', 'is_refunded', 'tracking_number', 'shipped_at',
            'delivered_at', 'paid_at', 'created_at', 'updated_at',
            'cancelled_by', 'cancelled_by_role', 'is_restocked'
        ]

    def get_cancelable(self, obj):
        return obj.status in ['pending', 'processing'] and obj.status != 'cancelled'

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
    locality = serializers.ChoiceField(choices=[], required=True)
    city = serializers.CharField(max_length=50)
    district = serializers.CharField(max_length=50, required=False, allow_blank=True)
    state = serializers.CharField(max_length=50)
    region = serializers.CharField(max_length=50, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=50)

    
    def validate(self, data):
        pincode = data.get('postal_code')
        if pincode:
            details = get_pincode_details(pincode)

            # Enrich data with autofill values
            if details.get('state'):
                data['state'] = details['state']
            if details.get('district'):
                data['district'] = details['district']

        return data

class ShippingAddressSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            "full_name", "phone_number", "address",
            "locality", "city", "district", "state",
            "postal_code", "country",'created_at'
        ]

class CartCheckoutInputSerializer(serializers.Serializer):
    shipping_address_id = serializers.IntegerField(required=False)
    shipping_address = ShippingAddressInputSerializer(required=False)
    payment_method = serializers.ChoiceField(choices=['Cash on Delivery', 'Razorpay'])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shipping_data = self.initial_data.get('shipping_address') if hasattr(self, 'initial_data') else None
        if shipping_data:
            pincode = shipping_data.get('postal_code')
            if pincode:
                try:
                    details = get_pincode_details(pincode)
                    self.fields['shipping_address'].fields['locality'].choices = details.get('localities', [])
                except Exception:
                    self.fields['shipping_address'].fields['locality'].choices = []

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
    
class OrderItemSimpleSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant', 'quantity', 'price', 'status']

class OrderDetailSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    promoter = PromoterSerializer(read_only=True)
    items = OrderItemSimpleSerializer(source='orderitem_set', many=True, read_only=True)
    cancelable = serializers.SerializerMethodField()
    cancelled_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'status', 'total', 'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'items',
            'cancel_reason', 'cancelled_at', 'cancelled_by',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at', 'refund_reason',
            'cancelable'
        ]

    def get_cancelable(self, obj):
        return obj.status in ['pending', 'processing'] and obj.status != 'cancelled'

class OrderSummarySerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSummarySerializer(read_only=True)
    first_item = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "shipping_address", "status", "total", "payment_method", "is_paid", "is_refunded",
            "tracking_number", "created_at", "updated_at", "first_item",
            "refund_status", "refunded_at", "refund_reason"
        ]

    def get_first_item(self, obj):
        item = obj.orderitem_set.first()
        if item and item.product_variant:
            return {
                "product_name": item.product_variant.product_name,
                "variant_name": item.product_variant.variant_name,
                "image": item.product_variant.images[0].image if item.product_variant.images.exists() else None
            }
        return None

class CustomerOrderListSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    items = OrderItemSimpleSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'status', 'total', 'payment_method',
            'is_paid', 'is_refunded', 'tracking_number',
            'created_at', 'updated_at', 'items'
        ]

