from .models import Investment, Investor, InvestorWallet, Payout, ProductSaleShare
from rest_framework import serializers


class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            'id', 'phone', 'net_worth', 'profile_image', 'address',
            'verification_status', 'joined_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at', 'verification_status']



class InvestmentSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(), write_only=True)

    class Meta:
        model = Investment
        fields = ['id', 'investor', 'investor_id', 'amount',
                  'transaction_id', 'invested_at', 'confirmed', 'note']


class ProductSaleShareSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(), write_only=True)

    class Meta:
        model = ProductSaleShare
        fields = ['id', 'investor', 'investor_id', 'total_sales_volume',
                  'profit_generated', 'investor_share',
                  'period_start', 'period_end', 'created_at']
        read_only_fields = ['created_at']


class PayoutSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(), write_only=True)
    sale_share = ProductSaleShareSerializer(read_only=True)
    sale_share_id = serializers.PrimaryKeyRelatedField(queryset=ProductSaleShare.objects.all(), write_only=True)

    class Meta:
        model = Payout
        fields = ['id', 'investor', 'investor_id', 'amount', 'status',
                  'payout_date', 'sale_share', 'sale_share_id']
        read_only_fields = ['payout_date']

class InvestorWalletSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(), write_only=True)

    class Meta:
        model = InvestorWallet
        fields = ['id', 'investor', 'investor_id', 'balance', 'last_updated']
        read_only_fields = ['balance', 'last_updated']
