from django.contrib import admin
from .models import Promoter

@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'phone_number', 
        'referral_code',
        'bank_account_number', 'ifsc_code', 
        'bank_name', 'account_holder_name',
        'deposit_amount', 'application_status',
        'submitted_at', 'approved_at',
        'total_sales_count', 'total_commission_earned',
        'wallet_balance', 'is_eligible_for_withdrawal'
    ]

    list_filter = ['application_status']
    search_fields = [
        'phone_number', 
        'user__username', 'user__email',
        'bank_account_number', 'account_holder_name',
    ]
    readonly_fields = ['submitted_at', 'approved_at','referral_code']
    ordering = ['-submitted_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number')
        }),
        ('Referral code',{
            'fields':('referral_code',)
        }),
        ('Bank Details', {
            'fields': ('bank_account_number', 'ifsc_code', 'bank_name', 'account_holder_name')
        }),
        ('Application Status', {
            'fields': ('application_status', 'submitted_at', 'approved_at')
        }),
        ('Performance & Wallet', {
            'fields': ('deposit_amount', 'total_sales_count', 'total_commission_earned', 'wallet_balance', 'is_eligible_for_withdrawal')
        }),
    )
