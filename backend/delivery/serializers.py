from rest_framework import serializers
from .models import DeliveryMan,DeliveryManRequest


class DeliveryManSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMan
        fields = ["id", "user", "phone", "address", "vehicle_number", 
                  "joined_at", "last_active", "total_deliveries", "earnings", "notes"]
        read_only_fields = ["joined_at", "last_active", "total_deliveries", "earnings"]


class DeliveryManRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=DeliveryManRequest
        fields = [
            'id', 'user', 'phone', 'address', 'vehicle_number', 
            'status', 'applied_at', 'reviewed_at', 'notes'
        ]
        read_only_fields=['status','applied_at','reviewed_at','user']

        def create(self, validated_data):
            user = self.context["request"].user
            if DeliveryManRequest.objects.filter(user=user, status="pending").exists():
                raise serializers.ValidationError("You already have a pending request.")
            return DeliveryManRequest.objects.create(user=user, **validated_data)