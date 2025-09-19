from django.urls import path
from .views import (
    MarkOrderDeliveredAPIView,
    ShippedOrderForDeliveryAPIView,
    DeliveryManRequestListCreateAPIView,
    ApproveDeliveryManRequestAPIView,
    RejectDeliveryManRequestAPIView,
    DeliveryManProfileUpdateAPIView,
    MarkOrderDeliveryFailedAPIView,
    SendDeliveryOTPAPIView,
    ResendDeliveryOTPAPIView,
    VerifyDeliveryOTPAPIView
)

urlpatterns = [
    # Mark order as delivered (COD or online payment)
    path("orders/<int:id>/mark-delivered/",MarkOrderDeliveredAPIView.as_view(),name="order-mark-delivered"),
    path("orders/<int:order_id>/failed/", MarkOrderDeliveryFailedAPIView.as_view(), name="mark-order-failed"),

    # List shipped orders (for deliveryman or admin)
    path("orders/shipped/",ShippedOrderForDeliveryAPIView.as_view(),name="shipped-orders"
    ),

   

    # DeliveryMan Requests
    path( "requests/", DeliveryManRequestListCreateAPIView.as_view(), name="deliveryman-request-list-create"
    ),

    # Approve a deliveryman request (admin only)
    path( "requests/<int:request_id>/approve/", ApproveDeliveryManRequestAPIView.as_view(), name="deliveryman-request-approve"
    ),

    # Reject a deliveryman request (admin only)
    path("requests/<int:request_id>/reject/",RejectDeliveryManRequestAPIView.as_view(),name="deliveryman-request-reject"
    ),
    path("deliveryman/profile/", DeliveryManProfileUpdateAPIView.as_view(), name="deliveryman-profile"),
    
    path('delivery/send-otp/<int:item_id>/', SendDeliveryOTPAPIView.as_view(), name='send-delivery-otp'),
    path('delivery/resend-otp/', ResendDeliveryOTPAPIView.as_view(), name='resend-delivery-otp'),
    path('delivery/verify-otp/', VerifyDeliveryOTPAPIView.as_view(), name='verify-delivery-otp'),
]