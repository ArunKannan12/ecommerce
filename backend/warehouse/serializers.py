from rest_framework import serializers
from orders.models import Order, OrderItem
from django.utils.timesince import timesince


class WarehouseOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    order_number=serializers.CharField(source='order.order_number',read_only=True)
    customer=serializers.CharField(source='order.user.email',read_only=True)
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price",
            "status",
            "packed_at",
            'order_number',
            'customer',
            "shipped_at",
            "failed_at",
            "out_for_delivery_at",
        ]

    def get_product(self, obj):
        # Return product name + variant (e.g., "Samsung - 236L Fridge")
        return str(obj.product_variant)


class WarehouseOrderSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    deliveryman = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()
    items = WarehouseOrderItemSerializer(source="orderitem_set", many=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_items = serializers.SerializerMethodField()
    created_at_human = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "order_number",
            "status",
            "status_display",
            "assigned_at",
            "deliveryman",
            "shipping_address",
            "subtotal",
            "delivery_charge",
            "total",
            "payment_method",
            "is_paid",
            "created_at",
            "created_at_human",
            "total_items",
            "items",
        ]

    def get_customer(self, obj):
        return obj.user.email if obj.user else None

    def get_deliveryman(self, obj):
        return obj.delivered_by.user.email if obj.delivered_by else None

    def get_shipping_address(self, obj):
        addr = obj.shipping_address
        if not addr:
            return None
        return {
            "full_name": addr.full_name,
            "phone_number": addr.phone_number,
            "address": addr.address,
            "locality": addr.locality,
            "city": addr.city,
            "district": addr.district,
            "state": addr.state,
            "postal_code": addr.postal_code,
            "country": addr.country,
        }

    def get_total_items(self, obj):
        return obj.orderitem_set.count()

    def get_created_at_human(self, obj):
        return f"{timesince(obj.created_at)} ago"
