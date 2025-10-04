from rest_framework import serializers
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Category, Product, ProductVariant, ProductVariantImage, Banner

# Configurable thresholds
LOW_STOCK_THRESHOLD = getattr(settings, "LOW_STOCK_THRESHOLD", 5)
NEW_PRODUCT_DAYS = getattr(settings, "NEW_PRODUCT_DAYS", 7)

# -------------------- CATEGORY --------------------
class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.data.get('remove_image') and instance.image:
            instance.image.delete(save=False)
            instance.image = None
        return super().update(instance, validated_data)

# -------------------- PRODUCT VARIANT IMAGE --------------------
class ProductVariantImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantImage
        fields = ['id', 'alt_text', 'image_url','image']
        extra_kwargs = {
            'alt_text': {'required': False}
        }

    def get_image_url(self, obj):
        return obj.url

# -------------------- PRODUCT VARIANT --------------------
class ProductVariantSerializer(serializers.ModelSerializer):
    images = ProductVariantImageSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    # Parent product info
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_category = serializers.CharField(source="product.category.name", read_only=True)
    product_created_at = serializers.DateTimeField(source="product.created_at", read_only=True)

    # Simplified flags
    is_returnable = serializers.BooleanField(source='allow_return', read_only=True)
    is_replaceable = serializers.BooleanField(source='allow_replacement', read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'variant_name', 'description', 'sku', 'base_price',
            'offer_price', 'final_price', 'discount_percent', 'stock',
            'is_low_stock', 'is_active', 'promoter_commission_rate', 'images', 'primary_image_url',
            'product_id', 'product_name', 'product_slug', 'product_category', 'product_created_at', 'is_new',
            'allow_return', 'return_days', 'allow_replacement', 'replacement_days', 'is_returnable', 'is_replaceable',
        ]
        extra_kwargs = {
            'variant_name': {'required': True},
            'stock': {'required': True},
            'base_price': {'required': True},
            'sku': {'required': False}
        }

    # ---------------- SerializerMethodFields ----------------
    def get_final_price(self, obj):
        return Decimal(obj.offer_price or obj.base_price)

    def get_discount_percent(self, obj):
        if obj.offer_price and obj.base_price and obj.offer_price < obj.base_price:
            return round(((obj.base_price - obj.offer_price) / obj.base_price) * 100)
        return 0

    def get_is_low_stock(self, obj):
        return 0 < obj.stock < LOW_STOCK_THRESHOLD

    def get_primary_image_url(self, obj):
        first_image = obj.images.first()
        if first_image and hasattr(first_image,'url'):
            return first_image.url
        return getattr(obj.product, 'image_url', None)

    def get_is_new(self, obj):
        return obj.product.created_at >= timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)

    def get_description(self, obj):
        return obj.description or obj.product.description

    # ---------------- Validation ----------------
    def validate(self, attrs):
        for flag_field, days_field in [('allow_return', 'return_days'), ('allow_replacement', 'replacement_days')]:
            if attrs.get(flag_field):
                days = attrs.get(days_field)
                if not days or days <= 0:
                    raise serializers.ValidationError(
                        {days_field: f"{days_field.replace('_', ' ').title()} must be greater than 0 if {flag_field.replace('_', ' ')} is True."}
                    )
            else:
                attrs[days_field] = None
        return attrs

    # ---------------- Update with multiple image removal ----------------
    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Remove main image if requested
        if request and request.data.get('remove_image') and getattr(instance, 'image', None):
            instance.image.delete(save=False)
            instance.image = None

        # Remove multiple images if IDs provided
        remove_image_ids = []
        if request:
            # FormData
            if hasattr(request.data, 'getlist'):
                remove_image_ids = request.data.getlist('remove_images')
            # JSON payload
            else:
                remove_image_ids = request.data.get('remove_images', [])

        if remove_image_ids and hasattr(instance, 'images'):
            images_to_remove = instance.images.filter(id__in=remove_image_ids)
            for img in images_to_remove:
                img.image.delete(save=False)
                img.delete()

        return super().update(instance, validated_data)


# -------------------- PRODUCT --------------------
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'is_available', 'featured',
            'created_at', 'image_url', 'category', 'variants',
            'min_price', 'max_price', 'total_stock', 'is_low_stock', 'is_new'
        ]

    # ---------------- Image URLs ----------------
    def get_image_url(self, obj):
        try:
            return obj.image_url or (obj.image.url if obj.image else None)
        except ValueError:
            return obj.image_url or None

    # ---------------- Calculated fields ----------------
    def get_min_price(self, obj):
        if obj.variants.exists():
            return min(v.final_price for v in obj.variants.all())
        return None

    def get_max_price(self, obj):
        if obj.variants.exists():
            return max(v.final_price for v in obj.variants.all())
        return None

    def get_total_stock(self, obj):
        return sum(v.stock for v in obj.variants.all())

    def get_is_low_stock(self, obj):
        return any(v.stock <= LOW_STOCK_THRESHOLD for v in obj.variants.all())

    def get_is_new(self, obj):
        return obj.created_at >= timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)

    # ---------------- Update with bulk image removal ----------------
    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Remove main product image if requested
        if request and request.data.get('remove_image') and getattr(instance, 'image', None):
            instance.image.delete(save=False)
            instance.image = None

        # Remove multiple product images if IDs provided
        remove_image_ids = request.data.get('remove_images') if request else []
        if remove_image_ids and hasattr(instance, 'images'):
            images_to_remove = instance.images.filter(id__in=remove_image_ids)
            for img in images_to_remove:
                img.image.delete(save=False)
                img.delete()

        return super().update(instance, validated_data)

# -------------------- BANNER --------------------
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image_url", "link_url", "order", "is_active"]
