from .views import (CheckoutAPIView,
                    OrderDetailAPIView,
                    OrderListAPIView,
                    OrderPaymentAPIView,
                    CancelOrderAPIView,
                    RazorpayOrderCreateAPIView,
                    RazorpayPaymentVerifyAPIView
                    )
from django.urls import path

urlpatterns = [
    path('checkout/',CheckoutAPIView.as_view()),
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/<int:id>/pay/', OrderPaymentAPIView.as_view(), name='order-pay'),
    path('orders/<int:id>/cancel/',CancelOrderAPIView.as_view()),
    path('orders/<int:id>/razorpay/', RazorpayOrderCreateAPIView.as_view()),
    path('orders/razorpay/verify/', RazorpayPaymentVerifyAPIView.as_view()),
]
