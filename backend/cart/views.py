from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.throttling import UserRateThrottle

from .serializers import CartItemSerializer, CartSummarySerializer
from .models import CartItem, Cart
from accounts.permissions import IsCustomer
from products.models import ProductVariant
from products.serializers import ProductVariantSerializer
from .utils import check_stock

class CartItemListCreateApiView(ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product_variant = serializer.validated_data.get('product_variant')
        quantity = serializer.validated_data.get('quantity')
        existing_item = CartItem.objects.filter(cart=cart, product_variant=product_variant).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            check_stock(product_variant, new_quantity)
            existing_item.quantity = new_quantity
            existing_item.save()
        else:
            check_stock(product_variant, quantity)
            serializer.save(cart=cart)


class CartItemRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsCustomer]
    lookup_field = 'id'

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
    @transaction.atomic

    def perform_update(self, serializer):
        item = serializer.instance

        if item.cart.user != self.request.user:
            raise ValidationError("You can't update items in someone else's cart.")

        new_quantity = serializer.validated_data.get('quantity')
        check_stock(item.product_variant, new_quantity)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.cart.user != self.request.user:
            raise ValidationError("You can't remove items from someone else's cart.")
        instance.delete()


class CartSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({
                "items": [],
                "total_quantity": 0,
                "total_price": 0,
            })

        serializer = CartSummarySerializer(cart, context={'request': request})
        return Response(serializer.data)


class CartMergeAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    throttle_classes = [UserRateThrottle]

    @transaction.atomic

    def post(self, request):
        items = request.data.get('items', [])
        cart, _ = Cart.objects.get_or_create(user=request.user)

        for item in items:
            variant_id = item.get('product_variant_id')
            quantity = item.get('quantity', 1)

            if not variant_id:
                continue

            variant = get_object_or_404(ProductVariant, id=variant_id)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=variant,
                defaults={'quantity': quantity}
            )
            if not created:
                new_quantity = cart_item.quantity + quantity
                check_stock(variant, new_quantity)
                cart_item.quantity = new_quantity
                cart_item.save()

        return Response({"detail": "Cart merged successfully"}, status=status.HTTP_200_OK)


class ProductVariantBulkAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        variant_ids = request.data.get('variant_ids', [])
        if not isinstance(variant_ids, list):
            return Response({"error": "variant_ids must be a list"}, status=400)

        variants = ProductVariant.objects.filter(id__in=variant_ids).prefetch_related('images', 'product__images')
        serializer = ProductVariantSerializer(variants, many=True, context={'request': request})
        return Response(serializer.data)

