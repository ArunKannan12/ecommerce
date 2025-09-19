from rest_framework import serializers
from orders.models import Order,OrderItem

class WarehouseOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price",
            "status",
            "packed_at",
            "shipped_at",
            "failed_at",
            "out_for_delivery_at",
        ]

    def get_product(self, obj):
        # Return product name + variant (example: "Nike Shoes - Size 9")
        return str(obj.product_variant)


class WarehouseOrderSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    deliveryman = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()
    items = WarehouseOrderItemSerializer(source="orderitem_set", many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "assigned_at",
            "deliveryman",
            "shipping_address",
            "subtotal",
            "delivery_charge",
            "total",
            "payment_method",
            "is_paid",
            "created_at",
            "items",
        ]

    def get_customer(self, obj):
        return obj.user.email if obj.user else None

    def get_deliveryman(self, obj):
        return obj.delivered_by.user.email if obj.delivered_by else None

    def get_shipping_address(self, obj):
        if obj.shipping_address:
            return {
                "full_name": obj.shipping_address.full_name,
                "phone_number": obj.shipping_address.phone_number,
                "address": obj.shipping_address.address,
                "locality": obj.shipping_address.locality,
                "city": obj.shipping_address.city,
                "district": obj.shipping_address.district,
                "state": obj.shipping_address.state,
                "postal_code": obj.shipping_address.postal_code,
                "country": obj.shipping_address.country,
            }
        return None
