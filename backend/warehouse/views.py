from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from delivery.models import DeliveryMan
from orders.models import Order, OrderItem
from accounts.permissions import IsWarehouseStaffOrAdmin,IsWarehouseStaff
from orders.utils import update_item_status
from rest_framework.generics import ListAPIView
from .serializers import WarehouseOrderSerializer,WarehouseOrderItemSerializer
from django_filters.rest_framework import DjangoFilterBackend



class WarehouseOrderListAPIView(ListAPIView):
    serializer_class=WarehouseOrderSerializer
    permission_classes = [IsWarehouseStaffOrAdmin]

    def get_queryset(self):
        return (
            Order.objects.filter(status__in=["processing", "shipped"])
            .select_related("user", "delivered_by", "shipping_address")
            .prefetch_related("orderitem_set__product_variant")
            .order_by("-created_at")
        )

class PickOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        update_item_status(id, expected_status='pending', new_status='picked', user=request.user)
        return Response({'message': 'Item marked as picked'}, status=200)


class PackOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        update_item_status(id, expected_status='picked', new_status='packed', user=request.user, timestamp_field='packed_at')
        return Response({'message': 'Item marked as packed'}, status=200)


class ShipOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        update_item_status(id, expected_status='packed', new_status='shipped', user=request.user, timestamp_field='shipped_at')
        return Response({'message': 'Item marked as shipped'}, status=200)


class AssignOrdersToDeliverymanAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request):
        data = request.data
        order_ids = data.get("order_ids")
        deliveryman_id = data.get("deliveryman_id")

        if not order_ids or not deliveryman_id:
            return Response({"error": "Both 'order_ids' and 'deliveryman_id' are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if isinstance(order_ids, int):
            order_ids = [order_ids]
        elif not isinstance(order_ids, list):
            return Response({"error": "'order_ids' must be a list or an integer."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            deliveryman = DeliveryMan.objects.get(id=deliveryman_id)
        except DeliveryMan.DoesNotExist:
            raise NotFound("Deliveryman not found.")

        assigned_orders = []
        skipped_orders = []

        for order_id in order_ids:
            try:
                order = Order.objects.get(id=order_id, status='shipped')
            except Order.DoesNotExist:
                skipped_orders.append({"order_id": order_id, "reason": "Not found or not in 'shipped' status"})
                continue

            if order.delivered_by:
                skipped_orders.append({
                    "order_id": order.id,
                    "reason": f"Already assigned to {order.delivered_by.user.email}"
                })
                continue

            # Only assign if all items are shipped
            if order.orderitem_set.exclude(status='shipped').exists():
                skipped_orders.append({"order_id": order.id, "reason": "Some items are not yet shipped"})
                continue

            order.delivered_by = deliveryman
            order.assigned_at = timezone.now()
            order.save(update_fields=['delivered_by', 'assigned_at', 'updated_at','status'])
            for item in order.orderitem_set.all():
                item.status='out_for_delivery'
                item.out_for_delivery_at=timezone.now()
                item.save(update_fields=['status','out_for_delivery_at'])
            assigned_orders.append(order.id)
        return Response({
            "assigned_orders": assigned_orders,
            "skipped_orders": skipped_orders,
            "message": f"{len(assigned_orders)} orders assigned to {deliveryman.user.email}"
        }, status=status.HTTP_200_OK)

class WarehouseOrderItemStatusAPIView(ListAPIView):

    serializer_class = WarehouseOrderItemSerializer
    permission_classes = [IsWarehouseStaffOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "status": ["exact"],
        "order__status": ["exact"],
        "order__delivered_by": ["exact"],
        "order__user": ["exact"],
    }

    def get_queryset(self):
        return OrderItem.objects.select_related("order__delivered_by", "order__user", "product_variant")

class WarehouseAssignedOrdersAPIView(ListAPIView):
    serializer_class = WarehouseOrderSerializer   # Use the warehouse serializer
    permission_classes = [IsWarehouseStaffOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "status": ["exact"],                # filter by order status
        "delivered_by": ["exact"],          # filter by deliveryman ID
        "user": ["exact"],                  # filter by customer ID
        "assigned_at": ["gte", "lte"],      # filter by assignment date range
    }

    def get_queryset(self):
        # Only include orders that have been assigned to a deliveryman
        return (
            Order.objects
            .filter(delivered_by__isnull=False)
            .select_related("user", "delivered_by", "shipping_address")
            .prefetch_related("orderitem_set__product_variant")
            .order_by("-assigned_at")
        )
