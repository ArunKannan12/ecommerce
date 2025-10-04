from delivery.models import DeliveryMan
from django.db.models import Avg, Count, Q, F, ExpressionWrapper, DurationField
from rest_framework import serializers
from products.models import Product, ProductVariant, Category,ProductVariantImage
from orders.models import Order, OrderItem, ReturnRequest, ReplacementRequest
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count,Max
from django.db.models.functions import TruncMonth, TruncDay
from products.serializers import CategorySerializer,ProductVariantSerializer
from django.db import transaction
from orders.serializers import ShippingAddressSerializer
import random
import string
from .models import WarehouseLog
from products.serializers import ProductVariantImageSerializer
import logging
logger = logging.getLogger('admin_dashboard')
logger.debug("🚨 Logging test: This should appear in your terminal")

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


class ProductVariantAdminSerializer(serializers.ModelSerializer):
    images = ProductVariantImageSerializer(many=True, required=False)
    primary_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id", "variant_name", "base_price", "offer_price", "stock",
            "sku", "description", "images", "primary_image_url"
        ]
        extra_kwargs = {
            "variant_name": {"required": True},
            "base_price": {"required": True},
            "stock": {"required": True},
            "sku": {"required": False},
            "description": {"required": False},
        }

    def get_primary_image_url(self, obj):
        first_image = obj.images.first()
        return first_image.url if first_image else None

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        product = self.context['product']

        # Auto-generate SKU if missing
        if not validated_data.get("sku"):
            validated_data["sku"] = self.generate_sku(product.name)

        variant = ProductVariant.objects.create(product=product, **validated_data)

        for img_data in images_data:
            ProductVariantImage.objects.create(variant=variant, **img_data)

        return variant

    def generate_sku(self, product_name):
        base = "".join(e for e in product_name if e.isalnum()).upper()[:3]
        rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{base}-{rand}"
    
    def update(self, instance, validated_data):
        logger.debug(f"🛠️ ProductAdminSerializer.update called for product {instance.id}")
        images_data = validated_data.pop("images", [])
        remove_images = validated_data.pop("remove_images", [])

        # 🔥 Delete marked images FIRST
        if remove_images:
            logger.debug(f"🧹 Attempting to delete images from variant {instance.id}: {remove_images}")
            deleted_count, _ = instance.images.filter(id__in=remove_images).delete()
            logger.debug(f"✅ Deleted {deleted_count} image(s)")

        # Update basic fields
        for attr, value in validated_data.items():
            logger.debug(f"✏️ Updating field '{attr}' to '{value}'")
            setattr(instance, attr, value)
        instance.save()

        # Reconcile remaining images
        existing_images = {img.id: img for img in instance.images.all()}
        logger.debug(f"📸 Existing images after deletion: {list(existing_images.keys())}")

        incoming_ids = [img.get("id") for img in images_data if img.get("id")]
        logger.debug(f"📥 Incoming image IDs: {incoming_ids}")

        # Delete images not included in incoming list
        if images_data:
            for img_id in set(existing_images) - set(incoming_ids):
                logger.debug(f"🗑️ Removing image not in incoming list: {img_id}")
                existing_images[img_id].delete()

        # Update existing or add new
        for img_data in images_data:
            img_id = img_data.get("id")
            if img_id and img_id in existing_images:
                logger.debug(f"🔄 Updating existing image {img_id}")
                img_instance = existing_images[img_id]
                for k, v in img_data.items():
                    if k != "id":
                        logger.debug(f"   ↪️ Setting '{k}' to '{v}'")
                        setattr(img_instance, k, v)
                img_instance.save()
            elif img_data.get("image"):
                logger.debug(f"➕ Adding new image to variant {instance.id}")
                ProductVariantImage.objects.create(variant=instance, **img_data)

        return instance

    
