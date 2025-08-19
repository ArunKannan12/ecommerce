from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)  # Optional manual URL
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        # Generate slug if not exists
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{get_random_string(4)}"
            self.slug = slug

        # If image uploaded, override image_url with image file URL
        if self.image:
            self.image_url = self.image.url

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=50, decimal_places=2)
    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

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
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=50)
    promoter_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sku = models.CharField(max_length=50, unique=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    @property
    def final_price(self):
        return self.product.price + self.additional_price

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"


class BaseImage(models.Model):
    """Abstract base model for Product and Variant images"""
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    alt_text = models.CharField(max_length=50, blank=True)

    class Meta:
        abstract = True

    @property
    def url(self):
        return self.image.url if self.image else self.image_url

    def clean(self):
        if not self.image and not self.image_url:
            raise ValidationError("Either upload an image or provide an image URL.")


class ProductImage(BaseImage):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariantImage(BaseImage):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"Image for {self.variant}"


@receiver(post_save, sender=Product)
def ensure_default_variant(sender, instance, created, **kwargs):
    """Automatically create a default variant if none exist"""
    if created and not instance.variants.exists():
        ProductVariant.objects.create(
            product=instance,
            variant_name="Default",
            sku=f"SKU-{instance.id}-DEF-{get_random_string(4)}",  # ✅ ensure uniqueness
            stock=0,
            additional_price=0
        )
