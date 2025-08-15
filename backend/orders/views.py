from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter    
from orders.serializers import OrderItemSerializer,OrderSummarySerializer,OrderDetailSerializer,OrderSerializer
from .serializers import OrderSerializer,ShippingAddressSerializer,CartCheckoutInputSerializer,ShippingAddressInputSerializer,ReferralCheckoutInputSerializer
from rest_framework.generics import ListAPIView,RetrieveAPIView,ListCreateAPIView,RetrieveUpdateDestroyAPIView
from accounts.permissions import IsCustomer,IsAdminOrCustomer,IsWarehouseStaffOrAdmin
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from cart.models import Cart,CartItem
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import Order,OrderItem,ShippingAddress
from django.db import transaction
import razorpay
from django.conf import settings
from promoter.models import Promoter
from promoter.utils import apply_promoter_commission
from django.shortcuts import get_object_or_404
from decimal import Decimal
from products.models import ProductVariant
from .utils import create_order_with_items,update_order_status_from_items
from datetime import timedelta
from django.utils import timezone
from delivery.permissions import IsDeliveryManOrAdmin

class ReferralCheckoutAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        serializer = ReferralCheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Step 1: Validate item list
        items = data.get("items")
        payment_method = data.get("payment_method")
        
        # Step 2: Validate shipping address
        shipping_address = None
        if data.get("shipping_address_id"):
            try:
                shipping_address = ShippingAddress.objects.get(id=data["shipping_address_id"], user=user)
            except ShippingAddress.DoesNotExist:
                raise ValidationError({"shipping_address_id": "Invalid address for this user."})
        else:
            shipping_data = data.get("shipping_address")
            if not shipping_data:
                raise ValidationError({"shipping_address": "This field is required."})
            shipping_serializer = ShippingAddressSerializer(data=shipping_data)
            shipping_serializer.is_valid(raise_exception=True)
            shipping_address = shipping_serializer.save(user=user)

        # Step 3: Validate referral code if provided
        promoter = None
        referral_code = request.query_params.get('ref')
        if referral_code:
            promoter = Promoter.objects.filter(
                referral_code=referral_code,
                application_status="approved"
            ).first()
            if not promoter:
                raise ValidationError({"referral_code": "Invalid or inactive referral code."})

        # Step 4: Validate payment method
        if payment_method not in ["Cash on Delivery", "Razorpay"]:
            raise ValidationError({"payment_method": "Invalid payment method."})

        # Step 5: Create order and optional Razorpay order
        order, razorpay_order = create_order_with_items(
            user=user,
            items=items,
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter
        )

        # Step 6: Return appropriate response
        if razorpay_order:
            return Response({
                "order_id": razorpay_order.get("id"),
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": razorpay_order.get("amount"),
                "currency": razorpay_order.get("currency"),
                "order": OrderSerializer(order).data
            }, status=status.HTTP_200_OK)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class CartCheckoutAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(cart__user=request.user)
        if not cart_items.exists():
            return Response({"detail":"Cart is empty"},status=status.HTTP_400_BAD_REQUEST)
        
        
        serializer = CartCheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Handle shipping address
        shipping_address = None
        if data.get("shipping_address_id"):
            try:
                shipping_address = ShippingAddress.objects.get(id=data["shipping_address_id"], user=user)
            except ShippingAddress.DoesNotExist:
                raise ValidationError({"shipping_address_id": "Invalid address for this user."})
        else:
            shipping_input = data.get("shipping_address")
            shipping_serializer = ShippingAddressSerializer(data=shipping_input)
            shipping_serializer.is_valid(raise_exception=True)
            shipping_address = shipping_serializer.save(user=user)

        # Handle referral code
        promoter = None
        referral_code = data.get("referral_code")
        if referral_code:
            promoter = Promoter.objects.filter(
                referral_code=referral_code,
                application_status="approved"
            ).first()
            if not promoter:
                raise ValidationError({"referral_code": "Invalid or inactive referral code."})

        # Handle payment method
        payment_method = data.get("payment_method")
        if payment_method not in ["Cash on Delivery", "Razorpay"]:
            raise ValidationError({"payment_method": "Invalid payment method."})

        # Create the order from cart
        order, razorpay_order = create_order_with_items(
            user=user,
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter,
            items=cart_items
        )
        if payment_method == "Cash on Delivery":
            cart_items.delete()
        # Prepare response
        if razorpay_order:
            return Response({
                "order_id": razorpay_order.get("id"),
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": razorpay_order.get("amount"),
                "currency": razorpay_order.get("currency"),
                "order": OrderSerializer(order).data
            }, status=status.HTTP_200_OK)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED) 
    

