
from rest_framework import serializers
from .serializers import OrderitemLightSerializer,OrderLightSerializer,ShippingAddressSerializer
from .models import ReturnRequest,ReplacementRequest,Order,OrderItem,OrderStatus
from django.utils import timezone,timesince
from products.models import ProductVariant
from decimal import Decimal

class ReturnRequestSerializer(serializers.ModelSerializer):
    # --- Read-only relations ---
    order = OrderLightSerializer(read_only=True)
    order_item = OrderitemLightSerializer(read_only=True)
    shipping_address = serializers.SerializerMethodField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)
    variant = serializers.SerializerMethodField(read_only=True)
    variant_images = serializers.SerializerMethodField(read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)
    
    # --- Status / Refund info ---
    is_refunded = serializers.SerializerMethodField(read_only=True)
    refunded_at_human = serializers.SerializerMethodField(read_only=True)
    refund_method_display = serializers.SerializerMethodField(read_only=True)
    refund_id = serializers.SerializerMethodField(read_only=True)
    refund_status = serializers.SerializerMethodField(read_only=True)
    delivery_charge = serializers.SerializerMethodField(read_only=True)
    return_days_remaining = serializers.SerializerMethodField(read_only=True)

    # --- Pickup / warehouse / admin ---
    pickup_verified_by_name = serializers.SerializerMethodField(read_only=True)
    pickup_status_display = serializers.SerializerMethodField(read_only=True)
    warehouse_status_display = serializers.SerializerMethodField(read_only=True)
    admin_status_display = serializers.SerializerMethodField(read_only=True)
    
    # --- Payment info ---
    payment_id = serializers.SerializerMethodField(read_only=True)
    currency = serializers.SerializerMethodField(read_only=True)

    # --- Input fields ---
    user_upi = serializers.CharField(required=False, allow_blank=True)
    refund_method = serializers.ChoiceField(
        choices=ReturnRequest.REFUND_METHOD_CHOICES,
        required=False
    )
    order_number = serializers.CharField( write_only=True)
    
    order_item_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(), write_only=True
    )
    order_number_display = serializers.CharField(source='order.order_number', read_only=True)
    class Meta:
        model = ReturnRequest
        fields = [
            "id",
            # relations
            "order", "order_item",
            "order_number", "order_item_id",
            # request info
            "reason", "status",
            'order_number_display',
            # refund info
            "refund_amount", "user_upi", "refund_method", "refund_method_display",
            # pickup / warehouse / admin
            "pickup_verified_by_name", "pickup_comment", "pickup_status_display",
            "warehouse_decision", "warehouse_comment", "warehouse_status_display",
            "admin_comment", "admin_status_display",
            # timestamps
            "created_at", "updated_at", "refunded_at",
            # refund tracking
            "refund_id", "refund_status",
            # display only
            "product", "variant", "variant_images", "product_image",
            "shipping_address", "delivery_charge",
            "return_days_remaining",
            "is_refunded", "refunded_at_human",
            # new fields
            'payment_id', 'currency', 'pickup_collected_at',
            'warehouse_processed_at', 'admin_processed_at'
        ]
        read_only_fields = [
            "order", "order_item",
            "refund_amount", "is_refunded", "refunded_at_human",
            "product", "variant", "variant_images", "product_image",
            "shipping_address", "delivery_charge",
            "pickup_verified_by", "pickup_verified_by_name",
        ]

    # --- Validation ---
    def validate(self, attrs):
        user = self.context["request"].user

        if self.instance is None:  # Only on create
            order_number = attrs.get("order_number")
            order_item = attrs.get("order_item_id")
            
            if not order_number or not order_item:
                raise serializers.ValidationError("Both 'order_number' and 'order_item_id' are required.")

            # Fetch the actual Order instance
            try:
                order = Order.objects.get(order_number=order_number)
            except Order.DoesNotExist:
                raise serializers.ValidationError({"order_number": "Order not found."})

            # Validate that the order_item belongs to the order
            if order_item.order != order:
                raise serializers.ValidationError({"order_item_id": "Order item not found for this order."})

            # Now it's safe to check
            if order.user != user:
                raise serializers.ValidationError("You can only request a return for your own orders.")

            if order.status.lower() != "delivered":
                raise serializers.ValidationError("Return requests can only be created for delivered orders.")

            variant = order_item.product_variant
            if not variant.allow_return:
                raise serializers.ValidationError("This product is not eligible for return.")

            # COD UPI check
            if order.payment_method.lower() in ["cod", "cash on delivery"]:
                user_upi = attrs.get("user_upi", "").strip()
                if not user_upi:
                    raise serializers.ValidationError("For COD return requests, UPI address is required for refund.")

            # Replace string/ids with actual objects for use in create()
            attrs["order"] = order
            attrs["order_item"] = order_item

        return attrs

    # --- Creation ---
    def create(self, validated_data):
        order = validated_data.pop("order")       # <-- already an Order instance
        order_item = validated_data.pop("order_item")  # <-- already an OrderItem instance
        validated_data.pop('order_number',None)
        validated_data.pop('order_item_id',None)

        user_upi = validated_data.pop("user_upi", "").strip()
        refund_method = validated_data.pop("refund_method", None)

        # --- Set refund method ---
        if order.payment_method.lower() in ["cod", "cash on delivery"]:
            if not user_upi:
                raise serializers.ValidationError("For COD return requests, UPI address is required.")
            refund_method = "upi"  # enforce UPI for COD
        else:
            refund_method = refund_method or "razorpay"

        # --- Calculate proportional refund ---
        total_items_price = sum(item.price * item.quantity for item in order.orderitem_set.all())
        item_share_of_delivery = 0
        if hasattr(order, "delivery_charge") and order.delivery_charge:
            item_share_of_delivery = (
                (order_item.price * order_item.quantity / total_items_price) * order.delivery_charge
            )
        refund_amount = (order_item.price * order_item.quantity) + item_share_of_delivery
        instance = ReturnRequest.objects.create(
            order=order,
            order_item=order_item,
            user_upi=user_upi,
            refund_method=refund_method,
            refund_amount=refund_amount,
            **validated_data
        )
        return instance

    # --- Custom Getters for new fields ---
    def get_pickup_collected_at(self, obj):
        if obj.pickup_verified_by and hasattr(obj.pickup_verified_by, "collected_at"):
            return obj.pickup_verified_by.collected_at
        return None
    def get_payment_id(self, obj):
        return getattr(obj.order, "payment_id", None)
    def get_currency(self, obj):
        return getattr(obj.order, "currency", "INR") 
    # --- Custom Getters ---
    def get_refund_id(self, obj):
        return getattr(obj.order, "refund_id", None)

    def get_refund_status(self, obj):
        return getattr(obj.order, "refund_status", None)

    def get_return_days_remaining(self, obj):
        variant = obj.order_item.product_variant
        if not variant.allow_return:
            return 0
        delta = (timezone.now().date() - obj.order.created_at.date()).days
        return max(variant.return_days - delta, 0)

    def get_delivery_charge(self, obj):
        order, order_item = obj.order, obj.order_item
        if not order or not order_item:
            return 0
        total_items_price = sum(item.price * item.quantity for item in order.orderitem_set.all())
        if total_items_price == 0:
            return 0
        proportional_delivery = 0
        if hasattr(order, "delivery_charge") and order.delivery_charge:
            proportional_delivery = (order_item.price * order_item.quantity / total_items_price) * order.delivery_charge
        return round(proportional_delivery, 2)

    def get_shipping_address(self, obj):
        if obj.order and getattr(obj.order, "shipping_address", None):
            return ShippingAddressSerializer(obj.order.shipping_address).data
        return None

    def get_product(self, obj):
        return getattr(obj.order_item.product_variant.product, "name", None)

    def get_variant(self, obj):
        return getattr(obj.order_item.product_variant, "variant_name", None)

    def get_variant_images(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            return [img.url for img in obj.order_item.product_variant.images.all() if img.url]
        return []

    def get_is_refunded(self, obj):
        return obj.status == "refunded"

    def get_refunded_at_human(self, obj):
        return timesince(obj.refunded_at) + " ago" if obj.refunded_at else None

    def get_product_image(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            product = obj.order_item.product_variant.product
            if getattr(product, "image_url", None):
                return product.image_url
            elif getattr(product, "image", None):
                return product.image.url
        return None

    def get_refund_method_display(self, obj):
        return obj.get_refund_method_display() if obj.refund_method else None

        # --- Custom Getters ---
    def get_pickup_verified_by_name(self, obj):
        # Safely return the full name or email of the user who verified pickup
        if obj.pickup_verified_by and getattr(obj.pickup_verified_by, "user", None):
            user = obj.pickup_verified_by.user
            return user.get_full_name() or user.email
        return None

    def get_pickup_status_display(self, obj):
        return obj.get_pickup_status_display() if hasattr(obj, "get_pickup_status_display") else None

    def get_warehouse_status_display(self, obj):
        return obj.get_warehouse_decision_display() if hasattr(obj, "get_warehouse_decision_display") else None

    def get_admin_status_display(self, obj):
        return obj.get_admin_decision_display() if hasattr(obj, "get_admin_decision_display") else None


class ReplacementRequestSerializer(serializers.ModelSerializer):
    order = OrderLightSerializer(read_only=True)
    order_item = OrderitemLightSerializer(read_only=True)
    new_order = OrderLightSerializer(read_only=True)
    shipping_address = serializers.SerializerMethodField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)
    variant = serializers.SerializerMethodField(read_only=True)
    variant_images = serializers.SerializerMethodField(read_only=True)
    replacement_days_remaining = serializers.SerializerMethodField(read_only=True)
    pickup_verified_by_name = serializers.SerializerMethodField(read_only=True)
    pickup_status_display = serializers.SerializerMethodField(read_only=True)
    warehouse_status_display = serializers.SerializerMethodField(read_only=True)
    admin_status_display = serializers.SerializerMethodField(read_only=True)

    # --- Input fields ---
    order_number = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), write_only=True, required=False
    )
    order_item_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = ReplacementRequest
        fields = [
            "id",
            "order", "order_item", "new_order",
            "order_number", "order_item_id",
            "reason", "status","pickup_status",
            "pickup_verified_by_name", "pickup_comment", "pickup_status_display",
            "warehouse_decision", "warehouse_comment", "warehouse_status_display",
            "admin_decision","admin_comment", "admin_status_display",
            "created_at", "updated_at", "delivered_at",
            "product", "variant", "variant_images",
            "shipping_address", "replacement_days_remaining",
        ]
        read_only_fields = [
            "order", "order_item", "new_order",
            "product", "variant", "variant_images",
            "shipping_address",
            "pickup_verified_by", "pickup_verified_by_name",
        ]

    def validate(self, attrs):
        user =self.context["request"].user

        if self.instance:  # update
            order = self.instance.order
            order_item = self.instance.order_item
        else:  # create
            order = attrs.get("order_number")
            order_item = attrs.get("order_item_id")

            if not order or not order_item:
                raise serializers.ValidationError("Order and order item are required.")

            # Only the customer who placed the order can create a replacement request
            if order.user_id != user.id:
                raise serializers.ValidationError("You can only request a replacement for your own orders.")

            # Creation-only validations
            if order_item.order != order:
                raise serializers.ValidationError("Order item does not belong to this order.")
            if order.status.lower() != "delivered":
                raise serializers.ValidationError("Replacement requests can only be created for delivered orders.")
            if not order_item.product_variant.allow_replacement:
                raise serializers.ValidationError("This product is not eligible for replacement.")
            if ReturnRequest.objects.filter(order_item=order_item).exclude(
                status__in=["refunded", "rejected"]
            ).exists():
                raise serializers.ValidationError("A return request exists, cannot create replacement.")

            # Prevent duplicate active replacement requests
            existing_qs = ReplacementRequest.objects.filter(order_item=order_item).exclude(
                status__in=["delivered", "failed", "rejected"]
            )
            if existing_qs.exists():
                raise serializers.ValidationError("A replacement request already exists for this item.")

        # ✅ Common validations for both create and update
        if order_item.order.order_number != order.order_number:
            raise serializers.ValidationError("Order item does not belong to this order.")

        return attrs


    def create(self, validated_data):
        order = validated_data.pop("order_number")
        order_item = validated_data.pop("order_item_id")

        instance = ReplacementRequest.objects.create(
            order=order,
            order_item=order_item,
            **validated_data
        )

        # Automatically create the new replacement order
        new_order = Order.objects.create(
            user=order.user,
            shipping_address=order.shipping_address,
            subtotal=order_item.price,
            total=order_item.price + order.delivery_charge,
            payment_method=order.payment_method,
            status=OrderStatus.PENDING
        )
        OrderItem.objects.create(
            order=new_order,
            product_variant=order_item.product_variant,
            quantity=order_item.quantity,
            price=order_item.price
        )
        instance.new_order = new_order
        instance.save(update_fields=["new_order"])

        return instance

    # --- Custom Getters ---
    def get_replacement_days_remaining(self, obj):
        variant = obj.order_item.product_variant
        if not variant.allow_replacement:
            return 0
        delta = (timezone.now().date() - obj.order.created_at.date()).days
        return max(variant.replacement_days - delta, 0)

    def get_shipping_address(self, obj):
        if obj.order and getattr(obj.order, "shipping_address", None):
            return ShippingAddressSerializer(obj.order.shipping_address).data
        return None

    def get_product(self, obj):
        return getattr(obj.order_item.product_variant.product, "name", None)

    def get_variant(self, obj):
        return getattr(obj.order_item.product_variant, "variant_name", None)

    def get_variant_images(self, obj):
        if obj.order_item and obj.order_item.product_variant:
            return [img.url for img in obj.order_item.product_variant.images.all() if img.url]
        return []

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
