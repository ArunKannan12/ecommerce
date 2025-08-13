from .views import (
    ProductListCreateApiView,
    ProductRetrieveUpdateDestroyApiView,
    ProductVariantListCreateAPIView,
    ProductVariantRetrieveUpdateDestroyAPIView,
    ProductImageListCreateAPIView,
    ProductImageRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    FeaturedProducts,
    RelatedProductsAPIView,
    ProductVariantImageListCreateAPIView,           # new import
    ProductVariantImageRetrieveUpdateDestroyAPIView, # new import
)
from django.urls import path

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),

    # ----- PRODUCT -----
    path('products/', ProductListCreateApiView.as_view(), name='product-list-create'),
    path("products/featured/", FeaturedProducts.as_view(), name="product-featured-list"),
    path("products/<slug:slug>/related/", RelatedProductsAPIView.as_view(), name=""),
    path('products/<slug:slug>/', ProductRetrieveUpdateDestroyApiView.as_view(), name='product-detail'),

    # ----- VARIANTS -----
    path('products/<int:product_id>/variants/', ProductVariantListCreateAPIView.as_view(), name='variant-list-create'),
    path('variants/<int:id>/', ProductVariantRetrieveUpdateDestroyAPIView.as_view(), name='variant-detail'),

    # ----- PRODUCT IMAGES -----
    path('products/<int:product_id>/images/', ProductImageListCreateAPIView.as_view(), name='image-list-create'),
    path('images/<int:id>/', ProductImageRetrieveUpdateDestroyAPIView.as_view(), name='image-detail'),

    # ----- VARIANT IMAGES -----
    path('variants/<int:variant_id>/images/', ProductVariantImageListCreateAPIView.as_view(), name='variant-image-list-create'),
    path('variants/images/<int:id>/', ProductVariantImageRetrieveUpdateDestroyAPIView.as_view(), name='variant-image-detail'),
]
