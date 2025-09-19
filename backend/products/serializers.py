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
    discount_percent = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()

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
            'id','variant_name','description','sku','base_price',
            'offer_price','final_price','discount_percent','stock',
            'is_low_stock','is_active','promoter_commission_rate','images','primary_image_url',

            # Parent product info 
            'product_id','product_name','product_slug',
            'product_category','product_created_at','is_new',

            # Return/replacement info
            'allow_return','return_days','allow_replacement','replacement_days','is_returnable','is_replaceable',
        ]
        extra_kwargs = {
            'variant_name': {'required': True},
            'stock': {'required': True},
            'base_price': {'required': True},
            'sku':{'required':False}
        }
    def get_final_price(self, obj):
        if obj.offer_price and obj.offer_price < obj.base_price:
            return obj.offer_price
        return obj.base_price

    def get_discount_percent(self, obj):
        if obj.offer_price and obj.base_price and obj.offer_price < obj.base_price:
            return round(((obj.base_price - obj.offer_price) / obj.base_price) * 100)
        return 0

    def get_is_low_stock(self, obj):
        return obj.stock > 0 and obj.stock < 5

    def get_primary_image_url(self, obj):
        first_image = obj.images.first()
        return first_image.url if first_image else None

    def get_is_new(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        return obj.product.created_at >= timezone.now() - timedelta(days=7)

    def validate(self, attrs):
        # Validate return days
        if attrs.get('allow_return'):
            if not attrs.get('return_days') or attrs['return_days'] <= 0:
                raise serializers.ValidationError("Return days must be greater than 0 if the product is returnable.")
        else:
            attrs['return_days'] = None  # Clear if return not allowed

        # Validate replacement days
        if attrs.get('allow_replacement'):
            if not attrs.get('replacement_days') or attrs['replacement_days'] <= 0:
                raise serializers.ValidationError("Replacement days must be greater than 0 if the product allows replacement.")
        else:
            attrs['replacement_days'] = None  # Clear if replacement not allowed

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