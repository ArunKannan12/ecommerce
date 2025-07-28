from rest_framework import generics,permissions
from .models import Product,ProductImage,ProductVariant,Category
from .serializers import (
                        ProductSerializer,
                        ProductImageSerializer,
                        CategorySerializer,
                        ProductVariantSerializer
                        )
from django.conf import settings
class ProductListCreateApiView(generics.ListCreateAPIView):
    permission_classes=[permissions.AllowAny]
    serializer_class=ProductSerializer

    def get_queryset(self):
        return Product.objects.all()

class ProductRetrieveUpdateDestroyApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes=[permissions.IsAuthenticated]
    serializer_class=ProductSerializer

    def get_queryset(self):
        return Product.objects.all()