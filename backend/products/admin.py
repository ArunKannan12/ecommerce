from django.contrib import admin
from .models import Product, ProductImage, ProductVariant, Category

# Inline for Product inside CategoryAdmin
class ProductInline(admin.TabularInline):
    model = Product
    extra = 1

# Inline for ProductVariant inside ProductAdmin
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

# Inline for ProductImage inside ProductAdmin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'created_at']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant_name', 'sku', 'additional_price', 'stock', 'is_active']
    list_filter = ['is_active']
    search_fields = ['variant_name', 'sku']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text']
