from django.contrib.auth import get_user_model
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer
from rest_framework import serializers
from .models import Cart,CartItem

User=get_user_model()
# Create your models here.


class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model=Cart
        fields=['id','created_at']
        read_only_fields = ['id', 'created_at']

class CartItemSerializer(serializers.ModelSerializer):
    # --- ProductVariant fields ---
    variant_id = serializers.IntegerField(source="product_variant.id", read_only=True)
    variant_name = serializers.CharField(source="product_variant.variant_name", read_only=True)
    sku = serializers.CharField(source="product_variant.sku", read_only=True)
    base_price = serializers.DecimalField(source="product_variant.base_price", max_digits=10, decimal_places=2, read_only=True)
    offer_price = serializers.DecimalField(source="product_variant.offer_price", max_digits=10, decimal_places=2, read_only=True)
    final_price = serializers.DecimalField(source="product_variant.final_price", max_digits=10, decimal_places=2, read_only=True)
    stock = serializers.IntegerField(source="product_variant.stock", read_only=True)
    is_active = serializers.BooleanField(source="product_variant.is_active", read_only=True)
    promoter_commission_rate = serializers.DecimalField(source="product_variant.promoter_commission_rate", max_digits=5, decimal_places=2, read_only=True)

    # Variant images
    images = serializers.SerializerMethodField()

    # --- Product fields ---
    product_id = serializers.IntegerField(source="product_variant.product.id", read_only=True)
    product_name = serializers.CharField(source="product_variant.product.name", read_only=True)
    product_slug = serializers.CharField(source="product_variant.product.slug", read_only=True)
    product_category = serializers.CharField(source="product_variant.product.category.name", read_only=True)

    # --- Cart-specific ---
    price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    quantity = serializers.IntegerField()  # writable

    class Meta:
        model = CartItem
        fields = [
            'id',
            'variant_id',
            'variant_name',
            'sku',
            'base_price',
            'offer_price',
            'final_price',
            'stock',
            'is_active',
            'promoter_commission_rate',
            'images',
            'product_id',
            'product_name',
            'product_slug',
            'product_category',
            'quantity',
            'price',
            'subtotal',
            'added_at',
            'product_variant',  # writable
        ]
        read_only_fields = [
            'id', 'added_at', 'variant_id', 'variant_name',
            'sku', 'base_price', 'offer_price', 'final_price',
            'stock', 'is_active', 'promoter_commission_rate',
            'images', 'product_id', 'product_name',
            'product_slug', 'product_category',
            'price', 'subtotal'
        ]

    def get_images(self, obj):
        if obj.product_variant and obj.product_variant.images.exists():
            return [{"id": img.id, "url": img.url} for img in obj.product_variant.images.all()]
        return []

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def get_price(self, obj):
        return obj.product_variant.final_price if obj.product_variant else 0

    def get_subtotal(self, obj):
        return obj.quantity * obj.product_variant.final_price if obj.product_variant else 0

    
class CartSummarySerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'items', 'total_quantity', 'total_price']

class CartItemInputSerializer(serializers.Serializer):
    product_variant_id = serializers.IntegerField()
    quantity=serializers.IntegerField(min_value=1)