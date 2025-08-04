from django.db import models

# Create your models here.

class Category(models.Model):
    name=models.CharField(max_length=100,unique=True)
    slug=models.SlugField(unique=True)
    class Meta:
        verbose_name_plural='Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name=models.CharField(max_length=50)
    slug=models.SlugField(unique=True)
    description=models.TextField()
    price=models.DecimalField( max_digits=50, decimal_places=2)
    is_available=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
    
class ProductImage(models.Model):
    product=models.ForeignKey(Product, on_delete=models.CASCADE,related_name='Images')
    image=models.ImageField (upload_to='product-images/')
    alt_text=models.CharField( max_length=50,blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"