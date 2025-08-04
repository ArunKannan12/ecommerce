from django.urls import path
from .views import (
    InvestorListCreateAPIView,
    InvestorDetailAPIView,
    InvestmentListCreateAPIView,
    InvestmentRetrieveUpdateDestroyAPIView,
    ProductSaleShareListCreateAPIView,
    PayoutListCreateAPIView,
    InvestorWalletDetailAPIView,
)

urlpatterns = [
    # Investor profile management
    path('investors/', InvestorListCreateAPIView.as_view(), name='investor-list-create'),
    path('investors/<int:pk>/', InvestorDetailAPIView.as_view(), name='investor-detail'),

    # Investments
    path('investments/', InvestmentListCreateAPIView.as_view(), name='investment-list-create'),
    path('investments/<int:pk>/', InvestmentRetrieveUpdateDestroyAPIView.as_view(), name='investment-detail'),

    # Product Sale Shares
    path('product-sale-shares/', ProductSaleShareListCreateAPIView.as_view(), name='product-sale-share-list-create'),

    # Payouts
    path('payouts/', PayoutListCreateAPIView.as_view(), name='payout-list-create'),

    # Wallet (individual investor or admin access)
    path('wallets/<int:investor_id>/', InvestorWalletDetailAPIView.as_view(), name='investor-wallet-detail'),
]
