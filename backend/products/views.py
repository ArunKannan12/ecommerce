from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, ProductVariant, Category, ProductVariantImage,Banner
from .serializers import (
    ProductSerializer, CategorySerializer,BannerSerializer,
    ProductVariantSerializer, ProductVariantImageSerializer
)
from accounts.permissions import IsAdmin, IsAdminOrReadOnly
from rest_framework.exceptions import ValidationError


# -------------------- CATEGORIES --------------------
class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admin can create


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


# -------------------- PRODUCTS --------------------
class ProductListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['featured', 'is_available']
    search_fields = ['name', 'description', 'slug','variants__variant_name','variants__description','variants__sku']
    ordering_fields = ['created_at', 'name']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Product.objects.select_related('category').order_by('-created_at')
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(is_available=True)
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs.distinct()


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Product.objects.select_related('category')
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            qs = qs.filter(is_available=True)
        return qs


# -------------------- PRODUCT VARIANTS --------------------
class ProductVariantListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductVariantSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['variant_name', 'sku']
    ordering_fields = ['base_price','offer_price', 'stock']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductVariant.objects.filter(product_id=product_id).select_related('product')

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        serializer.save(product_id=product_id)

    def perform_update(self, serializer):
        # Ensures validation for returnable/replacement fields is applied
        serializer.is_valid(raise_exception=True)
        serializer.save()


class ProductVariantRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantSerializer
    lookup_field = 'id'
    queryset = ProductVariant.objects.select_related('product')

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
# -------------------- FEATURED & RELATED --------------------
class FeaturedProductsAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(featured=True, is_available=True).order_by('-created_at')


class RelatedProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise ValidationError("Product not found")
        return Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id).order_by('created_at')[:6]


# -------------------- VARIANT IMAGES --------------------
class ProductVariantImageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductVariantImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        variant_id = self.kwargs.get('variant_id')
        return ProductVariantImage.objects.filter(variant_id=variant_id)

    def perform_create(self, serializer):
        variant_id = self.kwargs.get('variant_id')
        serializer.save(variant_id=variant_id)


class ProductVariantImageRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        return ProductVariantImage.objects.all()

# CUSTOMER: list only active banners (no filters, no search)
class CustomerBannerListAPIView(generics.ListAPIView):
    queryset = Banner.objects.filter(is_active=True).order_by("order")
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]


# ADMIN: list all banners with search & filtering
class AdminBannerListAPIView(generics.ListAPIView):
    queryset = Banner.objects.all().order_by("order")
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAdminUser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]   # ?is_active=true/false
    search_fields = ["title", "subtitle"]  # ?search=summer
    ordering_fields = ["order", "created_at"]  # ?ordering=order or ?ordering=-created_at


# ADMIN: create banners
class BannerCreateAPIView(generics.CreateAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAdminUser]


# ADMIN: retrieve, update, delete
class BannerUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAdminUser]
