from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class Investor(models.Model):
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?\d{10,15}$')]
    )
    net_worth = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    profile_image = models.ImageField(upload_to='investors/', null=True, blank=True)
    address = models.TextField()
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        return self.user.is_active

    def __str__(self):
        return self.user.email


class Investment(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    invested_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)  # Set to True once payment is verified
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.investor.user.email} - ₹{self.amount} on {self.invested_at.date()}"


class ProductSaleShare(models.Model):  # ✅ Fixed typo here
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    total_sales_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    profit_generated = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    investor_share = models.DecimalField(max_digits=15, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.investor.user.email} earned ₹{self.investor_share} from sales"


class Payout(models.Model):
    CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid')
    ]
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payout_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=CHOICES, default='pending')
    sale_share = models.ForeignKey(ProductSaleShare, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.investor.user.email} - ₹{self.amount} - {self.status}"


class InvestorWallet(models.Model):
    investor = models.OneToOneField(Investor, related_name='wallet', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # ✅ Increased max_digits
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.investor.user.email} - ₹{self.balance}"
