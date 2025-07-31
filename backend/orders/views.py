from .serializers import OrderSerializer,ShippingAddressSerializer
from rest_framework.generics import ListAPIView,RetrieveAPIView
from accounts.permissions import IsCustomer,IsAdminOrCustomer
from cart.models import CartItem,Cart
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import Order,OrderItem
from django.db import transaction
import razorpay
from django.conf import settings

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

            item_total=item.quantity * variant.product.price
            total_price+=item_total


            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                quantity=item.quantity,
                price=variant.product.price
            )

        order.total = total_price
        order.save()

        # Clear the cart
        cart_items.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        

class OrderListAPIView(ListAPIView):
    serializer_class=OrderSerializer
    permission_classes=[IsCustomer]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    

class OrderDetailAPIView(RetrieveAPIView):
    serializer_class=OrderSerializer
    permission_classes=[IsCustomer]
    lookup_field='id'


    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
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
        order.is_paid = True
        order.paid_at = timezone.now()
        order.payment_method = method

        # Optional: Automatically update status if still pending
        if order.status == 'pending':
            order.status = 'processing'

        order.save()

        return Response({'message': 'Payment confirmed'}, status=status.HTTP_200_OK)


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
            'order_id':razorpay_order.get('id'),
            'razorpay_key':settings.RAZORPAY_KEY_ID,
            'amount':razorpay_order.get('amount'),
            'currency':razorpay_order.get('currency'),
        },status=status.HTTP_200_OK)
    
class RazorpayPaymentVerifyAPIView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
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
            order = Order.objects.get(tracking_number=razorpay_order_id, user=request.user)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")

        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = 'processing'
        order.payment_method = 'Razorpay'
        order.save()

        return Response({'message': 'Payment verified and order updated'}, status=status.HTTP_200_OK)
