from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductVariantImage,Banner


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

            # parent product info
            'product_id',
            'product_name',
            'product_slug',
            'product_category',

            # return/replacement info
            'is_returnable',
            'return_days',
            'is_replacement_only',
            'replacement_days',
        ]
    def get_final_price(self, obj):
        # Use offer_price if available and less than base_price, otherwise base_price
        if obj.offer_price and obj.offer_price < obj.base_price:
            return obj.offer_price
        return obj.base_price
    
    def validate(self, attrs):
        # Enforce that both returnable and replacement_only cannot be True
        if attrs.get('is_returnable') and attrs.get('is_replacement_only'):
            raise serializers.ValidationError("A product cannot be both returnable and replacement-only.")

        # Return days validation
        if attrs.get('is_returnable'):
            if not attrs.get('return_days') or attrs['return_days'] <= 0:
                raise serializers.ValidationError("Return days must be greater than 0 if the product is returnable.")
        else:
            attrs['return_days'] = None

        # Replacement days validation
        if attrs.get('is_replacement_only'):
            if not attrs.get('replacement_days') or attrs['replacement_days'] <= 0:
                raise serializers.ValidationError("Replacement days must be greater than 0 if the product allows replacement.")
        else:
            attrs['replacement_days'] = None

        return attrs

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


class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image_url", "link_url", "order", "is_active"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None