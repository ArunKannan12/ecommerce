from django.urls import path
from .views import (
    ReferralCheckoutAPIView,
    CartCheckoutAPIView,
    BuyNowAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
    OrderSummaryListAPIView,
    OrderPaymentAPIView,
    CancelOrderAPIView,
    RazorpayOrderCreateAPIView,
    RazorpayPaymentVerifyAPIView,
    OrderItemListAPIView,
    PickOrderItemAPIView,
    PackOrderItemAPIView,
    ShipOrderItemAPIView,
    ShippingAddressListCreateView,
    ShippingAddressRetrieveUpdateDestroyView
)

urlpatterns = [
    # Checkout APIs
    path('checkout/referral/', ReferralCheckoutAPIView.as_view(), name='referral-checkout'),
    path('checkout/cart/', CartCheckoutAPIView.as_view(), name='cart-checkout'),
    path('checkout/buy-now/', BuyNowAPIView.as_view(), name='buy-now'),

    # Customer order APIs
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/summary/', OrderSummaryListAPIView.as_view(), name='order-summary'),
    path('orders/<int:id>/pay/', OrderPaymentAPIView.as_view(), name='order-payment'),
    path('orders/<int:id>/cancel/', CancelOrderAPIView.as_view(), name='order-cancel'),
    path('orders/<int:id>/razorpay/', RazorpayOrderCreateAPIView.as_view(), name='razorpay-create'),
    path('orders/razorpay/verify/', RazorpayPaymentVerifyAPIView.as_view(), name='razorpay-verify'),

    # Warehouse staff APIs for order items
    path('items/', OrderItemListAPIView.as_view(), name='orderitem-list'),
    path('items/<int:id>/pick/', PickOrderItemAPIView.as_view(), name='orderitem-pick'),
    path('items/<int:id>/pack/', PackOrderItemAPIView.as_view(), name='orderitem-pack'),
    path('items/<int:id>/ship/', ShipOrderItemAPIView.as_view(), name='orderitem-ship'),

    # Shipping address APIs
    path('shipping-addresses/', ShippingAddressListCreateView.as_view(), name='shipping-address-list-create'),
    path('shipping-addresses/<int:id>/', ShippingAddressRetrieveUpdateDestroyView.as_view(), name='shipping-address-detail'),
]
