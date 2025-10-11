from django.urls import path
from .views import (
    WarehouseOrderListAPIView,
    PickOrderItemAPIView,
    PackOrderItemAPIView,
    ShipOrderItemAPIView,
    AssignOrdersToDeliverymanAPIView,
    WarehouseOrderItemStatusAPIView,
    WarehouseAssignedOrdersAPIView,
    WarehouseStatsWithTrendsAPIView,
    WarehouseUnassignedOrdersAPIView,
    DeliverymanListForAssignmentAPIView
)

urlpatterns = [
    # List all orders for warehouse staff
    path("warehouse/stats/", WarehouseStatsWithTrendsAPIView.as_view(), name="warehouse-stats"),
    path("warehouse/orders/", WarehouseOrderListAPIView.as_view(), name="warehouse-order-list"),

    # Pick, Pack, Ship single order item
    path("warehouse/items/<int:id>/pick/", PickOrderItemAPIView.as_view(), name="items-pick"),
    path("warehouse/items/<int:id>/pack/", PackOrderItemAPIView.as_view(), name="items-pack"),
    path("warehouse/items/<int:id>/ship/", ShipOrderItemAPIView.as_view(), name="items-ship"),

    # Assign multiple orders to a deliveryman
    path("warehouse/orders/assign/deliveryman/", AssignOrdersToDeliverymanAPIView.as_view(), name="assign-order-deliveryman"),
    path("warehouse/orders/assigned-orders/", WarehouseAssignedOrdersAPIView.as_view(), name="warehouse-assigned-orders"),
    path("warehouse/orders/unassigned-orders/", WarehouseUnassignedOrdersAPIView.as_view(), name="warehouse-unassigned-orders"),
    # urls.py
    path("warehouse/deliverymen/", DeliverymanListForAssignmentAPIView.as_view(), name="warehouse-deliverymen-list"),

    # List all order items by status (pending, picked, packed, shipped, out_for_delivery, failed)
    path("order-items/status/", WarehouseOrderItemStatusAPIView.as_view(), name="warehouse-order-item-status"),
]
