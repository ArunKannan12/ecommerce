from django.db import models
from django.contrib.auth import get_user_model
import uuid
import random
import string
# Create your models here.

User=get_user_model()

def generate_random_code():
    return ''.join(random.choices(string.ascii_uppercase+string.digits,k=10))

class Promoter(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user=models.OneToOneField(User, on_delete=models.CASCADE)
    referral_code=models.CharField(unique=True,editable=False,default=generate_random_code)
    phone_number=models.CharField( max_length=50)
    bank_account_number=models.CharField( max_length=50)
    ifsc_code=models.CharField( max_length=50)
    bank_name=models.CharField( max_length=50)
    account_holder_name=models.CharField( max_length=50)

    deposit_amount=models.DecimalField( max_digits=5, decimal_places=2)
    application_status=models.CharField(choices=STATUS_CHOICES, max_length=50,default='pending')
    submitted_at=models.DateTimeField(auto_now_add=True)
    approved_at=models.DateTimeField(auto_now_add=True)

    total_sales_count=models.PositiveIntegerField(default=0)
    total_commission_earned=models.DecimalField( max_digits=10, decimal_places=2,default=0)
    wallet_balance=models.DecimalField( max_digits=10, decimal_places=2,default=0)
    is_eligible_for_withdrawal=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.application_status}"
