from django.urls import path
from .views import (
    WarehouseOrderListAPIView,
    PickOrderItemAPIView,
    PackOrderItemAPIView,
    ShipOrderItemAPIView,
    AssignOrdersToDeliverymanAPIView,
    WarehouseOrderItemStatusAPIView,
    WarehouseAssignedOrdersAPIView
)

urlpatterns = [
    # List all orders for warehouse staff
    path("warehouse/orders/", WarehouseOrderListAPIView.as_view(), name="warehouse-order-list"),

    # Pick, Pack, Ship single order item
    path("items/<int:id>/pick/", PickOrderItemAPIView.as_view(), name="items-pick"),
    path("items/<int:id>/pack/", PackOrderItemAPIView.as_view(), name="items-pack"),
    path("items/<int:id>/ship/", ShipOrderItemAPIView.as_view(), name="items-ship"),

    # Assign multiple orders to a deliveryman
    path("orders/assign/deliveryman/", AssignOrdersToDeliverymanAPIView.as_view(), name="assign-order-deliveryman"),
    path("orders/assigned/", WarehouseAssignedOrdersAPIView.as_view(), name="warehouse-assigned-orders"),

    # List all order items by status (pending, picked, packed, shipped, out_for_delivery, failed)
    path("order-items/status/", WarehouseOrderItemStatusAPIView.as_view(), name="warehouse-order-item-status"),
]
