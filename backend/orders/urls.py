from django.urls import path
from .views import (
    ReferralCheckoutAPIView,
    CartCheckoutAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    OrderPaymentAPIView,
    CancelOrderAPIView,
    RazorpayOrderCreateAPIView,
    RazorpayPaymentVerifyAPIView
)

urlpatterns = [
    # Checkout endpoints
    path("checkout/cart/", CartCheckoutAPIView.as_view(), name="checkout-cart"),
    path("checkout/referral/", ReferralCheckoutAPIView.as_view(), name="checkout-referral"),

    # Order endpoints
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("orders/<int:id>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("orders/<int:id>/pay/", OrderPaymentAPIView.as_view(), name="order-pay"),
    path("orders/<int:id>/cancel/", CancelOrderAPIView.as_view(), name="order-cancel"),

    # Razorpay endpoints
    path("orders/<int:id>/razorpay/", RazorpayOrderCreateAPIView.as_view(), name="razorpay-create"),
    path("orders/razorpay/verify/", RazorpayPaymentVerifyAPIView.as_view(), name="razorpay-verify"),
]
