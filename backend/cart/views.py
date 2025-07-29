from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from .serializers import CartItemSerializer,CartSerializer
from .models import CartItem,Cart
from rest_framework.exceptions import ValidationError
from accounts.permissions import IsCustomer
# Create your views here.

class CartItemListCreateApiView(ListCreateAPIView):
    serializer_class=CartItemSerializer
    permission_classes=[IsCustomer]
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def perform_create(self, serializer):
        cart,_=Cart.objects.get_or_create(user=self.request.user)
        variant=serializer.validated_data.get('product_variant_id')
        quantity=serializer.validated_data.get('quantity')

        if variant.stock < quantity:
            raise ValidationError('Not enough stock')
        existing_item=CartItem.objects.filter(cart=cart,product_variant=variant).first()
        if existing_item:
            new_quantity=existing_item.quantity + quantity

            if new_quantity > variant.stock:
                raise ValidationError('Not enough stock for the total quantity')
            existing_item.quantity = new_quantity
            existing_item.save()
        else:
            serializer.save(cart=cart)

class CartItemRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class=CartItemSerializer
    permission_classes=[IsCustomer]
    lookup_field='id'

    def perform_update(self, serializer):
        item=serializer.instance

        if item.cart.user != self.request.user:
            raise ValidationError("you can't update items in someone else's cart.")
        
        new_quantity=serializer.validated_data.get('quantity')

        if new_quantity > item.product_variant.stock:
            raise ValidationError('Not enough stock available')

        serializer.save()

    def perform_destroy(self, instance):
        if instance.cart.user != self.request.user:
            raise ValidationError("You can't remove items from someone else's cart.")
        instance.delete()