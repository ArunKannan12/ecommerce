from django.urls import path
from .views import (
    InvestorListCreateAPIView,
    InvestorDetailAPIView,
    InvestmentListCreateAPIView,
    InvestmentRetrieveUpdateDestroyAPIView,
    ProductSaleShareListAPIView,
    PayoutListCreateAPIView,
    InvestorWalletDetailAPIView,
    InvestmentSummaryDetailedAPIView,
    GenerateProductSalesShareAPIView
)

urlpatterns = [
    # Investor profile management
    path('investors/', InvestorListCreateAPIView.as_view(), name='investor-list-create'),
    path('investors/<int:pk>/', InvestorDetailAPIView.as_view(), name='investor-detail'),

    # Investments
    path('investments/', InvestmentListCreateAPIView.as_view(), name='investment-list-create'),
    path('investments/<int:pk>/', InvestmentRetrieveUpdateDestroyAPIView.as_view(), name='investment-detail'),

    path("investments/summary/", InvestmentSummaryDetailedAPIView.as_view(), name="investment-summary"),
    # Product Sale Shares
    path('product-sale-shares/', ProductSaleShareListAPIView.as_view(), name='product-sale-share-list-create'),

    # Payouts
    path('payouts/', PayoutListCreateAPIView.as_view(), name='payout-list-create'),

    # Wallet (individual investor or admin access)
    path('wallets/<int:investor_id>/', InvestorWalletDetailAPIView.as_view(), name='investor-wallet-detail'),

    path("generate-product-shares/", GenerateProductSalesShareAPIView.as_view(), name="generate-product-shares"),

]
