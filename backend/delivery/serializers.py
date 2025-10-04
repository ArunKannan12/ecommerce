from rest_framework import serializers
from .models import DeliveryMan,DeliveryManRequest
import re
from orders.models import OrderItem

class DeliveryManSerializer(serializers.ModelSerializer):
    full_name=serializers.SerializerMethodField()
    email=serializers.SerializerMethodField()
    is_active=serializers.BooleanField(source='user.is_active',read_only=True)

    total_orders_pending=serializers.SerializerMethodField()
    earnings_pending=serializers.SerializerMethodField()
    current_status=serializers.SerializerMethodField()
   
    class Meta:
        model = DeliveryMan
        fields = ["id", "user","full_name","email", "phone", "address", "vehicle_number",
                  "joined_at", "last_active", "total_deliveries", "earnings", "notes","is_active",
                  "total_orders_pending","earnings_pending","current_status"]
        
        read_only_fields = ['user',"joined_at", "last_active", "total_deliveries", "earnings"]
    def get_full_name(self,obj):
        return obj.user.get_full_name()
    def get_email(self,obj):
        return obj.user.email
    
    def get_total_orders_pending(self, obj):
        """Count orders assigned to this deliveryman but not yet delivered/failed"""
        return OrderItem.objects.filter(
            order__delivered_by=obj,
            status__in=["out_for_delivery", "shipped"]
        ).count()

    def get_earnings_pending(self, obj):
        """Placeholder: calculate unpaid earnings"""
        # Example: if you track payouts separately
        return 0  # Replace with logic if you implement payout settlement

    def get_current_status(self, obj):
        """Infer status (example logic, can be expanded with real tracking)"""
        active_orders = OrderItem.objects.filter(
            order__delivered_by=obj,
            status__in=["out_for_delivery", "shipped"]
        ).exists()
        return "on_delivery" if active_orders else "available"
    def validate_phone(self, value):
        """
        Indian phone number validation: 10 digits starting with 6-9, optional +91
        """
        if value:
            clean_value = value.strip().replace(" ", "").replace("-", "")
            pattern = r'^(?:\+91)?[6-9]\d{9}$'
            if not re.fullmatch(pattern, clean_value):
                raise serializers.ValidationError(
                    "Enter a valid Indian phone number (10 digits, starting with 6-9, optional +91)."
                )
            # Unique check ignoring current instance
            qs = DeliveryMan.objects.filter(phone=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("This phone number is already in use.")
        return value

    def validate_vehicle_number(self, value):
        """
        Indian vehicle number plate validation (supports KA01AB1234, TN43X1234, etc.)
        """
        if value:
            clean_value = value.strip().replace(" ", "").upper()
            pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{3,4}$'
            if not re.fullmatch(pattern, clean_value):
                raise serializers.ValidationError(
                    "Enter a valid Indian vehicle number plate (e.g., KA01AB1234, TN43X1234)."
                )
            value = clean_value  # store in uppercase
        return value

    def to_representation(self, instance):
        """
        Ensure vehicle_number is always returned in uppercase in the API response.
        """
        ret = super().to_representation(instance)
        if ret.get("vehicle_number"):
            ret["vehicle_number"] = ret["vehicle_number"].upper()
        return ret

class DeliveryManRequestSerializer(serializers.ModelSerializer):
    user=serializers.SerializerMethodField()
    email=serializers.SerializerMethodField()

    class Meta:
        model = DeliveryManRequest
        fields = [
            'id', 'user', 'phone', 'address', 'vehicle_number', 'email',
            'status', 'applied_at', 'reviewed_at', 'notes'
        ]
        read_only_fields = ['status', 'applied_at', 'reviewed_at', 'user']
        extra_kwargs = {
                'phone': {'required': True},
                'address': {'required': True},
                'vehicle_number': {'required': True},
            }
    def get_user(self,obj):
        return obj.user.get_full_name()
    def get_email(self,obj):
        return obj.user.email
    def validate_phone(self, value):
        if value:
            value = value.strip().replace(" ", "").replace("-", "")
            pattern = r'^(?:\+91)?[6-9]\d{9}$'
            if not re.fullmatch(pattern, value):
                raise serializers.ValidationError(
                    "Enter a valid Indian phone number (10 digits, starting with 6-9, optional +91)."
                )
        return value

    def validate_vehicle_number(self, value):
        if value:
            value = value.strip().replace(" ", "").upper()
            pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{3,4}$'
            if not re.fullmatch(pattern, value):
                raise serializers.ValidationError(
                    "Enter a valid Indian vehicle number plate (e.g., KA01AB1234, TN43X1234)."
                )
            value = value.upper()  # ensure uppercase
        return value
    
    def to_representation(self, instance):
        """
        Ensure vehicle_number is always returned in uppercase in the API response.
        """
        ret = super().to_representation(instance)
        if ret.get("vehicle_number"):
            ret["vehicle_number"] = ret["vehicle_number"].upper()
        return ret

    def create(self, validated_data):
        user = self.context["request"].user
        # Prevent multiple pending requests or already-approved deliveryman
        if DeliveryManRequest.objects.filter(user=user, status="pending").exists():
            pending_request = DeliveryManRequest.objects.get(user=user, status="pending")
            raise serializers.ValidationError({
                "detail": "You already have a pending request.",
                "edit_request_id": pending_request.id
            })
        if getattr(user, 'role','') == 'deliveryman':
            raise serializers.ValidationError("You are already approved as a deliveryman.")

        return DeliveryManRequest.objects.create(user=user, **validated_data)
    