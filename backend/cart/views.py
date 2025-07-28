from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from .serializers import CartItemSerializer,CartSerializer
from .models import CartItem,Cart
from rest_framework.exceptions import ValidationError
# Create your views here.

class CartItemListCreateApiView(ListCreateAPIView):
    serializer_class=CartItemSerializer
    permission_classes=[AllowAny]
    
    def get_queryset(self):

        return CartItem.objects.filter(cart__user=self.request.user)
    
    def perform_create(self, serializer):
        cart=serializer.validated_data.get('cart_id')
        if cart.user != self.request.user:
            raise ValidationError('You can only add items to your own cart')
        serializer.save()

class CartItemRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class=CartItemSerializer
    permission_classes=[AllowAny]
    lookup_field='id'


        