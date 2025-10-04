from django.urls import path
from .views import (
    # Checkout flows
    ReferralCheckoutAPIView,
    CartCheckoutAPIView,
    BuyNowAPIView,
    OrderPreviewAPIView,

    # Customer order flows
    OrderListAPIView,
    OrderDetailAPIView,
    OrderSummaryListAPIView,
    OrderPaymentAPIView,
    CancelOrderAPIView,
    RazorpayOrderCreateAPIView,
    RazorpayPaymentVerifyAPIView,

    # Warehouse item flows
    OrderItemListAPIView,

    # Shipping address flows
    ShippingAddressListCreateView,
    ShippingAddressRetrieveUpdateDestroyView,
)
from .returnReplacement import (
    # Return request flows
    ReturnRequestCreateAPIView,
    ReturnRequestUpdateAPIView,
    ReturnRequestListAPIView,
    ReturnRequestDetailAPIView,

    RefundStatusAPIView,
    ConfirmCODRefundAPIView,

    ReplacementRequestCreateAPIView,
    ReplacementRequestDetailAPIView,
    ReplacementRequestListAPIView,
    ReplacementRequestUpdateAPIView
   
)

urlpatterns = [
    # 🛒 Checkout APIs
    path('checkout/referral/', ReferralCheckoutAPIView.as_view(), name='checkout-referral'),
    path('checkout/cart/', CartCheckoutAPIView.as_view(), name='checkout-cart'),
    path('checkout/buy-now/', BuyNowAPIView.as_view(), name='checkout-buy-now'),
    path('checkout/preview/', OrderPreviewAPIView.as_view(), name='checkout-preview'),

    # 📦 Customer Order APIs
    path('orders/', OrderListAPIView.as_view(), name='orders-list'),
    path('orders/<str:order_number>/', OrderDetailAPIView.as_view(), name='orders-detail'),
    path('orders/summary/', OrderSummaryListAPIView.as_view(), name='orders-summary'),
    path('orders/<str:order_number>/pay/', OrderPaymentAPIView.as_view(), name='orders-pay'),
    path('orders/<str:order_number>/cancel/', CancelOrderAPIView.as_view(), name='orders-cancel'),
    path('orders/<str:order_number>/razorpay/', RazorpayOrderCreateAPIView.as_view(), name='orders-razorpay-create'),
    path('orders/razorpay/verify/', RazorpayPaymentVerifyAPIView.as_view(), name='orders-razorpay-verify'),
    
    # 🚚 Warehouse Item APIs
    path('items/', OrderItemListAPIView.as_view(), name='items-list'),
    
    # 🏠 Shipping Address APIs
    path('shipping-addresses/', ShippingAddressListCreateView.as_view(), name='shipping-addresses-list-create'),
    path('shipping-addresses/<int:id>/', ShippingAddressRetrieveUpdateDestroyView.as_view(), name='shipping-addresses-detail'),

   # Customer creates a return request
    path("returns/create/", ReturnRequestCreateAPIView.as_view(), name="return-create"),

    # Admin (or staff) updates return status (approve/reject/refunded etc.)
    path("returns/<int:pk>/update/", ReturnRequestUpdateAPIView.as_view(), name="return-update"),

    # List of return requests (customer → their own, admin → all)
    path("returns/", ReturnRequestListAPIView.as_view(), name="return-list"),

    # Details of a single return request
    # urls.py
    path("returns/<int:pk>/", ReturnRequestDetailAPIView.as_view()),
    path("refund-status/<int:order_number>/", RefundStatusAPIView.as_view(), name="refund-status"),

    path("cod-refund/confirm/<int:order_id>/", ConfirmCODRefundAPIView.as_view(), name="confirm-cod-refund"),

    # replacements/ endpoints should use plural like returns/
    path("replacements/create/", ReplacementRequestCreateAPIView.as_view(), name="replacement-create"),
    path("replacements/<int:pk>/update/", ReplacementRequestUpdateAPIView.as_view(), name="replacement-update"),
    path("replacements/", ReplacementRequestListAPIView.as_view(), name="replacement-list"),
    path("replacements/<int:pk>/", ReplacementRequestDetailAPIView.as_view(), name="replacement-detail"),

]