class ProductAdminSerializer(serializers.ModelSerializer):
    variants = ProductVariantAdminSerializer(many=True, required=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, required=True
    )
    category = CategorySerializer(read_only=True)
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "is_available", "featured",
            "created_at", "image", "image_url", "category", "category_id", "variants"
        ]
        extra_kwargs = {
            "name": {"required": True},
            "description": {"required": True},
            "slug": {"required": False},
        }

    def validate(self, attrs):
        variant_names = [v["variant_name"] for v in attrs.get("variants", [])]
        if len(variant_names) != len(set(variant_names)):
            raise serializers.ValidationError("Duplicate variant names are not allowed.")
        return attrs

    def generate_sku(self, product_name):
        base = "".join(e for e in product_name if e.isalnum()).upper()[:3]
        rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{base}-{rand}"

    @transaction.atomic
    def create(self, validated_data):
        variants_data = validated_data.pop("variants")
        category = validated_data.pop("category_id")
        product = Product.objects.create(category=category, **validated_data)

        for variant_data in variants_data:
            variant_data["description"] = variant_data.get("description") or product.description
            variant_data["sku"] = variant_data.get("sku") or self.generate_sku(product.name)
            serializer = ProductVariantAdminSerializer(
                data=variant_data, context={"product": product}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        variants_data = validated_data.pop("variants", None)
        category = validated_data.pop("category_id", None)

        # Handle main product image removal
        if request and request.data.get("remove_image"):
            if instance.image:
                instance.image.delete(save=False)
            instance.image = None
            instance.image_url = None

        # Update main product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if category:
            instance.category = category
        instance.save()

        if variants_data is not None:
            existing_variants = {v.id: v for v in instance.variants.all()}

            for variant_data in variants_data:
                variant_id = variant_data.get("id")
                # Extract remove_images for this variant
                remove_images = variant_data.pop("remove_images", [])

                if variant_id and variant_id in existing_variants:
                    variant_instance = existing_variants.pop(variant_id)
                    serializer = ProductVariantAdminSerializer(
                        variant_instance,
                        data=variant_data,
                        context={"product": instance}
                    )
                    serializer.is_valid(raise_exception=True)
                    variant = serializer.save()

                    # Delete images marked for removal
                    if remove_images:
                        variant.images.filter(id__in=remove_images).delete()

                else:
                    serializer = ProductVariantAdminSerializer(
                        data=variant_data,
                        context={"product": instance}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

            # Delete any variants that were removed entirely
            for remaining_variant in existing_variants.values():
                remaining_variant.delete()

            # Ensure at least one variant exists
            if instance.variants.count() == 0:
                raise serializers.ValidationError("A product must have at least one variant.")

        return instance

class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    auth_provider_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p")
    updated_at = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p")
    last_activation_email_sent = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p", required=False)
    last_password_reset_sent = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p", required=False)
    blocked_until = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p", required=False)
    blocked_until_password_reset = serializers.DateTimeField(format="%d-%b-%Y %I:%M %p", required=False)

    # --- New fields for admin panel ---
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'address', 'pincode', 'district', 'city', 'state',
            'is_active', 'is_verified', 'role', 'auth_provider', 'auth_provider_display',
            'created_at', 'updated_at',
            'social_auth_pro_pic', 'custom_user_profile', 'profile_picture_url',
            'last_activation_email_sent', 'last_password_reset_sent',
            'blocked_until', 'block_count', 'is_permanently_banned',
            'blocked_until_password_reset', 'block_count_password_reset',
            'last_login_ip',
            'total_orders', 'total_spent', 'last_order_date',  # new fields
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

    def get_profile_picture_url(self, obj):
        return obj.custom_user_profile if obj.custom_user_profile else obj.social_auth_pro_pic

    def get_auth_provider_display(self, obj):
        return obj.get_auth_provider_display()

    def get_total_orders(self, obj):
        return Order.objects.filter(user=obj).count()

    def get_total_spent(self, obj):
        total = Order.objects.filter(user=obj, status='delivered').aggregate(Sum('total'))['total__sum']
        return total or 0

    def get_last_order_date(self, obj):
        last_order = Order.objects.filter(user=obj, status='delivered').aggregate(Max('created_at'))['created_at__max']
        return last_order.strftime("%d-%b-%Y %I:%M %p") if last_order else None


class AdminOrderItemSerializer(serializers.ModelSerializer):
    # Read-only nested product info
    product_variant = ProductVariantSerializer(read_only=True)
    
    # Write-only IDs for creation/updating
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), write_only=True, source='order'
    )
    product_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), write_only=True, source='product_variant'
    )

    # Read-only timestamps
    packed_at = serializers.DateTimeField(read_only=True)
    shipped_at = serializers.DateTimeField(read_only=True)
    delivered_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order_id',
            'product_variant',
            'product_variant_id',
            'quantity',
            'price',
            'status',
            'packed_at',
            'shipped_at',
            'delivered_at'
        ]

    def validate_quantity(self, value):
        product_variant=self.initial_data.get('product_variant_id')
        if product_variant:
            variant=ProductVariant.objects.get(id=product_variant)
            if value > variant.stock:
                raise serializers.ValidationError("Quantity exceeds available stock")
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value 


class AdminOrderSerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSerializer(read_only=True)
    items = AdminOrderItemSerializer(many=True, source='orderitem_set', read_only=True)
    user = serializers.StringRelatedField(read_only=True)  # show customer name/email

    class Meta:
        model = Order
        fields = [
            'id','order_number','user', 'shipping_address', 'status', 'subtotal', 'delivery_charge', 'total',
            'payment_method', 'is_paid', 'is_refunded', 'tracking_number',
            'shipped_at', 'delivered_at', 'paid_at', 'created_at', 'updated_at',
            'promoter', 'cancel_reason', 'cancelled_at', 'cancelled_by', 'cancelled_by_role',
            'razorpay_order_id', 'razorpay_payment_id', 'refund_id', 'refund_status',
            'refunded_at', 'is_restocked', 'items'
        ]
        read_only_fields = fields  # Admin list is mostly read-only

class WarehouseLogSerializer(serializers.ModelSerializer):
    order_item = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    formatted_timestamp=serializers.SerializerMethodField()

    
    class Meta:
        model = WarehouseLog
        fields = [
            'id', 'order_item', 'order','formatted_timestamp',
            'action', 'updated_by', 'comment', 'timestamp', 'action_display'
        ]
        read_only_fields = ['id', 'timestamp', 'updated_by']

    def get_action_display(self, obj):
        return obj.get_action_display()

    def get_order_item(self, obj):
        product_variant = getattr(obj.order_item, 'product_variant', None)
        product = getattr(product_variant, 'product', None)
        
        # Attempt to find an image URL from multiple fallback options
        product_image = (
            getattr(product_variant, 'image_url', None) or
            getattr(getattr(product_variant, 'images', None), 'url', None) or
            getattr(product, 'image_url', None) or
            getattr(getattr(product, 'image', None), 'url', None) or
            ''
        )

        return {
            "id": obj.order_item.id,
            "product": getattr(product, 'name', ''),
            "variant": getattr(product_variant, 'variant_name', ''),
            "quantity": obj.order_item.quantity,
            "product_image": product_image,
            "status": obj.order_item.status
        }

    def get_order(self, obj):
        if obj.order:
            return {
                'id': obj.order.id,
                'order_number': obj.order.order_number,
                'status': obj.order.status,
                'total': obj.order.total
            }
        return None

    def get_updated_by(self, obj):
        user = obj.updated_by
        if user:
            return {
                'id': user.id,
                'name': user.get_full_name() or user.get_short_name() or user.username,
                'email': user.email
            }
        return None
    def get_formatted_timestamp(self, obj):
        return obj.timestamp.strftime('%d %b %Y, %I:%M %p')



class WarehouseTimeLineSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    picked_at = serializers.DateTimeField(allow_null=True)
    packed_at = serializers.DateTimeField(allow_null=True)
    shipped_at = serializers.DateTimeField(allow_null=True)
    out_for_delivery_at = serializers.DateTimeField(allow_null=True)
    delivered_at = serializers.DateTimeField(allow_null=True)

    current_status=serializers.SerializerMethodField()
    time_to_pack=serializers.SerializerMethodField()
    time_to_ship=serializers.SerializerMethodField()
    time_to_delivery=serializers.SerializerMethodField()
    products=serializers.SerializerMethodField()

    def get_current_status(self, obj):
        for field in ['delivered_at', 'out_for_delivery_at', 'shipped_at', 'packed_at', 'picked_at']:
            if obj.get(field):
                return field.replace('_at', '')
        return 'pending'

    def get_time_to_pack(self, obj):
        if obj.get('picked_at') and obj.get('packed_at'):
            return str(obj['packed_at'] - obj['picked_at'])
        return None

    def get_time_to_ship(self, obj):
        if obj.get('packed_at') and obj.get('shipped_at'):
            return str(obj['shipped_at'] - obj['packed_at'])
        return None

    def get_time_to_delivery(self, obj):
        if obj.get('shipped_at') and obj.get('delivered_at'):
            return str(obj['delivered_at'] - obj['shipped_at'])
        return None

    def get_products(self, obj):
        order_number = obj.get('order_number') or getattr(obj, 'order_number', None)
        order = Order.objects.filter(order_number=order_number).prefetch_related(
            'orderitem_set__product_variant__product'
        ).first()

        if not order:
            return []

        products = []
        for item in order.orderitem_set.all():
            variant = getattr(item, 'product_variant', None)
            product = getattr(variant, 'product', None) if variant else None
            if not product or not variant:
                continue

            image_url = getattr(product, 'image_url', None)
            products.append({
                "variant_name": variant.variant_name,
                "product_name": product.name,
                "product_image": image_url if image_url else ''
            })
        return products



class DeliveryTrackingSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_name = serializers.SerializerMethodField()
    deliveryman_name = serializers.SerializerMethodField()
    deliveryman_phone = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)  # Adjust if nested differently
    product_variant_name = serializers.CharField(source='product_variant.name', read_only=True)
    quantity=serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order_number',
            'customer_name',
            'deliveryman_name',
            'deliveryman_phone',
            'product_name',
            'product_variant_name',
            'quantity',
            'status',
            'packed_at',
            'shipped_at',
            'out_for_delivery_at',
            'delivered_at',
        ]

    def get_customer_name(self, obj):
        return obj.order.user.get_full_name()

    def get_deliveryman_name(self, obj):
        if obj.order.delivered_by:
            return obj.order.delivered_by.user.get_full_name()
        return None

    def get_deliveryman_phone(self, obj):
        if obj.order.delivered_by:
            return obj.order.delivered_by.phone
        return None



class DeliveryManStatsSerializer(serializers.ModelSerializer):
    total_deliveries = serializers.IntegerField(read_only=True)
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_delivery_time = serializers.SerializerMethodField()
    failed_deliveries = serializers.SerializerMethodField()
    full_name=serializers.SerializerMethodField()
    email=serializers.SerializerMethodField()
    class Meta:
        model = DeliveryMan
        fields = [
            'id',
            'user',
            "full_name",
            "email",
            'phone',
            'total_deliveries',
            'total_earnings',
            'average_delivery_time',
            'failed_deliveries',
        ]
    def get_full_name(self,obj):
        return obj.user.get_full_name()
    
    def get_email(self,obj):
        return obj.user.email
    
    def get_average_delivery_time(self, obj):
        qs = OrderItem.objects.filter(
            order__delivered_by=obj,
            delivered_at__isnull=False,
            packed_at__isnull=False
        ).annotate(
            delivery_duration=ExpressionWrapper(
                F('delivered_at') - F('packed_at'),
                output_field=DurationField()
            )
        )
        avg_duration = qs.aggregate(avg_time=Avg('delivery_duration'))['avg_time']
        return avg_duration.total_seconds()/3600 if avg_duration else None  # returns hours

    def get_failed_deliveries(self, obj):
        return OrderItem.objects.filter(
            order__delivered_by=obj,
            status='failed'
        ).count()
