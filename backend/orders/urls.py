from django.urls import path
from .views import (
    ReferralCheckoutAPIView,
    CartCheckoutAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
    OrderPaymentAPIView,
    CancelOrderAPIView,
    RazorpayOrderCreateAPIView,
    RazorpayPaymentVerifyAPIView,
    PickOrderItemAPIView,
    PackOrderItemAPIView,
    ShipOrderItemAPIView,
    OrderItemListAPIView
)

urlpatterns = [
    # Checkout APIs
    path('checkout/referral/', ReferralCheckoutAPIView.as_view(), name='referral-checkout'),
    path('checkout/cart/', CartCheckoutAPIView.as_view(), name='cart-checkout'),

    # Order views for customers
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderDetailAPIView.as_view(), name='order-detail'),

    # Payment-related
    path('orders/<int:id>/pay/', OrderPaymentAPIView.as_view(), name='order-payment'),
    path('orders/<int:id>/cancel/', CancelOrderAPIView.as_view(), name='order-cancel'),
    path('orders/<int:id>/razorpay/', RazorpayOrderCreateAPIView.as_view(), name='razorpay-create'),
    path('orders/razorpay/verify/', RazorpayPaymentVerifyAPIView.as_view(), name='razorpay-verify'),

    # Warehouse staff APIs
    path("items/", OrderItemListAPIView.as_view(), name=""),
    path('items/<int:id>/pick/', PickOrderItemAPIView.as_view(), name='orderitem-pick'),
    path('items/<int:id>/pack/', PackOrderItemAPIView.as_view(), name='orderitem-pack'),
    path('items/<int:id>/ship/', ShipOrderItemAPIView.as_view(), name='orderitem-ship'),
]