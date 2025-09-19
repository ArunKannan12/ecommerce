#accounts app

from djoser.serializers import PasswordResetConfirmSerializer,SetPasswordSerializer
from .models import CustomUser
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from accounts.email import CustomPasswordResetEmail
from rest_framework.views import APIView
from rest_framework.response import Response
from investor.serializers import InvestorSerializer
from delivery.serializers import DeliveryManSerializer
from promoter.serializers import PromoterSerializer

User=get_user_model()

class BaseUserSerializer(serializers.ModelSerializer):
    profile_image=serializers.ImageField(source='custom_user_profile',read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'is_verified', 'role',
            'profile_image',
            'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'created_at','profile_image']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        profile_pic = validated_data.pop('custom_user_profile', None)
        delete_pic_flag = str(request.data.get('delete_profile_pic', '')).lower() == 'true'

        # Handle profile picture deletion
        if delete_pic_flag and getattr(instance, 'custom_user_profile', None):
            instance.custom_user_profile.delete(save=False)
            instance.custom_user_profile = None
        elif profile_pic:
            if getattr(instance, 'auth_provider', 'email').lower() != 'email':
                raise serializers.ValidationError(
                    "Profile picture can only be updated by users who signed up with email."
                )
            instance.custom_user_profile = profile_pic

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class CustomerProfileSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'phone_number', 'address', 'pincode', 
            'district', 'city', 'state','social_auth_pro_pic'
        ]

class DeliveryManProfileSerializer(BaseUserSerializer):
    delivery_profile = DeliveryManSerializer(source='deliveryman', read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['delivery_profile']

class InvestorProfileSerializer(BaseUserSerializer):
    investor_profile = InvestorSerializer(source='investor', read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['investor_profile']


class PromoterProfileSerializer(BaseUserSerializer):
    promoter_profile = PromoterSerializer(source='promoter', read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ['promoter_profile']


class RoleBasedUserSerializer(serializers.Serializer):
    def to_representation(self, instance):
        role = getattr(instance, 'role', 'customer')
        if role == 'customer':
            serializer = CustomerProfileSerializer(instance, context=self.context)
        elif role == 'promoter':
            serializer = PromoterProfileSerializer(instance, context=self.context)
        elif role == 'investor':
            serializer = InvestorProfileSerializer(instance, context=self.context)
        elif role == 'deliveryman':
            serializer = DeliveryManProfileSerializer(instance, context=self.context)
        elif role in ['admin', 'warehouse_staff']:
            serializer = BaseUserSerializer(instance, context=self.context)
        else:
            serializer = BaseUserSerializer(instance, context=self.context)
        return serializer.data


class ResendActivationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class CustomPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self,value):
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user is associated with this email address")

        if not (self.user.is_active and self.user.is_verified):
            raise serializers.ValidationError("User account is inactive or not verified")

        return value

    def get_user(self):
        return self.user

    def save(self):
        request = self.context.get('request')
        
        user = self.get_user()

        # Generate password reset token and uid
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Prepare email content
        email_sender = CustomPasswordResetEmail(
            context={
                'user':user,
                'uid':uid,
                'token':token,
                'request':request
            }
        )
        email_sender.send(to=[user.email])


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    def validate(self, attrs):
        uid = attrs.get('uid')
        token = attrs.get('token')
        new_password = attrs.get('new_password')

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError('Invalid UID')

        if not default_token_generator.check_token(self.user, token):
            raise serializers.ValidationError('Invalid or expired token')

        if self.user.check_password(new_password):
            raise serializers.ValidationError("New password cannot be the same as the old password")

        # ✅ Enforce Django's built-in password validators
        validate_password(new_password, self.user)

        return attrs

    def save(self):
        password = self.validated_data['new_password']
        self.user.set_password(password)
        self.user.save()
        return self.user
    
class CustomSetPasswordSerializer(SetPasswordSerializer):
    def validate(self, attrs):
        user = self.context['request'].user

        old_password = attrs.get("current_password")
        new_password = attrs.get("new_password")

        # Check if old password is correct
        if not user.check_password(old_password):
            raise serializers.ValidationError({"current_password": "Old password is incorrect."})

        # Prevent reuse of the old password
        if old_password == new_password:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password."})

        # Validate new password against Django validators
        validate_password(new_password, user)

        return attrs

    def save(self, **kwargs):
        password = self.validated_data["new_password"]
        self.user.set_password(password)
        self.user.save()
        return self.user

class FacebookLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(write_only=True)


    def validate_access_token(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Access token is required')

        return value