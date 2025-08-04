from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from accounts.permissions import IsAdminOrPromoter
from .serializers import PromoterSerializer,PromoterCommissionSerializer,WithdrawalRequestSerializer
from django.utils import timezone
from .models import Promoter,PromoterCommission,WithdrawalRequest
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsPromoter,IsAdminOrPromoter,IsAdmin
from rest_framework.views import APIView
from orders.models import Order
from rest_framework.response import Response
from rest_framework import status
from .utils import apply_promoter_commission
from django.db import transaction
# Create your views here.


class PromoterListCreateAPIView(ListCreateAPIView):
    permission_classes=[IsAdminOrPromoter]
    serializer_class=PromoterSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or user.role == 'admin':
            return Promoter.objects.all()
        return Promoter.objects.filter(user=user)
    
    def perform_create(self, serializer):
        if Promoter.objects.filter(user=self.request.user).exists():
            raise ValidationError('You have already applied as a promoter')
        serializer.save(user=self.request.user)

class PromoterRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes=[IsAuthenticated,IsAdminOrPromoter]
    serializer_class=PromoterSerializer
    lookup_field='id'

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or user.role == 'admin':
            return Promoter.objects.all()
        return Promoter.objects.filter(user=user)
    
    def perform_update(self, serializer):
        user = self.request.user
        # Only allow admin to update
        if not (user.is_staff or user.role == 'admin'):
            raise PermissionDenied("You are not allowed to update promoter details.")
        
        data = self.request.data
        old_status = serializer.instance.application_status
        new_status = data.get('application_status', old_status)

        if old_status != new_status:
            serializer.save(approved_at=timezone.now() if new_status == 'approved' else None)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        user=self.request.user
        if not user.is_staff or user.role == 'admin':
            raise PermissionDenied('only admins can delete promoter profiles')
        instance.delete()

class PromoterCommissionListCreateAPIView(ListCreateAPIView):
    serializer_class=PromoterCommissionSerializer
    permission_classes=[IsPromoter]

    def get_queryset(self):
        user=self.request.user
        return PromoterCommission.objects.filter(promoter__user=user)
    
    def perform_create(self, serializer):
        promoter=Promoter.objects.get(user=self.request.user)
        serializer.save(promoter=promoter)

class WithdrawalRequestListCreateAPIView(ListCreateAPIView):
    serializer_class=WithdrawalRequestSerializer
    permission_classes=[IsPromoter]

    def get_queryset(self):
        user=self.request.user
        return WithdrawalRequest.objects.filter(promoter__user=user)
    
    def perform_create(self, serializer):
        promoter=Promoter.objects.get(user=self.request.user)
        serializer.save(promoter=promoter)

class WithdrawalRequestAdminManageView(RetrieveUpdateDestroyAPIView):
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

