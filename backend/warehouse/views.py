from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from delivery.models import DeliveryMan
from orders.models import Order, OrderItem
from accounts.permissions import IsWarehouseStaffOrAdmin,IsWarehouseStaff
from orders.utils import update_item_status,update_order_status_from_items
from rest_framework.generics import ListAPIView
from .serializers import WarehouseOrderSerializer,WarehouseOrderItemSerializer
from django_filters.rest_framework import DjangoFilterBackend
from admin_dashboard.models import WarehouseLog



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
        update_item_status(item_id=id, expected_status='pending', new_status='picked', user=request.user,comment="Item picked by warehouse staff")
        return Response({'message': 'Item marked as picked'}, status=200)


class PackOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        update_item_status(item_id=id, expected_status='picked', new_status='packed', user=request.user, timestamp_field='packed_at',comment="Item packed by warehouse staff")
        return Response({'message': 'Item marked as packed'}, status=200)


class ShipOrderItemAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request, id):
        update_item_status(item_id=id, expected_status='packed', new_status='shipped', user=request.user, timestamp_field='shipped_at',comment="Item shipped by warehouse staff")
        return Response({'message': 'Item marked as shipped'}, status=200)

class AssignOrdersToDeliverymanAPIView(APIView):
    permission_classes = [IsWarehouseStaffOrAdmin]

    def post(self, request):
        data = request.data
        order_numbers = data.get("order_numbers")
        deliveryman_id = data.get("deliveryman_id")

        if not order_numbers or not deliveryman_id:
            return Response(
                {"error": "Both 'order_numbers' and 'deliveryman_id' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(order_numbers, str):
            order_numbers = [order_numbers]
        elif not isinstance(order_numbers, list):
            return Response(
                {"error": "'order_numbers' must be a list or a string."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            deliveryman = DeliveryMan.objects.get(id=deliveryman_id)
        except DeliveryMan.DoesNotExist:
            raise NotFound("Deliveryman not found.")

        assigned_orders = []
        skipped_orders = []

        for number in order_numbers:
            try:
                order = Order.objects.get(
                    order_number=number, status__in=['shipped', 'out_for_delivery']
                )
            except Order.DoesNotExist:
                skipped_orders.append({
                    "order_number": number,
                    "reason": "Not found or not in 'shipped'/'out_for_delivery' status"
                })
                continue

            if order.delivered_by:
                skipped_orders.append({
                    "order_number": order.order_number,
                    "reason": f"Already assigned to {order.delivered_by.user.email}"
                })
                continue

            # Only assign if all items are shipped
            if order.orderitem_set.exclude(status__in=['shipped', 'out_for_delivery']).exists():
                skipped_orders.append({
                    "order_number": order.order_number,
                    "reason": "Some items are not yet shipped"
                })
                continue

            # Assign deliveryman
            order.delivered_by = deliveryman
            order.assigned_at = timezone.now()
            order.save(update_fields=['delivered_by', 'assigned_at'])

            # Update each item via update_item_status
            for item in order.orderitem_set.all():
                update_item_status(
                    item_id=item.id,
                    expected_status='shipped',
                    new_status='out_for_delivery',
                    user=request.user,
                    timestamp_field='out_for_delivery_at',
                    comment=f"Assigned to deliveryman ({deliveryman.user.email})"
                )

            update_order_status_from_items(order)
            assigned_orders.append(order.order_number)

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
