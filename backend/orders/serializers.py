from .models import Order, OrderItem, ShippingAddress,ReturnRequest
from rest_framework import serializers
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant
from promoter.serializers import PromoterSerializer
from rest_framework.validators import UniqueTogetherValidator
from promoter.models import Promoter
from django.utils.timesince import timesince
from django.utils import timezone

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
            'status', 'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'promoter_id',
            'cancel_reason', 'cancelled_at', 'cancelled_by', 'cancelled_by_role',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at',
            'is_restocked', 'cancelable'
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


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'order_id', 'product_variant', 'product_variant_id',
            'quantity', 'price', 'status', 'packed_at', 'shipped_at'
        ]


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
    refund_info=serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'status',
            'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded',
            'tracking_number', 'shipped_at', 'delivered_at', 'paid_at',
            'created_at', 'updated_at', 'promoter', 'items',
            'cancel_reason', 'cancelled_at', 'cancelled_by',
            'razorpay_order_id', 'razorpay_payment_id',
            'refund_id', 'refund_status', 'refunded_at', 
            'cancelable','refund_info'
        ]

    def get_cancelable(self, obj):
        return obj.status in ['pending', 'processing'] and obj.status != 'cancelled'

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

class OrderSummarySerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSummarySerializer(read_only=True)
    first_item = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "shipping_address", "status",
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
            'id', 'shipping_address', 'status',
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
        model=Order
        fields=['id','status','total','payment_method','created_at']

class OrderitemLightSerializer(serializers.ModelSerializer):
    product_variant=ProductVariantSerializer(read_only=True)

    class Meta:
        model=OrderItem
        fields=['id','quantity','price','status','product_variant']

class ReturnRequestSerializer(serializers.ModelSerializer):
    # --- Read-only representation fields ---
    order = OrderLightSerializer(read_only=True)
    order_item = OrderitemLightSerializer(read_only=True)
    shipping_address=serializers.SerializerMethodField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)
    variant = serializers.SerializerMethodField(read_only=True)
    variant_images = serializers.SerializerMethodField(read_only=True)
    is_refunded = serializers.SerializerMethodField(read_only=True)
    refunded_at_human = serializers.SerializerMethodField(read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)
    refund_method_display = serializers.SerializerMethodField(read_only=True)
    delivery_charge=serializers.SerializerMethodField(read_only=True)
    user_upi = serializers.CharField(required=False, allow_blank=True)
    return_days_remaining = serializers.SerializerMethodField()
    replacement_days_remaining = serializers.SerializerMethodField()
    pickup_verified_by_name = serializers.SerializerMethodField(read_only=True)
    pickup_status_display = serializers.SerializerMethodField(read_only=True)
    warehouse_status_display = serializers.SerializerMethodField(read_only=True)
    admin_status_display = serializers.SerializerMethodField(read_only=True)

    # --- Accept these for creation ---
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), write_only=True
    )
    order_item_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(), write_only=True
    )

    class Meta:
        model = ReturnRequest
        fields = [
            "id",
            "order", "order_item",
            "order_id", "order_item_id",
            "product", "variant", "variant_images",
            "reason", "status", "refund_amount", "user_upi",
            "pickup_verified_by_name", "pickup_comment", "pickup_status_display",
            "warehouse_comment", "warehouse_status_display",
            "admin_comment", "admin_status_display",
            "created_at", "updated_at", "refunded_at",
            "refund_method", "refund_method_display",
            'return_days_remaining','replacement_days_remaining',
            "is_refunded", "refunded_at_human", "product_image","shipping_address",'delivery_charge'
        ]

    def validate(self, attrs):
        order_item = attrs.get('order_item_id')
        if ReturnRequest.objects.filter(order_item=order_item).exclude(status='refunded').exists():
            raise serializers.ValidationError("A return request is already in progress for this item.")

        user = self.context['request'].user
        if attrs['order_id'].user != user:
            raise serializers.ValidationError("You can only request a return for your own orders.")

        variant = order_item.product_variant
        if not variant.is_returnable and not variant.is_replacement_only:
            raise serializers.ValidationError('This product cannot be returned or replaced')
        if variant.is_returnable and variant.is_replacement_only:
            raise serializers.ValidationError("A product cannot be both returnable and replacement-only at the same time")

        return attrs
    
    def get_return_days_remaining(self, obj):
        variant = obj.order_item.product_variant
        if not variant.is_returnable:
            return 0
        delta = (timezone.now().date() - obj.order.created_at.date()).days
        remaining = variant.return_days - delta
        return max(remaining, 0)

    def get_replacement_days_remaining(self, obj):
        variant = obj.order_item.product_variant
        if not variant.is_replacement_only:
            return 0
        delta = (timezone.now().date() - obj.order.created_at.date()).days
        remaining = variant.replacement_days - delta
        return max(remaining, 0)

    def create(self, validated_data):
        order = validated_data.pop("order_id")
        order_item = validated_data.pop("order_item_id")
        validated_data.pop("refund_amount", None)

        total_items_price = sum(item.price * item.quantity for item in order.orderitem_set.all())
        item_share_of_delivery = 0
        if hasattr(order, "delivery_charge") and order.delivery_charge:
            item_share_of_delivery = (order_item.price * order_item.quantity / total_items_price) * order.delivery_charge

        refund_amount = (order_item.price * order_item.quantity) + item_share_of_delivery

        # Create instance but don't save yet
        instance = ReturnRequest(
            order=order,
            order_item=order_item,
            refund_amount=refund_amount,
            **validated_data
        )
        # Validate the model
        instance.full_clean()
        # Save after validation
        instance.save()
        return instance

    

    def get_delivery_charge(self, obj):
       
        order = obj.order
        order_item = obj.order_item

        if not order or not order_item:
            return 0

        total_items_price = sum(item.price * item.quantity for item in order.orderitem_set.all())
        if total_items_price == 0:
            return 0

        proportional_delivery = 0
        if hasattr(order, "delivery_charge") and order.delivery_charge:
            proportional_delivery = (order_item.price * order_item.quantity / total_items_price) * order.delivery_charge

        return round(proportional_delivery, 2)


    def get_shipping_address(self,obj):
        if obj.order and hasattr(obj.order,"shipping_address") and obj.order.shipping_address:
            return ShippingAddressSerializer(obj.order.shipping_address).data
        return None
    # ---- Custom Getters ----
    def get_product(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            return obj.order_item.product_variant.product.name
        return None

    def get_variant(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            return obj.order_item.product_variant.variant_name
        return None

    def get_variant_images(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            images = obj.order_item.product_variant.images.all()
            return [img.url for img in images if img.url]
        return []

    def get_is_refunded(self, obj):
        return obj.status == "refunded"

    def get_refunded_at_human(self, obj):
        if obj.refunded_at:
            return timesince(obj.refunded_at) + " ago"
        return None

    def get_product_image(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            product = obj.order_item.product_variant.product
            if product.image_url:
                return product.image_url
            elif product.image:
                return product.image.url
        return None

    def get_refund_method_display(self, obj):
        return obj.get_refund_method_display() if obj.refund_method else None

    def get_pickup_verified_by_name(self, obj):
        if obj.pickup_verified_by and obj.pickup_verified_by.user:
            return obj.pickup_verified_by.user.get_full_name() or obj.pickup_verified_by.user.email
        return None

    def get_pickup_status_display(self, obj):
        return obj.get_pickup_status_display()

    def get_warehouse_status_display(self, obj):
        return obj.get_warehouse_decision_display()

    def get_admin_status_display(self, obj):
        return obj.get_admin_decision_display()
