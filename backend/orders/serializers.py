from .models import Order, OrderItem, ShippingAddress,ReturnRequest,ReplacementRequest
from rest_framework import serializers
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant
from promoter.serializers import PromoterSerializer
from rest_framework.validators import UniqueTogetherValidator
from promoter.models import Promoter
from django.utils import timezone
from datetime import timedelta

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

class OrderItemSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number',read_only=True)
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order_number', 'product_variant', 'product_variant_id',
            'quantity', 'price', 'status', 'packed_at', 'shipped_at','delivered_at'
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
    items = OrderItemSerializer(many=True,source='orderitem_set',read_only=True)
    order_number=serializers.CharField(read_only=True)
    class Meta:
        model = Order
        fields = [
             'id','order_number','shipping_address', 'shipping_address_id',
            'status', 'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'promoter_id',
            'cancel_reason', 'cancelled_at', 'cancelled_by', 'cancelled_by_role',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at',
            'is_restocked', 'cancelable','items'
        ]
        read_only_fields = [
            'status', 'subtotal', 'delivery_charge', 'total',
            'is_paid', 'is_refunded', 'tracking_number',
            'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at',
            'cancelled_by', 'cancelled_by_role', 'is_restocked'
        ]

    def get_cancelable(self, obj):
        return obj.status in ['pending', 'processing'] and obj.status != 'cancelled'
    def get_items(self,obj):
        return 



class ShippingAddressInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    locality = serializers.CharField(max_length=100)  # frontend provides locality options
    city = serializers.CharField(max_length=50)
    district = serializers.CharField(max_length=50, required=False, allow_blank=True)
    state = serializers.CharField(max_length=50)
    region = serializers.CharField(max_length=50, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=50)


class ShippingAddressSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            "full_name", "phone_number", "address",
            "locality", "city", "district", "state",
            "postal_code", "country", 'created_at'
        ]


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
    order_number = serializers.CharField(required=True)
    payment_method = serializers.ChoiceField(choices=['Cash on Delivery', 'razorpay'])
    razorpay_order_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_signature = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        order_number = attrs.get('order_number')
        payment_method = attrs.get('payment_method')

        try:
            order = Order.objects.get(order_number=order_number, user=self.context['request'].user)
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
        fields = ['id', 'product_variant', 'quantity', 'price', 
                  'status','packed_at','shipped_at','failed_at',
                  'out_for_delivery_at','delivered_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    promoter = PromoterSerializer(read_only=True)
    items = serializers.SerializerMethodField()
    cancelable = serializers.SerializerMethodField()
    cancelled_by = serializers.StringRelatedField(read_only=True)
    refund_info = serializers.SerializerMethodField()
    delivered_by = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'shipping_address', 'status',
            'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded', 'is_restocked',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'items',
            'cancel_reason', 'cancelled_at', 'cancelled_by',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at', 'refund_finalized',
            'cancelable', 'refund_info', 'delivered_by'
        ]

    def get_cancelable(self, obj):
        return obj.status in ['pending', 'processing'] and obj.status != 'cancelled'

    def get_refund_info(self, obj):
        if not obj.refund_id:
            return None

        if obj.refund_status in ["processed", "refunded"]:
            message = "Refund Processed – may take 5–7 days to reflect in your account."
        elif obj.refund_status == "failed":
            message = "Refund failed. Please contact support."
        else:
            message = "Refund is in progress. Please check back later."

        return {
            "refund_id": obj.refund_id,
            "status": obj.refund_status,
            "finalized": obj.refund_finalized,
            "refunded_at": obj.refunded_at,
            "message": message,
        }

    def get_delivered_by(self, obj):
        if not obj.delivered_by:
            return None
        dm = obj.delivered_by
        return {
            "id": dm.id,
            "name": str(dm.user),
            "phone": dm.phone,
            "vehicle_number": dm.vehicle_number,
            "last_active": dm.last_active,
            "joined_at": dm.joined_at,
            "total_delivery": dm.total_deliveries,
            "earnings": dm.earnings
        }

    def get_items(self, obj):
        result = []
        delivered_at = obj.delivered_at

        # prefetch requests
        return_requests = {rr.order_item_id: rr for rr in obj.return_requests.all()}
        replacement_requests = {rr.order_item_id: rr for rr in obj.replacement_requests.all()}

        for item in obj.orderitem_set.all():
            variant = item.product_variant
            return_remaining_days = None
            replacement_remaining_days = None

            if delivered_at:
                if variant.allow_return and variant.return_days:
                    delta = (delivered_at + timedelta(days=variant.return_days)) - timezone.now()
                    return_remaining_days = max(delta.days, 0)
                if variant.allow_replacement and variant.replacement_days:
                    delta = (delivered_at + timedelta(days=variant.replacement_days)) - timezone.now()
                    replacement_remaining_days = max(delta.days, 0)

            # attach return/replacement request if exists
            return_request = None
            replacement_request = None
            if item.id in return_requests:
                rr = return_requests[item.id]
                return_request = {
                    "id": rr.id,
                    "status": rr.status,
                    "reason": rr.reason,
                    "pickup_status": rr.pickup_status,
                    "admin_decision": rr.admin_decision,
                    "warehouse_decision": rr.warehouse_decision,
                    "refund_amount": rr.refund_amount,
                    "refund_method": rr.refund_method,
                }
            if item.id in replacement_requests:
                rr = replacement_requests[item.id]
                replacement_request = {
                    "id": rr.id,
                    "status": rr.status,
                    "reason": rr.reason,
                    "pickup_status": rr.pickup_status,
                    "admin_decision": rr.admin_decision,
                    "warehouse_decision": rr.warehouse_decision,
                    "shipped_at": rr.shipped_at,
                    "delivered_at": rr.delivered_at,
                }

            result.append({
                **OrderItemSimpleSerializer(item).data,
                "return_remaining_days": return_remaining_days,
                "replacement_remaining_days": replacement_remaining_days,
                "return_request": return_request,
                "replacement_request": replacement_request,
            })
        return result

    
class OrderSummarySerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSummarySerializer(read_only=True)
    first_item = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "order_number", "shipping_address", "status",
            "subtotal", "delivery_charge", "total",
            "payment_method", "is_paid", "is_refunded",
            "tracking_number", "created_at", "updated_at", "first_item",
            "refund_status", "refunded_at", 
        ]

    def get_first_item(self, obj):
        item = obj.orderitem_set.first()
        if item and item.product_variant:
            return {
                "product_name": item.product_variant.product_name,
                "variant_name": item.product_variant.variant_name,
                "image": (
                    item.product_variant.images.first().image
                    if item.product_variant.images.exists() else None
                )
            }
        return None


class CustomerOrderListSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    items = OrderItemSimpleSerializer(source='orderitem_set', many=True, read_only=True)
    refund_info=serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'order_number', 'shipping_address', 'status',
            'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'created_at', 'updated_at', 'items','refund_info'
        ]

    def get_refund_info(self, obj):
        if not obj.refund_id:
            return None
        
        message = (
            "Refund Processed – may take 5–7 days to reflect in your account."
            if obj.refund_status == "processed"
            else "Refund is in progress. Please check back later."
        )

        return {
            "refund_id": obj.refund_id,
            "status": obj.refund_status,
            "finalized": obj.refund_finalized,
            "refunded_at": obj.refunded_at,
            "message": message,
        }

class OrderPreviewInputSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
        ),
        allow_empty=False,
        help_text="List of items with product_variant_id and quantity"
    )
    postal_code = serializers.CharField(max_length=20, required=False)
    def validate_items(self, value):
        for item in value:
            if "product_variant_id" not in item or "quantity" not in item:
                raise serializers.ValidationError(
                    "Each item must include 'product_variant_id' and 'quantity'."
                )
            if item["quantity"] <= 0:
                raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class OrderPreviewOutputSerializer(serializers.Serializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)

class OrderLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_number','status','total','payment_method','created_at','is_paid','paid_at']

class OrderitemLightSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = [
            'id', 'quantity', 'price', 'status',
            'product_variant'
        ]

class WarehouseOrderItemSerializer(serializers.ModelSerializer):
    order_number = serializers.SerializerMethodField()
    product_name=serializers.SerializerMethodField()
    variant_name=serializers.SerializerMethodField()

    class Meta:
        model=OrderItem
        fields=[
            'id','order_number','product_name','variant_name',
            'quantity','price','status','packed_at','shipped_at',
            'failed_at','out_for_delivery_at'
        ]

    def get_order_number(self, obj):
        return obj.order.order_number if obj.order else None

    def get_product_name(self, obj):
        return obj.product_variant.product.name if obj.product_variant and hasattr(obj.product_variant, 'product') else None

    def get_variant_name(self, obj):
        return obj.product_variant.variant_name if obj.product_variant else None