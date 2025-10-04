from django.db import models
from orders.models import OrderItem,Order
from django.contrib.auth import get_user_model

User=get_user_model()

# Create your models here.
class WarehouseLog(models.Model):
    ACTION_CHOICES = [
        ('picked', 'Picked'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery','Out for Delivery'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('delivered', 'Delivered'),
    ]

    order_item = models.ForeignKey(
        OrderItem, 
        on_delete=models.CASCADE, 
        related_name='warehouse_logs'  # logs per OrderItem
    )
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='warehouse_order_logs'  # logs per Order
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='warehouse_action_logs'  # logs per user
    )
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']  # newest logs first
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['order_item']),
            models.Index(fields=['order']),
            models.Index(fields=['updated_by']),
        ]

    def __str__(self):
        return f"{self.order_item} - {self.action} by {self.updated_by} at {self.timestamp}"