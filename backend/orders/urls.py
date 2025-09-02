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
    PickOrderItemAPIView,
    PackOrderItemAPIView,
    ShipOrderItemAPIView,

    # Shipping address flows
    ShippingAddressListCreateView,
    ShippingAddressRetrieveUpdateDestroyView,

    # Return request flows
    ReturnRequestCreateAPIView,
    ReturnRequestUpdateAPIView,
    ReturnRequestListAPIView,
    ReturnRequestDetailAPIView,

    RefundStatusAPIView
   
)

urlpatterns = [
    # 🛒 Checkout APIs
    path('checkout/referral/', ReferralCheckoutAPIView.as_view(), name='checkout-referral'),
    path('checkout/cart/', CartCheckoutAPIView.as_view(), name='checkout-cart'),
    path('checkout/buy-now/', BuyNowAPIView.as_view(), name='checkout-buy-now'),
    path('checkout/preview/', OrderPreviewAPIView.as_view(), name='checkout-preview'),

    # 📦 Customer Order APIs
    path('orders/', OrderListAPIView.as_view(), name='orders-list'),
    path('orders/<int:id>/', OrderDetailAPIView.as_view(), name='orders-detail'),
    path('orders/summary/', OrderSummaryListAPIView.as_view(), name='orders-summary'),
    path('orders/<int:id>/pay/', OrderPaymentAPIView.as_view(), name='orders-pay'),
    path('orders/<int:id>/cancel/', CancelOrderAPIView.as_view(), name='orders-cancel'),
    path('orders/<int:id>/razorpay/', RazorpayOrderCreateAPIView.as_view(), name='orders-razorpay-create'),
    path('orders/razorpay/verify/', RazorpayPaymentVerifyAPIView.as_view(), name='orders-razorpay-verify'),
    
    # 🚚 Warehouse Item APIs
    path('items/', OrderItemListAPIView.as_view(), name='items-list'),
    path('items/<int:id>/pick/', PickOrderItemAPIView.as_view(), name='items-pick'),
    path('items/<int:id>/pack/', PackOrderItemAPIView.as_view(), name='items-pack'),
    path('items/<int:id>/ship/', ShipOrderItemAPIView.as_view(), name='items-ship'),

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
    path("returns/<int:pk>/", ReturnRequestDetailAPIView.as_view(), name="return-detail"),
    path("refund-status/<int:order_id>/", RefundStatusAPIView.as_view(), name="refund-status"),
]