# delivery/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import DeliveryManSerializer
from rest_framework import status
from .models import DeliveryMan
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from orders.models import Order
from promoter.utils import apply_promoter_commission
from delivery.permissions import IsDeliveryManOrAdmin  
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView,ListAPIView
from rest_framework.exceptions import PermissionDenied
from orders.serializers import OrderSerializer
class MarkCODOrderDeliveredAndPaidAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDeliveryManOrAdmin]

    @transaction.atomic
    def post(self, request, id):
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")
        
        if order.status.lower() != 'shipped':
            return Response({'message': 'Only shipped orders can be marked as delivered'}, status=status.HTTP_400_BAD_REQUEST)

        if order.payment_method.lower() != 'cash on delivery':
            return Response({'message': 'Only COD orders can be marked as paid here'}, status=status.HTTP_400_BAD_REQUEST)

        if order.is_paid:
            return Response({'message': 'Order already marked as paid'}, status=status.HTTP_400_BAD_REQUEST)

        # Update payment and delivery status
        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = 'delivered'
        order.save()

        # Apply promoter commission if applicable
        apply_promoter_commission(order)

        return Response({
            'message': 'Order marked as paid and delivered. Commission applied.',
            'order_id': order.id,
            'commission': order.commission,
            'promoter': order.promoter.user.email if order.promoter else None
        }, status=status.HTTP_200_OK)


class DeliveryManListCreateAPIView(ListCreateAPIView):
    permission_classes=[IsDeliveryManOrAdmin]
    serializer_class=DeliveryManSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or getattr(user,'role','') == 'admin':
            return DeliveryMan.objects.all()
        return DeliveryMan.objects.filter(user=user)
    
class DeliveryManRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    permission_classes=[IsDeliveryManOrAdmin]
    serializer_class=DeliveryManSerializer

    def get_queryset(self):
        user=self.request.user
        if user.is_staff or user.role == 'admin':
            return DeliveryMan.objects.all()
        return DeliveryMan.objects.filter(user=user)
    

    def perform_destroy(self, instance):
        user=self.request.user
        if not (user.is_staff or user.role == 'admin'):
            raise PermissionDenied('Only admins can delete deliveryman profile')
        instance.delete()

class ShippedOrderForDeliveryAPIView(ListAPIView):
    permission_classes=[IsDeliveryManOrAdmin]
    serializer_class=OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(status='shipped').order_by('-created_at')