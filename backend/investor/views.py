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
from rest_framework.views import APIView
from django.db.models import Sum

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
    
    def perform_update(self, serializer):
        user=self.request.user
        if not (user.is_staff or user.role =='admin'):
            raise PermissionDenied('only admin can update ')
        serializer.save()
    
    def perform_destroy(self, instance):
        user=self.request.user
        if not (user.is_staff or user.role =='admin'):
            raise PermissionDenied('only admin can delete ')
        instance.delete()


class InvestmentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes=[IsInvestorOrAdmin]
    serializer_class=InvestmentSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff and user.role == 'admin':
            return Investment.objects.all()
        return Investment.objects.filter(investor__user=user)
    
    class InvestmentListCreateAPIView(generics.ListCreateAPIView):
        permission_classes = [IsInvestorOrAdmin]
        serializer_class = InvestmentSerializer

        def get_queryset(self):
            user = self.request.user
            if user.is_staff and user.role == 'admin':
                return Investment.objects.all()
            return Investment.objects.filter(investor__user=user)

        def perform_create(self, serializer):
            user = self.request.user
            try:
                investor = Investor.objects.get(user=user)
            except Investor.DoesNotExist:
                raise ValidationError("No investor found for this user.")

            # ✅ Prevent multiple pending investments
            if Investment.objects.filter(investor=investor, confirmed=False).exists():
                raise ValidationError("You already have a pending investment.")

            # ✅ Force confirmed=False during creation
            instance = serializer.save(investor=investor, confirmed=False)

            # ✅ Set total_confirmed_investments only if confirmed=True (which won’t happen here)
            instance.total_confirmed_investments = Investment.objects.filter(
                investor=investor, confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0
            instance.save()



class InvestmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsInvestorOrAdmin]
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return Investment.objects.all()
        return Investment.objects.filter(investor__user=user)
    
    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        old_confirmed = instance.confirmed

        if 'confirmed' in self.request.data and not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            raise PermissionDenied("Only admin can change the confirmed status.")

        instance = serializer.save()

        # ✅ Update total_confirmed_investments if it was just confirmed
        if not old_confirmed and instance.confirmed:
            investor = instance.investor
            total = Investment.objects.filter(
                investor=investor, confirmed=True
            ).aggregate(total=Sum('amount'))['total'] or 0
            instance.total_confirmed_investments = total
            instance.save()
        
    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_staff:
            raise PermissionDenied("Only admins can delete investments.")
        instance.delete()

class InvestmentSummaryDetailedAPIView(APIView):
    permission_classes=[IsInvestorOrAdmin]

    def get(self,request):
        user=request.user

        if user.is_staff or getattr(user,'role','') == 'admin':
            confirmed=Investment.objects.filter(confirmed=True)
            pending=Investment.objects.filter(confirmed=False)
        else:
            try:
                investor=Investor.objects.get(user=user)
            except Investor.DoesNotExist:
                return Response({"detail":"Investor profile not found"},status=status.HTTP_404_NOT_FOUND)
            confirmed=Investment.objects.filter(investor=investor,confirmed=True)
            pending=Investment.objects.filter(investor=investor,confirmed=False)
        
        return Response({
                   "confirmed_total": sum(i.amount for i in confirmed),
                   "pending_total": sum(i.amount for i in pending),
                   "confirmed_investments": InvestmentSerializer(confirmed, many=True).data,
                   "pending_investments": InvestmentSerializer(pending, many=True).data
               })  
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