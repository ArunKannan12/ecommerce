from rest_framework import serializers
from .models import Promoter, PromoterCommission, WithdrawalRequest
from products.serializers import ProductVariantSerializer
from products.models import ProductVariant
from orders.models import Order
from promoter.models import Promoter  # safe because it's the same module

class PromoterSerializer(serializers.ModelSerializer):
    referral_link = serializers.SerializerMethodField()
    class Meta:
        model = Promoter
        fields = '__all__'
        read_only_fields = [
            'total_sales_count',
            'total_commission_earned',
            'wallet_balance',
            'is_eligible_for_withdrawal',
            'user',
            'referral_code'
        ]


class PromoterCommissionSerializer(serializers.ModelSerializer):
    promoter = PromoterSerializer(read_only=True)
    promoter_id = serializers.PrimaryKeyRelatedField(queryset=Promoter.objects.all(), write_only=True)

    order = serializers.SerializerMethodField()
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)

    product = ProductVariantSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), write_only=True)

    class Meta:
        model = PromoterCommission
        fields = ['id', 'promoter', 'promoter_id', 'order', 'order_id', 'product', 'product_id', 'amount']

    def get_order(self, obj):
        # ✅ Lazy import to avoid circular import
        from orders.serializers import OrderSerializer
        return OrderSerializer(obj.order).data


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    promoter = PromoterSerializer(read_only=True)
    promoter_id = serializers.PrimaryKeyRelatedField(queryset=Promoter.objects.all(), write_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'promoter', 'promoter_id',
            'amount', 'status', 'request_at',
            'reviewwd_at', 'admin_note'
        ]

        read_only_fields = ['status', 'requested_at', 'reviewed_at', 'admin_note']
