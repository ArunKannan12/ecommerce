from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant, Category, ProductVariantImage


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        # Return uploaded image URL if exists
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        # Fallback to manual URL if uploaded image doesn't exist
        return getattr(obj, 'image_url', None)


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )

    class Meta:
        model = ProductImage
        fields = ['id', 'product_id', 'image', 'image_url', 'alt_text', 'url']
        extra_kwargs = {
            "image": {"write_only": True, "required": False},
            "image_url": {"write_only": True, "required": False},
        }

    def validate(self, attrs):
        """Ensure at least one of image or image_url is provided."""
        if not attrs.get("image") and not attrs.get("image_url"):
            raise serializers.ValidationError(
                "Either an uploaded image or an external image_url must be provided."
            )
        return attrs

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.url and request:
            return request.build_absolute_uri(obj.url)
        return obj.url

    def create(self, validated_data):
        product = validated_data.pop('product_id')
        return ProductImage.objects.create(product=product, **validated_data)

    def update(self, instance, validated_data):
        if 'product_id' in validated_data:
            instance.product = validated_data.pop('product_id')
        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'is_available', 'category', 'category_id',
            'images', 'variants', 'created_at', 'featured'
        ]
        read_only_fields = ['id', 'created_at']

    def get_images(self, obj):
        return ProductImageSerializer(obj.images.all(), many=True, context=self.context).data

    def get_variants(self, obj):
        return ProductVariantSerializer(obj.variants.all(), many=True, context=self.context).data

    def create(self, validated_data):
        category = validated_data.pop('category_id')
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            instance.category = validated_data.pop('category_id')
        return super().update(instance, validated_data)


class ProductVariantImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantImage
        fields = ['id', 'variant', 'image', 'image_url', 'alt_text', 'url']
        extra_kwargs = {
            "image": {"write_only": True, "required": False},
            "image_url": {"write_only": True, "required": False},
        }

    def validate(self, attrs):
        """Ensure at least one of image or image_url is provided."""
        if not attrs.get("image") and not attrs.get("image_url"):
            raise serializers.ValidationError(
                "Either an uploaded image or an external image_url must be provided."
            )
        return attrs

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.url and request:
            return request.build_absolute_uri(obj.url)
        return obj.url




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
            'product_id',          # ✅ keep only product_id for write
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
        images = []
        for img in obj.product.images.all():
            if img.image:  # uploaded
                url = request.build_absolute_uri(img.image.url) if request else img.image.url
            elif img.image_url:  # external
                url = img.image_url
            else:
                url = None
            if url:
                images.append(url)
        return images

    def create(self, validated_data):
        product = validated_data.pop('product_id')
        return ProductVariant.objects.create(product=product, **validated_data)

    def update(self, instance, validated_data):
        if 'product_id' in validated_data:
            instance.product = validated_data.pop('product_id')
        return super().update(instance, validated_data)
