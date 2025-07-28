from rest_framework import generics,permissions,filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product,ProductVariant,ProductImage
from .serializers import (
                        ProductSerializer,
                        ProductImageSerializer,ProductVariantSerializer
                        )
from accounts.permissions import IsAdmin
class ProductListCreateApiView(generics.ListCreateAPIView):

    serializer_class=ProductSerializer

    filter_backends=[
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['created_at', 'price', 'name']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')
    

class ProductRetrieveUpdateDestroyApiView(generics.RetrieveUpdateDestroyAPIView):
   
    serializer_class=ProductSerializer
    lookup_field='id'
    def get_permissions(self):
        if self.request.method in ['PUT','PATCH','DELETE']:
            return [IsAdmin()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        return Product.objects.all()
    
class ProductVariantListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductVariantSerializer
    filter_backends=[
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    search_fields = ['variant_name', 'sku']
    ordering_fields = ['additional_price', 'stock']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductVariant.objects.filter(product_id=product_id)

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        serializer.save(product_id=product_id)


class ProductVariantRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantSerializer
    lookup_field = 'id'
    queryset = ProductVariant.objects.all()

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        return [permissions.AllowAny()]

# ----- IMAGES -----

class ProductImageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductImageSerializer

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductImage.objects.filter(product_id=product_id)

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        serializer.save(product_id=product_id)


class ProductImageRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductImageSerializer
    lookup_field = 'id'
    queryset = ProductImage.objects.all()

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        return [permissions.AllowAny()]