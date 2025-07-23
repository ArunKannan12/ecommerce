from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser,PasswordResetEmailLog,ActivationEmailLog


class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = (
        'email', 'first_name', 'last_name', 'phone_number', 'city', 'is_staff', 'is_active', 
        'is_verified', 'blocked_until', 'block_count', 'is_permanently_banned', 'auth_provider'
    )

    list_filter = ('is_active', 'is_staff', 'is_superuser', 'auth_provider', 'is_verified')

    readonly_fields = ('last_login', 'created_at', 'updated_at', 'blocked_until', 'block_count', 'is_permanently_banned')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'address',
                'pincode', 'district', 'city', 'state',
                'custom_user_profile', 'social_auth_pro_pic'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Security', {
            'fields': (
                'last_activation_email_sent', 'blocked_until', 'block_count', 'is_permanently_banned',
                'last_password_reset_sent', 'blocked_until_password_reset', 'block_count_password_reset'
            )
        }),
        ('Authentication Provider', {'fields': ('auth_provider',)}),
)


    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'is_verified')}
         ),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(ActivationEmailLog)
class ActivationEmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sent_at', 'ip_address', 'user_agent')
    search_fields = ('user__email', 'ip_address')
    list_filter = ('sent_at',)


@admin.register(PasswordResetEmailLog)
class PasswordResetEmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sent_at', 'ip_address', 'user_agent')
    search_fields = ('user__email', 'ip_address')
    list_filter = ('sent_at',)

admin.site.register(CustomUser, CustomUserAdmin)