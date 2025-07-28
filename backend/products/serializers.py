from .models import Product,ProductImage,ProductVariant,Category
from rest_framework import serializers

# Create your models here.

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields=['id','name','slug']
        model=Category

class ProductSerializer(serializers.ModelSerializer):
    category=CategorySerializer(read_only=True)
    category_id=serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(),write_only=True)

    class Meta:
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'is_available', 'category', 'category_id', 'created_at'
        ]
        model=Product
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        category = validated_data.pop('category_id')
        return Product.objects.create(category=category, **validated_data)
    
    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            instance.category = validated_data.pop('category_id')
        return super().update(instance, validated_data)

class ProductVariantSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    product_id=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),write_only=True,required=False)
    class Meta:
        fields=['id','product','product_id','variant_name','sku','additional_price','stock','is_active']
        model=ProductVariant
        

class ProductImageSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    product_id=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),write_only=True,required=False)
    class Meta:
        fields=['id','product','product_id','image','alt_text']
        model=ProductImage
