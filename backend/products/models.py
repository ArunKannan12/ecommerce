from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

# Create your models here.

class Category(models.Model):
    name=models.CharField(max_length=100,unique=True)
    image=models.ImageField( upload_to='category_images/',blank=True,null=True)
    slug=models.SlugField(unique=True)

    class Meta:
        verbose_name_plural='Categories'

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

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name=models.CharField(max_length=50)
    slug=models.SlugField(unique=True)
    description=models.TextField()
    price=models.DecimalField( max_digits=50, decimal_places=2)
    is_available=models.BooleanField(default=True)
    featured=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [
        models.Index(fields=['slug']),
        models.Index(fields=['is_available']),
        models.Index(fields=['featured']),
    ]

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug=slugify(self.name)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.name
    
    
class ProductVariant(models.Model):
    product=models.ForeignKey(Product, on_delete=models.CASCADE,related_name='variants')
    variant_name=models.CharField(max_length=50)
    promoter_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sku=models.CharField( max_length=50,unique=True)
    additional_price=models.DecimalField( max_digits=5, decimal_places=2,default=0.00)
    stock=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    
    @property 
    def final_price(self):
        return self.product.price + self.additional_price
    
    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
    
class ProductImage(models.Model):
    product=models.ForeignKey(Product, on_delete=models.CASCADE,related_name='images')
    image=models.ImageField (upload_to='product-images/')
    alt_text=models.CharField( max_length=50,blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"
    
class ProductVariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product-variant-images', null=True, blank=True)
    alt_text = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Image for {self.variant}"
