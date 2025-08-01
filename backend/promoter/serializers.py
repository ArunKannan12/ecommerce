from rest_framework import serializers
from .models import Promoter

class PromoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promoter
        fields = [
            'id',
            'user',
            'referral_code',
            'phone_number',
            'bank_account_number',
            'ifsc_code',
            'bank_name',
            'account_holder_name',
            'deposit_amount',
            'application_status',
            'submitted_at',
            'approved_at',
            'total_sales_count',
            'total_commission_earned',
            'wallet_balance',
            'is_eligible_for_withdrawal',
        ]
        read_only_fields = [
            'application_status',
            'submitted_at',
            'approved_at',
            'total_sales_count',
            'total_commission_earned',
            'wallet_balance',
            'is_eligible_for_withdrawal',
            'user',
            'referral_code'
        ]
