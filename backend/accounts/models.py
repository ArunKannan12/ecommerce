from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator,MinLengthValidator,MaxLengthValidator,EmailValidator
from rest_framework.exceptions import ValidationError
AUTH_PROVIDERS = [
    ('email', 'Email'),
    ('google', 'Google'),
    ('facebook', 'Facebook'),
]

email_validator = EmailValidator(
    message="Enter a valid email address"
)
phone_regex = RegexValidator(
    regex=r'^(\+91[\-\s]?|0)?[6-9]\d{9}$',
    message="Phone number must be a valid Indian number. Examples: '+919876543210', '09876543210', '9876543210'."
)
pincode_regex = RegexValidator(
    regex=r'^[1-9][0-9]{5}$',
    message="Pincode must be a valid 6-digit Indian pincode."
)
name_regex = RegexValidator(
    regex=r'^[A-Za-z\s\-]+$',
    message="This field can only contain letters, spaces, and hyphens."
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not first_name or not last_name:
            raise ValueError('Users must have a first and last name')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, first_name, last_name, password, **extra_fields)
    

def user_profile_upload_path(instance, filename):
    return f'profile_pics/{instance.email}/{filename}'

ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('promoter', 'Promoter'),
        ('admin', 'Admin'),
        ('deliveryman','Delivery Man'),
        ('warehouse','Warehouse Staff'),
        ('investor','Investor'),
    ] 

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True,validators=[email_validator])
    first_name = models.CharField(max_length=30,validators=[name_regex])
    last_name = models.CharField(max_length=30,validators=[name_regex])

    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    social_auth_pro_pic=models.URLField(blank=True,null=True)
    custom_user_profile = models.URLField(max_length=500, blank=True, null=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True,validators=[phone_regex])
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True,validators=[pincode_regex])
    district = models.CharField(max_length=100, blank=True, null=True,validators=[name_regex])
    city = models.CharField(max_length=100, blank=True, null=True,validators=[name_regex])
    state = models.CharField(max_length=100, blank=True, null=True,validators=[name_regex])
    
    last_activation_email_sent = models.DateTimeField(null=True, blank=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    block_count = models.PositiveIntegerField(default=0)  # to count temporary blocks
    is_permanently_banned = models.BooleanField(default=False)
    
    last_password_reset_sent = models.DateTimeField(null=True, blank=True)
    blocked_until_password_reset = models.DateTimeField(null=True, blank=True)
    block_count_password_reset = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)


    auth_provider=models.CharField( max_length=50,default='email' ,choices=AUTH_PROVIDERS)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name
    
    def clean(self):
        super().clean()
        if self.phone_number and len(self.phone_number) != 10:
            raise ValidationError("Phone number must be 10 digits")
        if not self.email:
            raise ValidationError("Email is required")

    
# models.py
class ActivationEmailLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "sent_at"]),
        ]




class PasswordResetEmailLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_logs')
    sent_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Password reset email sent to {self.user.email} at {self.sent_at}"