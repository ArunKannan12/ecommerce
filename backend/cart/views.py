from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.throttling import UserRateThrottle

from .serializers import CartItemSerializer, CartSummarySerializer,CartItemInputSerializer
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
        print(f"[CartMerge] User: {request.user}")

        items = request.data.get("items", [])
        if not isinstance(items, list):
            print(f"[CartMerge] Invalid payload: Expected a list, got {type(items).__name__}")
            return Response({"error": "Expected a list of items"}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        print(f"[CartMerge] Cart ID: {cart.id}")

        merged_items = []
        skipped_items = []
        failed_items = []

        for idx, item in enumerate(items):
            print(f"[CartMerge] Processing item {idx + 1}: {item}")

            serializer = CartItemInputSerializer(data=item)
            if not serializer.is_valid():
                print(f"[CartMerge] Skipped: Invalid item data - {serializer.errors}")
                skipped_items.append({
                    "item": item,
                    "errors": serializer.errors
                })
                continue

            validated_data = serializer.validated_data
            variant_id = validated_data['product_variant_id']
            quantity = validated_data['quantity']

            try:
                variant = ProductVariant.objects.get(id=variant_id)
                print(f"[CartMerge] Found variant: {variant.id} - {variant.variant_name}")
            except ProductVariant.DoesNotExist:
                print(f"[CartMerge] Failed: Variant {variant_id} not found")
                failed_items.append(variant_id)
                continue

            try:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_variant=variant,
                    defaults={'quantity': quantity}
                )
                if created:
                    print(f"[CartMerge] Created new cart item")
                    check_stock(variant, quantity)
                else:
                    new_quantity = cart_item.quantity + quantity
                    print(f"[CartMerge] Updated cart item: {cart_item.quantity} → {new_quantity}")
                    check_stock(variant, new_quantity)
                    cart_item.quantity = new_quantity
                    cart_item.save()

                merged_items.append({
                    "variant_id": variant_id,
                    "quantity": cart_item.quantity
                })

            except Exception as e:
                print(f"[CartMerge] Failed to merge item {variant_id}: {str(e)}")
                failed_items.append({
                    "variant_id": variant_id,
                    "error": str(e)
                })

        print(f"[CartMerge] Merge complete. Merged: {len(merged_items)}, Skipped: {len(skipped_items)}, Failed: {len(failed_items)}")

        return Response({
            "detail": "Cart merged successfully",
            "merged_items": merged_items,
            "skipped_items": skipped_items,
            "failed_items": failed_items
        }, status=status.HTTP_200_OK)

class ProductVariantBulkAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        variant_ids = request.data.get('variant_ids', [])
        if not isinstance(variant_ids, list):
            return Response({"error": "variant_ids must be a list"}, status=400)

        variants = ProductVariant.objects.filter(id__in=variant_ids).prefetch_related('images', 'product__images')
        serializer = ProductVariantSerializer(variants, many=True, context={'request': request})
        return Response(serializer.data)

