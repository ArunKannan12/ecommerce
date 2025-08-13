import nested_admin
from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, ProductVariantImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # auto-fill slug in admin
    search_fields = ('name',)

class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1

class ProductVariantImageInline(nested_admin.NestedTabularInline):
    model = ProductVariantImage
    extra = 1

class ProductVariantInline(nested_admin.NestedTabularInline):
    model = ProductVariant
    extra = 1
    inlines = [ProductVariantImageInline]  # nested variant images here
    show_change_link = True

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'featured', 'created_at')
    list_filter = ('category', 'is_available', 'featured')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_name', 'sku', 'stock', 'is_active', 'promoter_commission_rate', 'additional_price')
    list_filter = ('is_active',)
    search_fields = ('variant_name', 'sku', 'product__name')
    inlines = [ProductVariantImageInline]  # optional here if you want separate variant admin page

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'alt_text')
    search_fields = ('product__name', 'alt_text')

@admin.register(ProductVariantImage)
class ProductVariantImageAdmin(admin.ModelAdmin):
    list_display = ('variant', 'image', 'alt_text')
    search_fields = ('variant__variant_name', 'alt_text')
