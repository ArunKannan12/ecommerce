from .models import Investment, Investor, InvestorWallet, Payout, ProductSaleShare,InvestmentPayment
from rest_framework import serializers
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer


class InvestorSerializer(serializers.ModelSerializer):
    total_confirmed_investments=serializers.DecimalField(max_digits=12,decimal_places=2,read_only=True)
    class Meta:
        model = Investor
        fields = [
            'id', 'phone', 'profile_image', 'address',
            'verification_status', 'joined_at', 'updated_at','total_confirmed_investments'
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at','total_confirmed_investments']



class InvestmentSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    product_variant=ProductVariantSerializer(read_only=True)
    product_variant_id=serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(),write_only=True,source='product_variant')
    class Meta:
        model = Investment
        fields = ['id', 'investor', 'amount','product_variant','product_variant_id',
                  'invested_at', 
                  'confirmed', 'note'
                  ]

        read_only_fields = ['investor', 'invested_at']

    

class InvestmentPaymentSerializer(serializers.ModelSerializer):
    investment=InvestmentSerializer(read_only=True)
    
    class Meta:
        model=InvestmentPayment
        fields=['id','investment',
                'amount','invested_at','confirmed','note'
                ]
        read_only_fields=['id','investor','invested_at','confirmed']

    
class ProductSaleShareSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = ProductSaleShare
        fields = ['id', 'total_sales_volume',
                  'profit_generated', 'investor_share',
                  'period_start', 'period_end', 'created_at']
        read_only_fields = ['id','created_at']

    
class PayoutSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    
    sale_share = ProductSaleShareSerializer(read_only=True)
    

    class Meta:
        model = Payout
        fields = ['id', 'investor',  'amount', 'status',
                  'payout_date', 'sale_share', ]
        read_only_fields = ['payout_date']

    

class InvestorWalletSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    

    class Meta:
        model = InvestorWallet
        fields = ['id', 'investor',  'balance', 'last_updated']
        read_only_fields = ['balance', 'last_updated']

    