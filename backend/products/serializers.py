from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant, Category,ProductVariantImage


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

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
            'images', 'variants', 'created_at','featured'
        ]
        read_only_fields = ['id', 'created_at']

    def get_images(self, obj):
        return ProductImageSerializer(obj.images.all(), many=True).data

    def get_variants(self, obj):
        return ProductVariantSerializer(obj.variants.all(), many=True).data

    def create(self, validated_data):
        category = validated_data.pop('category_id')
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            instance.category = validated_data.pop('category_id')
        return super().update(instance, validated_data)





class ProductImageSerializer(serializers.ModelSerializer):
   
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )

    class Meta:
        model = ProductImage
        fields = ['id', 'product_id', 'image', 'alt_text']

    
    def create(self, validated_data):
        product = validated_data.pop('product_id')
        return ProductImage.objects.create(product=product, **validated_data)

    def update(self, instance, validated_data):
        if 'product_id' in validated_data:
            instance.product = validated_data.pop('product_id')
        return super().update(instance, validated_data)


class ProductVariantImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariantImage
        fields = ['id', 'variant', 'image_url', 'alt_text']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None



class ProductVariantSerializer(serializers.ModelSerializer):
    images = ProductVariantImageSerializer(many=True, read_only=True)  # assuming related_name='images' on variant FK
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
            'product',          # Optional: include if you want full nested product object
            'product_id',       # Used for creation/update
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
        return [img.image.url for img in obj.product.images.all()]


    def create(self, validated_data):
        product = validated_data.pop('product_id')
        return ProductVariant.objects.create(product=product, **validated_data)

    def update(self, instance, validated_data):
        if 'product_id' in validated_data:
            instance.product = validated_data.pop('product_id')
        return super().update(instance, validated_data)