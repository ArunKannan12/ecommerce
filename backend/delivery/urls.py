from django.urls import path
from .views import (
    DeliveryActionAPIView,
    DeliveryManRequestListCreateAPIView,
    DeliveryManRequestRetrieveUpdateDestroyAPIView,
    DeliveryManProfileUpdateAPIView,
    DeliveryDashboardAPIView,
    DeliveryDetailAPIView,
)

urlpatterns = [
    # ---------------- Orders / Delivery Actions ----------------
    path("deliveryman/orders/action/", DeliveryActionAPIView.as_view(), name="delivery-action"),

    # ---------------- DeliveryMan Requests ----------------
    path("request_for_deliveryman/", DeliveryManRequestListCreateAPIView.as_view(), name="deliveryman-request-list-create"),
    path("request_for_deliveryman/<int:id>/", DeliveryManRequestRetrieveUpdateDestroyAPIView.as_view(), name="deliveryman-request-detail"),

    # ---------------- DeliveryMan Profile ----------------
    path("deliveryman/profile/", DeliveryManProfileUpdateAPIView.as_view(), name="deliveryman-profile"),

    # ---------------- Dashboard / Detail ----------------
    path("deliveryman/dashboard/", DeliveryDashboardAPIView.as_view(), name="delivery-dashboard"),
    path("deliveryman/orders/", DeliveryDetailAPIView.as_view(), name="delivery-detail"),
]
