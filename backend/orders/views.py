from django.shortcuts import render
from .serializers import OrderSerializer,OrderItemSerializer,ShippingAddressSerializer
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from accounts.permissions import IsCustomer
from cart.models import CartItem,Cart
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import Order,OrderItem,ShippingAddress
from django.db import transaction
# Create your views here.


class CheckoutAPIView(APIView):
    permission_classes=[IsCustomer]
    
    @transaction.atomic
    def post(self,request):
        user=request.user
        cart=Cart.objects.filter(user=user).first()

        if not cart:
            raise ValidationError('Cart does not exist')
        

        cart_items=CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            raise ValidationError('Cart is empty')
        
        serializer=ShippingAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping_address=serializer.save(user=user)


        order=Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            total=0,
            payment_method=request.data.get('payment_method','Cash on Delivery'),
            is_paid=False,
            paid_at=None,
            
        )

        total_price=0

        for item in cart_items:
            variant=item.product_variant

            if item.quantity > variant.stock:
                raise ValidationError(f"not enough stock for {variant}")
            
            variant.stock -=item.quantity
            variant.save()

            item_total=item.quantity * variant.price
            total_price+=item_total


            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                quantity=item.quantity,
                price=variant.price
            )

        order.total = total_price
        order.save()

        # Clear the cart
        cart_items.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        