from django.urls import path
from .views import (
    DeliveryManListCreateAPIView,
    DeliveryManRetrieveUpdateDestroy,
    MarkCODOrderDeliveredAndPaidAPIView,
    ShippedOrderForDeliveryAPIView
)

urlpatterns = [
    # Delivery man profile routes
    path('deliverymen/', DeliveryManListCreateAPIView.as_view(), name='deliveryman-list-create'),
    path('deliverymen/<int:pk>/', DeliveryManRetrieveUpdateDestroy.as_view(), name='deliveryman-detail'),

    # COD Order delivery & payment confirmation
    path('orders/<int:id>/cod-paid-delivered/', MarkCODOrderDeliveredAndPaidAPIView.as_view(), name='cod-order-delivered-paid'),
    path("orders/shipped/",ShippedOrderForDeliveryAPIView .as_view(), name="shipped-orders")
]
