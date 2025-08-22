from .views import (
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    ProductVariantListCreateAPIView,
    ProductVariantRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    FeaturedProductsAPIView,
    RelatedProductsAPIView,
    ProductVariantImageListCreateAPIView,
    ProductVariantImageRetrieveUpdateDestroyAPIView,
)
from django.urls import path

urlpatterns = [
    # -------------------- CATEGORIES --------------------
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),

    # -------------------- PRODUCTS --------------------
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/featured/', FeaturedProductsAPIView.as_view(), name='product-featured-list'),
    path('products/<slug:slug>/related/', RelatedProductsAPIView.as_view(), name='product-related-list'),
    path('products/<slug:slug>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-detail'),

    # -------------------- PRODUCT VARIANTS --------------------
    path('products/<int:product_id>/variants/', ProductVariantListCreateAPIView.as_view(), name='variant-list-create'),
    path('variants/<int:id>/', ProductVariantRetrieveUpdateDestroyAPIView.as_view(), name='variant-detail'),

    # -------------------- VARIANT IMAGES --------------------
    path('variants/<int:variant_id>/images/', ProductVariantImageListCreateAPIView.as_view(), name='variant-image-list-create'),
    path('variants/images/<int:id>/', ProductVariantImageRetrieveUpdateDestroyAPIView.as_view(), name='variant-image-detail'),
]
