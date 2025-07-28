from django.urls import path
from .views import (
    ProductListCreateApiView,
    ProductRetrieveUpdateDestroyApiView,
    ProductVariantListCreateAPIView,
    ProductVariantRetrieveUpdateDestroyAPIView,
    ProductImageListCreateAPIView,
    ProductImageRetrieveUpdateDestroyAPIView
)

urlpatterns = [
    # ----- PRODUCT -----
    path('products/', ProductListCreateApiView.as_view(), name='product-list-create'),
    path('products/<int:id>/', ProductRetrieveUpdateDestroyApiView.as_view(), name='product-detail'),

    # ----- VARIANTS -----
    path('products/<int:product_id>/variants/', ProductVariantListCreateAPIView.as_view(), name='variant-list-create'),
    path('variants/<int:id>/', ProductVariantRetrieveUpdateDestroyAPIView.as_view(), name='variant-detail'),

    # ----- IMAGES -----
    path('products/<int:product_id>/images/', ProductImageListCreateAPIView.as_view(), name='image-list-create'),
    path('images/<int:id>/', ProductImageRetrieveUpdateDestroyAPIView.as_view(), name='image-detail'),
]
