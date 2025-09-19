from rest_framework import serializers
from products.models import Product, ProductVariant, Category,ProductVariantImage
from orders.models import Order, OrderItem, ReturnRequest, ReplacementRequest
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from products.serializers import CategorySerializer
import random
import string
from products.serializers import ProductVariantSerializer

User = get_user_model()

class AdminDashboardStatsSerializer(serializers.Serializer):
    # Basic metrics
    total_orders = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()
    average_order_value = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    total_customers = serializers.SerializerMethodField()
    total_deliveryman=serializers.SerializerMethodField()
    total_warehousestaff=serializers.SerializerMethodField()
    pending_orders = serializers.SerializerMethodField()
    total_returns = serializers.SerializerMethodField()
    total_replacements = serializers.SerializerMethodField()

    # Advanced metrics
    monthly_sales = serializers.SerializerMethodField()
    weekly_sales = serializers.SerializerMethodField()
    top_products = serializers.SerializerMethodField()
    low_stock_products = serializers.SerializerMethodField()
    orders_by_status = serializers.SerializerMethodField()
    orders_by_payment_method = serializers.SerializerMethodField()
    returns_rate = serializers.SerializerMethodField()
    top_customers = serializers.SerializerMethodField()
    new_customers_monthly = serializers.SerializerMethodField()
    average_delivery_time = serializers.SerializerMethodField()

    # ---------------- Basic Stats ----------------
    def get_total_orders(self, obj):
        return Order.objects.count()
    
    def get_total_sales(self, obj):
        return Order.objects.aggregate(total=Sum('total'))['total'] or 0

    def get_average_order_value(self, obj):
        total_orders = self.get_total_orders(obj)
        total_sales = self.get_total_sales(obj)
        return round(total_sales / total_orders, 2) if total_orders else 0

    def get_total_products(self, obj):
        return Product.objects.count()

    def get_total_customers(self, obj):
        return User.objects.filter(role='customer').count()
    
    def get_total_deliveryman(self,obj):
        return User.objects.filter(role='deliveryman').count()
    
    def get_total_warehousestaff(self,obj):
        return User.objects.filter(role='warehouse').count()

    def get_pending_orders(self, obj):
        return Order.objects.filter(status='pending').count()

    def get_total_returns(self, obj):
        return ReturnRequest.objects.count()

    def get_total_replacements(self, obj):
        return ReplacementRequest.objects.count()

    # ---------------- Advanced Metrics ----------------
    def get_monthly_sales(self, obj):
        sales = (
            Order.objects.filter(status='delivered')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('total'))
            .order_by('month')
        )
        return [{"month": s['month'].strftime("%b %Y"), "total": s['total']} for s in sales]

    def get_weekly_sales(self, obj):
        sales = (
            Order.objects.filter(status='delivered')
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum('total'))
            .order_by('day')
        )
        return [{"day": s['day'].strftime("%d %b"), "total": s['total']} for s in sales]

    def get_top_products(self, obj):
        top_products = (
            OrderItem.objects
            .values('product_variant__product__id', 'product_variant__product__name')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:5]
        )
        return [{"id": p['product_variant__product__id'], "name": p['product_variant__product__name'], "sold": p['total_sold']} for p in top_products]

    def get_low_stock_products(self, obj):
        return list(ProductVariant.objects.filter(stock__lte=5).values('id', 'product__name', 'stock'))

    def get_orders_by_status(self, obj):
        queryset = Order.objects.values('status').annotate(count=Count('id'))
        return {item['status']: item['count'] for item in queryset}

    def get_orders_by_payment_method(self, obj):
        queryset = Order.objects.values('payment_method').annotate(count=Count('id'))
        return {item['payment_method']: item['count'] for item in queryset}

    def get_returns_rate(self, obj):
        total_orders = self.get_total_orders(obj)
        total_returns = self.get_total_returns(obj)
        return round((total_returns / total_orders) * 100, 2) if total_orders else 0

    def get_top_customers(self, obj):
        top_customers = (
            Order.objects.values('user__id', 'user__email')
            .annotate(order_count=Count('id'), total_spent=Sum('total'))
            .order_by('-total_spent')[:5]
        )
        return [
            {
                "id": c['user__id'],
                "email": c['user__email'],
                "orders": c['order_count'],
                "spent": c['total_spent']
            }
            for c in top_customers
        ]

    def get_new_customers_monthly(self, obj):
        customers = (
            User.objects.filter(role='customer')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        return [{"month": c['month'].strftime("%b %Y"), "count": c['count']} for c in customers]

    def get_average_delivery_time(self, obj):
        delivered_orders = Order.objects.filter(status='delivered', delivered_at__isnull=False, created_at__isnull=False)
        total_seconds = sum([(o.delivered_at - o.created_at).total_seconds() for o in delivered_orders])
        count = delivered_orders.count()
        return round(total_seconds / count / 3600, 2) if count else 0  # average hours


class ProductAdminSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "category", "category_id", "name", "slug", "description",
            "is_available", "featured", "created_at",
            "image", "image_url", "variants"
        ]
        extra_kwargs = {
            "slug": {"required": False},
            "description": {"required": True},
        }

    def create(self, validated_data):
        variants_data = validated_data.pop('variants')
        category = validated_data.pop('category_id')
        product = Product.objects.create(category=category, **validated_data)

        for variant_data in variants_data:
            images_data = variant_data.pop('images', [])
            if not variant_data.get('sku'):
                variant_data['sku'] = self.generate_sku(product.name)
            variant = ProductVariant.objects.create(product=product, **variant_data)

            for image_data in images_data:
                ProductVariantImage.objects.create(variant=variant, **image_data)

        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', None)
        category = validated_data.pop('category_id', None)

        # ---------------- Update product fields ----------------
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if category:
            instance.category = category
        instance.save()

        if variants_data is not None:
            existing_variants = {v.id: v for v in instance.variants.all()}

            for variant_data in variants_data:
                images_data = variant_data.pop('images', [])
                variant_id = variant_data.get('id', None)

                # ---------------- Update existing variant ----------------
                if variant_id and variant_id in existing_variants:
                    variant = existing_variants.pop(variant_id)
                    for attr, value in variant_data.items():
                        setattr(variant, attr, value)
                    # Auto-generate SKU if missing
                    if not variant.sku:
                        variant.sku = self.generate_sku(instance.name)
                    # Validate return/replacement days
                    ProductVariantSerializer().validate(variant_data)
                    variant.save()
                else:
                    # ---------------- Create new variant ----------------
                    if not variant_data.get('sku'):
                        variant_data['sku'] = self.generate_sku(instance.name)
                    # Validate return/replacement days
                    ProductVariantSerializer().validate(variant_data)
                    variant = ProductVariant.objects.create(product=instance, **variant_data)

                # ---------------- Handle images ----------------
                if images_data:
                    variant.images.all().delete()
                    for image_data in images_data:
                        ProductVariantImage.objects.create(variant=variant, **image_data)

            # ---------------- Delete removed variants ----------------
            for variant in existing_variants.values():
                variant.delete()

            # ---------------- Ensure at least one variant remains ----------------
            if instance.variants.count() == 0:
                raise serializers.ValidationError("A product must have at least one variant.")

        return instance


    def generate_sku(self, product_name):
        import random, string
        base = ''.join(e for e in product_name if e.isalnum()).upper()[:3]
        rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{base}-{rand}"
