from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DeliveryMan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=50, unique=True)
    
    # Optional additional fields
    address = models.TextField(blank=True, null=True)  # home or base location
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(blank=True, null=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True, null=True)  # For admin/internal use

    def __str__(self):
        return f"{self.user.email} - {self.phone}"
