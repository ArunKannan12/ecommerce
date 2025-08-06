from .models import Investment, Investor, InvestorWallet, Payout, ProductSaleShare,InvestmentPayment
from rest_framework import serializers


class InvestorSerializer(serializers.ModelSerializer):
    total_confirmed_investments=serializers.DecimalField(max_digits=12,decimal_places=2,read_only=True)
    class Meta:
        model = Investor
        fields = [
            'id', 'phone', 'net_worth', 'profile_image', 'address',
            'verification_status', 'joined_at', 'updated_at','total_confirmed_investments'
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at','total_confirmed_investments']



class InvestmentSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id=serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(),write_only=True)
    class Meta:
        model = Investment
        fields = ['id', 'investor', 'amount','investor_id',
                  'invested_at', 
                  'confirmed', 'note'
                  ]

        read_only_fields = ['investor', 'invested_at', 'confirmed']

    def create(self, validated_data):
        investor=validated_data.pop('investor_id')
        investment=Investment.objects.create(investor=investor,**validated_data)
        return investment

class InvestmentPaymentSerializer(serializers.ModelSerializer):
    investment=InvestmentSerializer(read_only=True)
    investment_id=serializers.PrimaryKeyRelatedField(queryset=Investment.objects.all(),write_only=True)   
    class Meta:
        model=Investment
        fields=['id','investment','investment_id',
                'amount','invested_at','confirmed','note'
                ]
        read_only_fields=['id','investor','invested_at','confirmed']

    def create(self, validated_data):
        investment=validated_data.pop('investment_id')
        return InvestmentPayment.objects.create(investment=investment,**validated_data)
    
class ProductSaleShareSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id=serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(),write_only=True)

    class Meta:
        model = ProductSaleShare
        fields = ['id', 'investor','investor_id','total_sales_volume',
                  'profit_generated', 'investor_share',
                  'period_start', 'period_end', 'created_at']
        read_only_fields = ['id','created_at']

    def create(self, validated_data):
        investor = validated_data.pop('investor_id')
        return ProductSaleShare.objects.create(investor=investor, **validated_data)


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

    def create(self, validated_data):
        investor = validated_data.pop('investor_id')
        sale_share = validated_data.pop('sale_share_id', None)
        return Payout.objects.create(investor=investor, sale_share=sale_share, **validated_data)
    

class InvestorWalletSerializer(serializers.ModelSerializer):
    investor = InvestorSerializer(read_only=True)
    investor_id = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all(), write_only=True)

    class Meta:
        model = InvestorWallet
        fields = ['id', 'investor', 'investor_id', 'balance', 'last_updated']
        read_only_fields = ['balance', 'last_updated']

    def create(self, validated_data):
        investor = validated_data.pop('investor_id')
        return InvestorWallet.objects.create(investor=investor, **validated_data)