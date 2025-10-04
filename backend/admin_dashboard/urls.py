# admin/urls.py
from django.urls import path
from .views import (
                    AdminDashboardStatsAPIView,
                    ProductAdminCreateAPIView,
                    ProductAdminDetailAPIView,
                    ProductBulkActionAPIView,
                    CustomerBlockAPIView,
                    CustomerListAPIView,
                    CustomerDetailAPIView,
                    AdminOrderListAPIView,
                    AdminOrderDetailAPIView,
                    AdminReturnRequestdetailAPIView,
                    AdminReturnRequestListAPIView,
                    AdminReplacementRequestdetailAPIView,
                    AdminReplacementRequestListAPIView,
                    WarehouseLogDetailAPIView,
                    WarehouseLogListAPIView,
                    WarehouseTimelineAPIView,
                    AdminApproveDeliveryManRequestAPIView,
                    AdminDeliveryManRequestListAPIView,
                    AdminRejectDeliveryManRequestAPIView,
                    AdminDeliveryManReuestDetailAPIView,
                    AdminDeliveryManListAPIView,
                    AdminDeliveryManDetailAPIView,
                    AdminToggleDeliveryManActiveAPIView,
                    AdminDeliveryTrackingAPIView,
                    AdminDeliveryTrackingDetailAPIView,
                    AdminDeliveryManStatsAPIView,
                    AdminBannerListAPIView,
                    BannerCreateAPIView,
                    BannerUpdateDestroyAPIView
                    )
from orders.returnReplacement import ReturnRequestUpdateAPIView,ReplacementRequestUpdateAPIView

urlpatterns = [
    path("dashboard-stats/", AdminDashboardStatsAPIView.as_view(), name="admin-dashboard-stats"),
    path('admin/create-products/',ProductAdminCreateAPIView.as_view(),name='admin-products'),
    path('admin/products/<int:id>/', ProductAdminDetailAPIView.as_view()),
    path("admin/products/bulk-action/", ProductBulkActionAPIView.as_view(), name=""),
    
    path('admin/customers/', CustomerListAPIView.as_view(), name='admin-customer-list'),
    path("admin/customers/<int:id>/", CustomerDetailAPIView.as_view(), name="admin-customer-detail"),
    path('admin/customers/<int:pk>/block/', CustomerBlockAPIView.as_view(), name='admin-customer-block'),

    path("admin/orders/", AdminOrderListAPIView.as_view(), name="admin-order-list"),
    path("admin/orders/<str:order_number>/", AdminOrderDetailAPIView.as_view(), name="admin-order-detail"),

    path("admin/returns/", AdminReturnRequestListAPIView.as_view(), name="admin-return-list"),
    path("admin/returns/<int:pk>/", AdminReturnRequestdetailAPIView.as_view(), name="admin-return-detail"),
    path("admin/returns/<int:pk>/update/", ReturnRequestUpdateAPIView.as_view(), name="admin-return-update"),

    path("admin/replacements/", AdminReplacementRequestListAPIView.as_view(), name="admin-return-list"),
    path("admin/replacements/<int:pk>/", AdminReplacementRequestdetailAPIView.as_view(), name="admin-return-detail"),
    path("admin/replacements/<int:pk>/update/", ReplacementRequestUpdateAPIView.as_view(), name="admin-return-update"),

    path("admin/warehouse-logs/", WarehouseLogListAPIView.as_view(), name="warehouse-logs"),
    path("admin/warehouse-timeline/", WarehouseTimelineAPIView.as_view(), name=""),
    path("admin/warehouse-logs/<int:id>/", WarehouseLogDetailAPIView.as_view(), name="warehouse-log-detail"),

    path('admin/deliveryman-requests/', AdminDeliveryManRequestListAPIView.as_view(), name='admin-deliveryman-requests'),
    path('admin/deliveryman-requests/<int:id>/', AdminDeliveryManReuestDetailAPIView.as_view(), name='admin-deliveryman-requests-detail'),
    path('admin/deliveryman-requests/<int:request_id>/approve/', AdminApproveDeliveryManRequestAPIView.as_view(), name='admin-approve-deliveryman-request'),
    path('admin/deliveryman-requests/<int:request_id>/reject/', AdminRejectDeliveryManRequestAPIView.as_view(), name='admin-reject-deliveryman-request'),

    path('admin/deliverymen/', AdminDeliveryManListAPIView.as_view(), name='admin-deliveryman-list'),
    path('admin/deliverymen/<int:id>/', AdminDeliveryManDetailAPIView.as_view(), name='admin-deliveryman-detail'),
    path('admin/deliverymen/<int:deliveryman_id>/toggle-active/', AdminToggleDeliveryManActiveAPIView.as_view(), name='admin-deliveryman-toggle-active'),

    # Delivery tracking
    path('admin/delivery-tracking/', AdminDeliveryTrackingAPIView.as_view(), name='admin-delivery-tracking'),
    path('admin/delivery-tracking/<int:id>/', AdminDeliveryTrackingDetailAPIView.as_view(), name='admin-delivery-tracking-detail'),

    # Deliveryman stats / performance
    path('admin/deliverymen/<int:id>/stats/', AdminDeliveryManStatsAPIView.as_view(), name='admin-deliveryman-stats'),

    path("admin/banners/", AdminBannerListAPIView.as_view(), name="admin-banner-list"),
    path("admin/banners/create/", BannerCreateAPIView.as_view(), name="banner-create"),
    path("admin/banners/<int:pk>/", BannerUpdateDestroyAPIView.as_view(), name="banner-update-destroy"),

]


