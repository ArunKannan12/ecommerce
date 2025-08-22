from rest_framework import serializers
from .models import Product, ProductVariant, Category, ProductVariantImage


# -------------------- CATEGORY --------------------
class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return obj.image_url


# -------------------- VARIANT IMAGES --------------------
class ProductVariantImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantImage
        fields = ['id', 'variant', 'image', 'image_url', 'alt_text', 'url']
        extra_kwargs = {
            "image": {"write_only": True, "required": False},
            "image_url": {"write_only": True, "required": False},
        }

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.url:
            return request.build_absolute_uri(obj.url) if request else obj.url
        return None


# -------------------- VARIANTS --------------------
class ProductVariantSerializer(serializers.ModelSerializer):
    images = ProductVariantImageSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_description = serializers.CharField(source='product.description', read_only=True)
    product_base_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_images = serializers.SerializerMethodField()

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product_id',
            'variant_name',
            'sku',
            'additional_price',
            'stock',
            'is_active',
            'images',
            'price',
            'product_name',
            'product_description',
            'product_base_price',
            'product_images',
        ]

    def get_price(self, obj):
        return obj.final_price

    def get_product_images(self, obj):
        request = self.context.get('request')
        urls = []
        if obj.product.image:
            urls.append(request.build_absolute_uri(obj.product.image.url) if request else obj.product.image.url)
        elif obj.product.image_url:
            urls.append(obj.product.image_url)
        return urls


# -------------------- PRODUCTS --------------------
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    variants = ProductVariantSerializer(many=True, read_only=True)  # still read-only

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'is_available', 'category', 'category_id',
            'image', 'image_url', 'variants', 'created_at', 'featured'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """
        Ensure that at least one variant exists when creating or updating a product.
        """
        # For create, product instance does not exist yet, so skip check
        if self.instance:
            if self.instance.variants.count() == 0:
                raise serializers.ValidationError(
                    "You must have at least one product variant."
                )
        return attrs

    def create(self, validated_data):
        category = validated_data.pop('category_id')
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            instance.category = validated_data.pop('category_id')
        return super().update(instance, validated_data)
