from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from accounts.permissions import IsInvestorOrAdmin,IsAdmin
from .utils import create_sale_shares_for_investment,generate_product_sale_shares
from datetime import datetime
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
            raise PermissionDenied('Only admins are allowed to update investor profiles.')

        serializer.save()
    
    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or user.role == 'admin'):
            raise PermissionDenied('Only admin can delete')
        instance.delete()



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

        serializer.save(investor=investor,confirmed=False)



class InvestmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated,IsInvestorOrAdmin]
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return Investment.objects.all()
        return Investment.objects.filter(investor__user=user)
    
    def perform_update(self, serializer):
        user = self.request.user
        data=self.request.data
        amount=data.get('amount')
        instance=serializer.instance

        if instance.confirmed and amount:
            raise PermissionDenied('confirmed amount cannot be updated')
        
        if 'confirmed' in data and not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            raise PermissionDenied("Only admin can change the confirmed status.")
        
        updated_investment=serializer.save()

        if not instance.confirmed and updated_investment.confirmed:
            create_sale_shares_for_investment(updated_investment)

             
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
class ProductSaleShareListAPIView(generics.ListAPIView):
    permission_classes=[IsInvestorOrAdmin]
    serializer_class=ProductSaleShareSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user,'role','')== 'admin':
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
    

class GenerateProductSalesShareAPIView(APIView):
    permission_classes=[IsAdmin]

    def post(self,request):
        start_date=request.data.get('start_date')
        end_date=request.data.get('end_date')

        if not start_date or not end_date:
            raise ValidationError({"detail":"start date and end date are required."})
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError({"detail": "Invalid date format. Use YYYY-MM-DD."})

        if start > end:
            raise ValidationError({"detail": "start_date must be before end_date"})

        generate_product_sale_shares(start, end)

        return Response({
            "message": f"Product sale shares generated for period {start} to {end}."})