# delivery/admin.py
from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress, ReturnRequest

# -------------------- INLINE --------------------
class OrderItemInline(admin.TabularInline):
    """Show OrderItems inside the Order admin page"""
    model = OrderItem
    extra = 0
    readonly_fields = ("product_variant", "quantity", "price")
    can_delete = False

# -------------------- ORDER --------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "status", "total", "delivery_charge",
        "payment_method", "is_paid", "paid_at", "created_at"
    )
    list_filter = ("status", "is_paid", "payment_method", "created_at")
    search_fields = ("user__email", "tracking_number", "id")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "updated_at", "paid_at")
    ordering = ("-created_at",)

# -------------------- ORDER ITEM --------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_variant", "quantity", "price", "status")
    list_filter = ("status",)
    search_fields = ("order__id", "product_variant__product__name")
    readonly_fields = ()

# -------------------- SHIPPING ADDRESS --------------------
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "city", "country", "phone_number")
    list_filter = ("country", "city")
    search_fields = ("user__email", "full_name", "city", "country")

# -------------------- RETURN REQUEST --------------------
@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "order_item", "user", "status", "refund_amount", "refund_method", "user_upi",
        "pickup_status", "warehouse_decision", "admin_decision", "created_at", "updated_at"
    )
    list_filter = ("status", "refund_method", "pickup_status", "warehouse_decision", "admin_decision", "created_at")
    search_fields = ("order__id", "order_item__product_variant__variant_name", "user__email", "user_upi")
    readonly_fields = ("created_at", "updated_at", "refunded_at")
    ordering = ("-created_at",)
