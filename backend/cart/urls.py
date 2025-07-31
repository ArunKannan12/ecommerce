from .views import CartItemRetrieveUpdateDestroyAPIView,CartItemListCreateApiView
from django.urls import path

urlpatterns = [
    path('cart/',CartItemListCreateApiView.as_view()),
    path('cart/<int:id>/',CartItemRetrieveUpdateDestroyAPIView.as_view()),
]
