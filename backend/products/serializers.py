from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductVariantImage


# -------------------- CATEGORY --------------------
class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image_url:
            return obj.image_url
        elif obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


# -------------------- PRODUCT VARIANT IMAGE --------------------
class ProductVariantImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantImage
        fields = ['id', 'url', 'alt_text']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.image_url:
            return obj.image_url
        elif obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


# -------------------- PRODUCT VARIANT --------------------
class ProductVariantSerializer(serializers.ModelSerializer):
    images = ProductVariantImageSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()

    # include parent product info
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_category = serializers.CharField(source="product.category.name", read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'variant_name',
            'sku',
            'base_price',
            'offer_price',
            'final_price',
            'stock',
            'is_active',
            'promoter_commission_rate',
            'images',

            # new fields
            'product_id',
            'product_name',
            'product_slug',
            'product_category',
        ]

    def get_final_price(self, obj):
        # Use offer_price if available and less than base_price, otherwise base_price
        if obj.offer_price and obj.offer_price < obj.base_price:
            return obj.offer_price
        return obj.base_price

# -------------------- PRODUCT --------------------
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_available',
            'featured',
            'created_at',
            'image_url',
            'category',
            'variants',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image_url:
            return obj.image_url
        elif obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
