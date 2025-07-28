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
        fields=['id','category','category_id','slug','description','price','is_available','created_at']
        model=Product

class ProductVariantSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    product_id=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),write_only=True)
    class Meta:
        fields=['id','product','product_id','variant_name','sku','additional_price','stock','is_active']
        model=ProductVariant

class ProductImageSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    product_id=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),write_only=True)
    class Meta:
        fields=['id','product','product_id','image','alt_text']
        model=ProductImage