class OrderListAPIView(ListAPIView):
    serializer_class=OrderSummarySerializer
    permission_classes=[IsCustomer]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    

class OrderDetailAPIView(RetrieveAPIView):
    serializer_class=OrderDetailSerializer
    permission_classes=[IsCustomer]
    lookup_field='id'


    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("shipping_address", "promoter")
            .prefetch_related("orderitem_set__product_variant")
        )
    
class OrderPaymentAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, user=self.request.user)
        except Order.DoesNotExist:
            raise ValidationError('Order not found')

        if order.is_paid:
            raise ValidationError('Order is already paid')

        method = request.data.get('payment_method', 'Cash on Delivery')
        valid_methods = ['Cash on Delivery', 'Credit Card', 'UPI']

        if method not in valid_methods:
            raise ValidationError('Invalid payment method')

        # Update payment fields
        payment_method=method
        if payment_method.lower() == 'cash on delivery':
            order.payment_method='cash on delivery'
            order.status='pending'
            
        else:
            order.payment_method=payment_method
            order.is_paid = True
            order.paid_at = timezone.now()
            order.status='processing'
            apply_promoter_commission(order)

        order.save()

        return Response({'message': 'Order confirmed'}, status=status.HTTP_200_OK)


class CancelOrderAPIView(APIView):
    permission_classes=[IsAdminOrCustomer]

    def post(self,request,id):
        user=self.request.user
        try:
            if user.is_staff:
               order=Order.objects.get(id=id)
            else:
               order=Order.objects.get(id=id,user=user)

        except Order.DoesNotExist:
            raise ValidationError("order not found")
        
        if order.status == 'cancelled':
            return Response({'message':'Order is already cancelled'},status=status.HTTP_400_BAD_REQUEST)
        if order.status in ['delivered','shipped']:
            return Response({'message':f"cannot cancel order once it 's {order.status}"},status=status.HTTP_400_BAD_REQUEST)
        

        reason=request.data.get('cancel_reason','')
        order.status='cancelled'
        order.cancel_reason=reason
        order.save()

        if user.is_staff:
            restocked_items = []
            for item in order.orderitem_set.all():
                variant = item.product_variant
                variant.stock += item.quantity
                variant.save()
                restocked_items.append({
                    "variant": str(variant),
                    "restocked_quantity": item.quantity
                })

            return Response({
                'message': 'Order cancelled and stock restored',
                'restocked_items': restocked_items
            }, status=status.HTTP_200_OK)

        return Response({'message':'Order cancelled successfully'})
    

class RazorpayOrderCreateAPIView(APIView):
    permission_classes=[IsCustomer]

    def post(self,request,id):
        try:
            order=Order.objects.get(id=id,user=self.request.user)

        except Order.DoesNotExist:
            raise ValidationError("order not found")
        if order.is_paid:
            raise ValidationError('Order is already paid')
        if order.status.lower() == 'cancelled':
            raise ValidationError('Cannot pay for a cancelled order')
        
        client=razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        razorpay_order=client.order.create({
            'amount':int(order.total * 100),
            'currency':'INR',
            'receipt':f"order_rcptid_{order.id}",
            'payment_capture':1
        })
        order.tracking_number=razorpay_order.get('id')
        order.save()

        return Response({
            'razorpay_order_id':razorpay_order.get('id'),
            'razorpay_key':settings.RAZORPAY_KEY_ID,
            'amount':razorpay_order.get('amount'),
            'currency':razorpay_order.get('currency'),
            'order':OrderSerializer(order).data
        },status=status.HTTP_200_OK)
    
