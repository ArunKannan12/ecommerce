from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from accounts.permissions import IsPromoter
from .serializers import PromoterSerializer
from .models import Promoter
from rest_framework.exceptions import ValidationError
# Create your views here.


class PromoterListCreateAPIView(ListCreateAPIView):
    permission_classes=[IsPromoter]
    serializer_class=PromoterSerializer

    def get_queryset(self):
        return Promoter.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        if Promoter.objects.filter(user=self.request.user).exists():
            raise ValidationError('You have already applied as a promoter')
        serializer.save(user=self.request.user)

class PromoterRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes=[IsPromoter]
    serializer_class=PromoterSerializer
    lookup_field='id'

    def get_queryset(self):
        return Promoter.objects.filter(user=self.request.user)
    
    