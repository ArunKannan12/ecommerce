# admin/urls.py
from django.urls import path
from .views import AdminDashboardStatsAPIView,ProductAdminCreateAPIView,ProductAdminDetailAPIView

urlpatterns = [
    path("dashboard-stats/", AdminDashboardStatsAPIView.as_view(), name="admin-dashboard-stats"),
    path('admin/products/',ProductAdminCreateAPIView.as_view(),name='admin-products'),
    path('admin/products/<int:id>/', ProductAdminDetailAPIView.as_view())

]