class RazorpayPaymentVerifyAPIView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_id = request.data.get('order_id')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature,order_id]):
            raise ValidationError("Missing Razorpay payment details")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            raise ValidationError("Invalid payment signature")

        # Mark order as paid
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")
        
        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = 'processing'
        order.payment_method = 'Razorpay'
        order.save()

        apply_promoter_commission(order)

        CartItem.objects.filter(cart__user=request.user).delete()


        return Response({'message': 'Payment verified and order updated'}, status=status.HTTP_200_OK)

class PickOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        try:
            item = OrderItem.objects.get(id=id)
        except OrderItem.DoesNotExist:
            raise ValidationError("Item not found")

        if item.status != 'pending':
            return Response({'message': 'Only pending items can be picked'}, status=400)

        item.status = 'picked'
        item.save(update_fields=['status'])

        update_order_status_from_items(item.order)

        return Response({'message': 'Item marked as picked'}, status=200)
    
class PackOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        try:
            item = OrderItem.objects.get(id=id)
        except OrderItem.DoesNotExist:
            raise ValidationError("Item not found")

        if item.status != 'picked':
            return Response({'message': 'Only picked items can be packed'}, status=400)

        item.status = 'packed'
        item.packed_at = timezone.now()
        item.save(update_fields=['status', 'packed_at'])

        update_order_status_from_items(item.order)

        return Response({'message': 'Item marked as packed'}, status=200)
    

class ShipOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        try:
            item = OrderItem.objects.get(id=id)
        except OrderItem.DoesNotExist:
            raise ValidationError("Item not found")

        if item.status != 'packed':
            return Response({'message': 'Only packed items can be shipped'}, status=400)

        item.status = 'shipped'
        item.shipped_at = timezone.now()
        item.save(update_fields=['status', 'shipped_at'])

        update_order_status_from_items(item.order)

        return Response({'message': 'Item marked as shipped'}, status=200)
    

class OrderItemListAPIView(ListAPIView):
    permission_classes = [IsWarehouseStaffOrAdmin]
    serializer_class = OrderItemSerializer
    filter_backends=[DjangoFilterBackend,SearchFilter]
    filterset_fields=['status','order__id']
    search_fields=['product_variant__product__name','order__id']
    

    def get_queryset(self):
        return OrderItem.objects.filter(
            status__in=['pending', 'picked', 'packed']
        ).order_by('status', 'id')
    
class OrderSummaryListAPIView(ListAPIView):
    serializer_class = OrderSummarySerializer
    permission_classes = [IsWarehouseStaffOrAdmin | IsDeliveryManOrAdmin]  # or delivery-man role

    def get_queryset(self):
        queryset = Order.objects.all().order_by('-created_at')

        # Optional: filter out cancelled or completed orders if not needed
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

class ShippingAddressListCreateView(ListCreateAPIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        # Only return addresses belonging to the authenticated user
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the user from the request
        serializer.save(user=self.request.user)

class ShippingAddressRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsCustomer]
    lookup_field='id'

    def get_queryset(self):
        # Only allow access to the user's own addresses
        return ShippingAddress.objects.filter(user=self.request.user)



class BuyNowAPIView(APIView):
    permission_classes = [IsCustomer]  # or your IsCustomer permission

    def post(self, request):
        user = request.user
        items = request.data.get("items")  # list of {product_variant_id, quantity}
        shipping_address_id = request.data.get("shipping_address")
        payment_method = request.data.get("payment_method")

        if not items:
            return Response({"detail": "No items provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not shipping_address_id:
            return Response({"detail": "Shipping address is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not payment_method:
            return Response({"detail": "Payment method is required."}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address = get_object_or_404(ShippingAddress, id=shipping_address_id, user=user)

        try:
            order, razorpay_order = create_order_with_items(
                user=user,
                items=items,
                shipping_address=shipping_address,
                payment_method=payment_method
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order)
        data = serializer.data
        if razorpay_order:
            data["razorpay_order"] = razorpay_order

        return Response(data, status=status.HTTP_201_CREATED)