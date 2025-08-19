import nested_admin
from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, ProductVariantImage

from django.utils.safestring import mark_safe


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # auto-fill slug in admin
    search_fields = ('name',)

class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_url', 'alt_text')  # show both upload + url


class ProductVariantImageInline(nested_admin.NestedTabularInline):
    model = ProductVariantImage
    extra = 1
    fields = ('image', 'image_url', 'alt_text')


class ProductVariantInline(nested_admin.NestedTabularInline):
    model = ProductVariant
    extra = 1
    inlines = [ProductVariantImageInline]  # nested variant images here
    show_change_link = True

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'is_available',
        'featured',
        'created_at',
        'thumbnail',   # 👈 added here
    )
    list_filter = ('category', 'is_available', 'featured')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]

    def thumbnail(self, obj):
        # get first product image (or variant image as fallback)
        img = obj.images.first()
        if not img and obj.variants.exists():
            img = obj.variants.first().images.first()

        if img:
            url = img.image.url if img.image else img.image_url
            if url:
                return mark_safe(
                    f'<a href="{url}" target="_blank">'
                    f'<img src="{url}" width="60" height="60" '
                    f'style="object-fit:cover;border-radius:6px;"/></a>'
                )
        return "No Image"

    thumbnail.short_description = "Preview"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_name', 'sku', 'stock', 'is_active', 'promoter_commission_rate', 'additional_price')
    list_filter = ('is_active',)
    search_fields = ('variant_name', 'sku', 'product__name')
    inlines = [ProductVariantImageInline]  # optional here if you want separate variant admin page

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'thumbnail', 'alt_text')
    search_fields = ('product__name', 'alt_text', 'image_url')

    def thumbnail(self, obj):
        url = None
        if obj.image:
            url = obj.image.url
        elif obj.image_url:
            url = obj.image_url
        if url:
            return mark_safe(f'<a href="{url}" target="_blank">'
                             f'<img src="{url}" width="60" height="60" '
                             f'style="object-fit:cover;border-radius:6px;"/></a>')
        return "No Image"

    thumbnail.short_description = "Preview"


@admin.register(ProductVariantImage)
class ProductVariantImageAdmin(admin.ModelAdmin):
    list_display = ('variant', 'image', 'image_url', 'alt_text','thumbnail')
    search_fields = ('variant__variant_name', 'alt_text', 'image_url')

    def thumbnail(self, obj):
        url = None
        if obj.image:
            url = obj.image.url
        elif obj.image_url:
            url = obj.image_url
        if url:
            return mark_safe(f'<a href="{url}" target="_blank">'
                             f'<img src="{url}" width="60" height="60" '
                             f'style="object-fit:cover;border-radius:6px;"/></a>')
        return "No Image"

    thumbnail.short_description = "Preview"