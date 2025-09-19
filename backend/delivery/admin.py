from django.contrib import admin
from .models import DeliveryMan, DeliveryManRequest
from datetime import timezone

@admin.register(DeliveryMan)
class DeliveryManAdmin(admin.ModelAdmin):
    list_display = [
        'id','user', 'phone', 'address', 'vehicle_number', 
        'joined_at', 'last_active', 'total_deliveries', 'earnings'
    ]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone', 'vehicle_number']
    list_filter = ['joined_at', 'last_active']
    readonly_fields = ['joined_at', 'last_active', 'total_deliveries', 'earnings']
    ordering = ['-joined_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'phone', 'address', 'vehicle_number', 'notes')
        }),
        ('Stats', {
            'fields': ('joined_at', 'last_active', 'total_deliveries', 'earnings')
        }),
    )

@admin.register(DeliveryManRequest)
class DeliveryManRequestAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'status', 'applied_at', 'reviewed_at', 'notes']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    list_filter = ['status', 'applied_at', 'reviewed_at']
    readonly_fields = ['applied_at', 'reviewed_at', 'user']
    ordering = ['-applied_at']

    def save_model(self, request, obj, form, change):
        """
        Automatically set the reviewer (admin) and reviewed_at timestamp
        when status is changed from pending to approved/rejected.
        """
        if change:
            if 'status' in form.changed_data:
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
