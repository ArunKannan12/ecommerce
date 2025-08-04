from django.contrib import admin
from .models import Investor, Investment, ProductSaleShare, Payout, InvestorWallet


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'verification_status', 'net_worth', 'joined_at']
    search_fields = ['user__email', 'phone']
    list_filter = ['verification_status', 'joined_at']
    readonly_fields = ['joined_at', 'updated_at']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'amount', 'transaction_id', 'invested_at', 'confirmed']
    search_fields = ['transaction_id', 'investor__user__email']
    list_filter = ['confirmed', 'invested_at']
    readonly_fields = ['invested_at']


@admin.register(ProductSaleShare)
class ProductSaleShareAdmin(admin.ModelAdmin):
    list_display = ['investor', 'profit_generated', 'investor_share', 'period_start', 'period_end']
    list_filter = ['period_start', 'period_end']
    search_fields = ['investor__user__email']


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['investor', 'amount', 'status', 'payout_date']
    list_filter = ['status', 'payout_date']
    search_fields = ['investor__user__email']


@admin.register(InvestorWallet)
class InvestorWalletAdmin(admin.ModelAdmin):
    list_display = ['investor', 'balance', 'last_updated']
    readonly_fields = ['last_updated']
