from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError
import cloudinary.uploader
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)  # Optional manual URL
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{get_random_string(4)}"
            self.slug = slug
        if self.image and not self.image_url:
            self.image_url = self.image.url
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # MAIN product image
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_available']),
            models.Index(fields=['featured']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{get_random_string(4)}"
            self.slug = slug

        # Cloudinary upload for product main image
        super().save(*args, **kwargs)
        if self.image and (not self.image_url or 'res.cloudinary.com' not in self.image_url):
            try:
                upload_result = cloudinary.uploader.upload(
                    self.image.path,
                    folder='ecommerce/product_main'
                )
                self.image_url = upload_result['secure_url']
                self.image.delete(save=False)
                super().save(update_fields=['image_url'])
            except Exception as e:
                print(f"Cloudinary upload failed: {e}")

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=50)
    description=models.TextField(blank=True,help_text="Optional description for this specific variant")
    promoter_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Returnable
    allow_return = models.BooleanField(default=False)
    return_days = models.PositiveIntegerField(null=True, blank=True)

    # Replacement-only
    allow_replacement = models.BooleanField(default=False)
    replacement_days = models.PositiveIntegerField( null=True, blank=True)

    def clean(self):
        errors = {}

        # ✅ Base price validation
        if self.base_price is None:
            errors['base_price'] = "Base price must be set."

        # ✅ Offer price check
        if self.offer_price and self.base_price and self.offer_price > self.base_price:
            errors['offer_price'] = "Offer price cannot exceed base price."
        if errors:
            raise ValidationError(errors)


    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures clean() runs in admin/API
        super().save(*args, **kwargs)

    @property
    def final_price(self):
        return self.offer_price if self.offer_price else self.base_price

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"


class BaseImage(models.Model):
    """Abstract base model for images (variant images only now)"""
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    alt_text = models.CharField(max_length=50, blank=True)

    class Meta:
        abstract = True

    @property
    def url(self):
        return self.image_url or (self.image.url if self.image else None)

    def clean(self):
        if not self.image and not self.image_url:
            raise ValidationError("Either upload an image or provide an image URL.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and (not self.image_url or 'res.cloudinary.com' not in self.image_url):
            try:
                upload_result = cloudinary.uploader.upload(
                    self.image.path,
                    folder='ecommerce/variant_images'
                )
                self.image_url = upload_result['secure_url']
                self.image.delete(save=False)
                super().save(update_fields=['image_url'])
            except Exception as e:
                print(f"Cloudinary upload failed: {e}")


class ProductVariantImage(BaseImage):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"Image for {self.variant}"


class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Optional title for the banner")
    subtitle = models.CharField(max_length=255, blank=True, null=True, help_text="Optional subtitle or tagline")
    image = models.ImageField(upload_to="banners/", help_text="Banner image")
    link_url = models.URLField(blank=True, null=True, help_text="Optional link when clicking banner")
    order = models.PositiveIntegerField(default=0, help_text="Sorting order for carousel")
    is_active = models.BooleanField(default=True, help_text="Show this banner in carousel?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")

    def __str__(self):
        return self.title or f"Banner {self.id}"