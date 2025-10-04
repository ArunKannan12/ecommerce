from django.urls import path
from .views import (
    MarkOrderDeliveredAPIView,
    ShippedOrderForDeliveryAPIView,
    DeliveryManRequestListCreateAPIView,
    DeliveryManProfileUpdateAPIView,
    MarkOrderDeliveryFailedAPIView,
    SendDeliveryOTPAPIView,
    ResendDeliveryOTPAPIView,
    VerifyDeliveryOTPAPIView,
    DeliveryManRequestRetrieveUpdateDestroyAPIView
)

urlpatterns = [
    # Mark order as delivered (COD or online payment)
    path("orders/<int:id>/mark-delivered/",MarkOrderDeliveredAPIView.as_view(),name="order-mark-delivered"),
    path("orders/<int:order_id>/failed/", MarkOrderDeliveryFailedAPIView.as_view(), name="mark-order-failed"),

    # List shipped orders (for deliveryman or admin)
    path("orders/shipped/",ShippedOrderForDeliveryAPIView.as_view(),name="shipped-orders"
    ),

    # DeliveryMan Requests
    path( "request_for_deliveryman/", DeliveryManRequestListCreateAPIView.as_view(), name="deliveryman-request-list-create"
    ),
    path(
        "request_for_deliveryman/<int:id>/",
        DeliveryManRequestRetrieveUpdateDestroyAPIView.as_view(),
        name="deliveryman-request-detail",
    ),
    
    path("deliveryman/profile/", DeliveryManProfileUpdateAPIView.as_view(), name="deliveryman-profile"),
    
    path('delivery/send-otp/<int:item_id>/', SendDeliveryOTPAPIView.as_view(), name='send-delivery-otp'),
    path('delivery/resend-otp/', ResendDeliveryOTPAPIView.as_view(), name='resend-delivery-otp'),
    path('delivery/verify-otp/', VerifyDeliveryOTPAPIView.as_view(), name='verify-delivery-otp'),
]