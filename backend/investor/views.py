from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsInvestorOrAdmin
from rest_framework.exceptions import PermissionDenied
from .models import (Investment,
                     Investor,
                     InvestorWallet,
                     Payout,
                     ProductSaleShare
                     )
from .serializers import (InvestmentSerializer,
                        InvestorSerializer,
                        InvestorWalletSerializer,
                        PayoutSerializer,
                        ProductSaleShareSerializer
                        )
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

class InvestorListCreateAPIView(generics.ListCreateAPIView):
    permission_classes=[IsAuthenticated,IsInvestorOrAdmin]
    serializer_class=InvestorSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or user.role == 'admin':
            return Investor.objects.all()
        return Investor.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        user = self.request.user
        if Investor.objects.filter(user=user).exists():
            raise ValidationError({'detail': 'Investor already exists'})
        serializer.save(user=user)

    
class InvestorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes=[IsAuthenticated,IsInvestorOrAdmin]
    serializer_class=InvestorSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or user.role == 'admin':
            return Investor.objects.all()
        return Investor.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        user=self.request.user
        if not (user.is_staff or user.role =='admin'):
            return PermissionDenied('only admin can delete ')
        instance.delete()


class InvestmentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes=[IsInvestorOrAdmin]
    serializer_class=InvestmentSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff and user.role == 'admin':
            return Investment.objects.all()
        return Investment.objects.filter(investor__user=user)
    
    def perform_create(self, serializer):
        user=self.request.user
        serializer.save(investor=Investor.objects.get(user=user))


class InvestmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsInvestorOrAdmin]
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Investment.objects.all()
        return Investment.objects.filter(investor__user=user)

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_staff:
            raise PermissionDenied("Only admins can delete investments.")
        instance.delete()


class ProductSaleShareListCreateAPIView(generics.ListCreateAPIView):
    permission_classes=[IsInvestorOrAdmin]
    serializer_class=ProductSaleShareSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ProductSaleShare.objects.all()
        return ProductSaleShare.objects.filter(investor__user=user)
    
class PayoutListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsInvestorOrAdmin]
    serializer_class = PayoutSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payout.objects.all()
        return Payout.objects.filter(investor__user=user)

    def perform_create(self, serializer):
        serializer.save(investor=Investor.objects.get(user=self.request.user))

class InvestorWalletDetailAPIView(generics.RetrieveAPIView):
    permission_classes=[IsInvestorOrAdmin]
    serializer_class=InvestorWalletSerializer

    def get_object(self):
        user=self.request.user
        if user.is_staff:
            investor_id=self.kwargs.get("investor_id")
            return InvestorWallet.objects.get(investor__id=investor_id)
        return InvestorWallet.objects.get(investor__user=user)