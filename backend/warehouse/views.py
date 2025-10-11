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
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import timedelta, date
from .pagination import WarehouseOrderPagination
from delivery.serializers import DeliveryManSerializer

class WarehouseOrderListAPIView(ListAPIView):
    serializer_class = WarehouseOrderSerializer
    permission_classes = [IsWarehouseStaffOrAdmin]
    pagination_class = WarehouseOrderPagination

    def get_queryset(self):
        # Include all warehouse-relevant statuses
        queryset = (
            Order.objects.filter(status__in=["processing", "picked", "packed", "shipped", "out_for_delivery"])
            .select_related("user", "delivered_by", "shipping_address")
            .prefetch_related("orderitem_set__product_variant")
            .order_by("-created_at")
        )

        # --- Filtering parameters ---
        status_param = self.request.query_params.get("status")
        customer_param = self.request.query_params.get("customer")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if status_param and status_param != "all":
            queryset = queryset.filter(status=status_param)
        if customer_param:
            queryset = queryset.filter(user__email__icontains=customer_param)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])

        return queryset



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
    pagination_class=WarehouseOrderPagination
    filterset_fields = {
        "status": ["exact"],
        "order__status": ["exact"],
        "order__delivered_by": ["exact"],
        "order__user": ["exact"],
    }

    def get_queryset(self):
        qs = OrderItem.objects.select_related(
            "order__delivered_by", "order__user", "product_variant"
        ).exclude(status="cancelled")  # Exclude cancelled items

        # Optional: filter by status from query params
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        # Optional: filter by product search
        product_search = self.request.query_params.get("product")
        if product_search:
            qs = qs.filter(product_variant__name__icontains=product_search)

        return qs.order_by("-id")
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


class WarehouseStatsWithTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWarehouseStaff]

    def get(self, request):
        today = date.today()
        last_7_days = today - timedelta(days=6)

        # 1️⃣ Overall counts
        pending_orders = Order.objects.filter(status='processing').count()
        picked_items = OrderItem.objects.filter(status='picked').count()
        packed_items = OrderItem.objects.filter(status='packed').count()
        shipped_items = OrderItem.objects.filter(status='shipped', order__delivered_by__isnull=True).count()
        assigned_orders = Order.objects.filter(delivered_by__isnull=False).count()

        # 2️⃣ Trends (last 7 days)
        orders_trend = (
            Order.objects
            .filter(created_at__date__gte=last_7_days)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        picked_trend = (
            OrderItem.objects
            .filter(status='picked', order__created_at__date__gte=last_7_days)
            .annotate(date=TruncDate('order__created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        packed_trend = (
            OrderItem.objects
            .filter(status='packed', order__created_at__date__gte=last_7_days)
            .annotate(date=TruncDate('order__created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        shipped_trend = (
            OrderItem.objects
            .filter(status='shipped', order__delivered_by__isnull=True, order__created_at__date__gte=last_7_days)
            .annotate(date=TruncDate('order__created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        assigned_trend = (
            Order.objects
            .filter(delivered_by__isnull=False, assigned_at__date__gte=last_7_days)
            .annotate(date=TruncDate('assigned_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response({
            "overall": {
                "pending_orders": pending_orders,
                "picked_items": picked_items,
                "packed_items": packed_items,
                "shipped_items": shipped_items,
                "assigned_orders": assigned_orders,
            },
            "trends": {
                "orders": list(orders_trend),
                "picked_items": list(picked_trend),
                "packed_items": list(packed_trend),
                "shipped_items": list(shipped_trend),
                "assigned_orders": list(assigned_trend),
            }
        })


class WarehouseUnassignedOrdersAPIView(ListAPIView):
    serializer_class=WarehouseOrderSerializer
    permission_classes=[IsWarehouseStaffOrAdmin]
    filter_backends=[DjangoFilterBackend]
    filterset_fields = {
        "status": ["exact"],     # filter by order status
        "user": ["exact"],       # filter by customer
        "order_number": ["exact"]  # specific order search
    }

    def get_queryset(self):
        return (
            Order.objects.filter(status__in=['shipped','out_for_delivery'],delivered_by__isnull=True)
            .select_related('user','shipping_address')
            .prefetch_related('orderitem_set__product_variant')
            .order_by('-created_at')
        )
    
class DeliverymanListForAssignmentAPIView(ListAPIView):
    """
    API to list only active deliverymen who are eligible for order assignment.
    Used in warehouse panel to assign orders.
    """
    serializer_class = DeliveryManSerializer
    permission_classes = [IsAuthenticated, IsWarehouseStaffOrAdmin]

    def get_queryset(self):
        return (
            DeliveryMan.objects
            .filter(
                user__is_active=True,
                user__role="deliveryman",
            )
            .select_related("user")  # improves performance
            .order_by("user__first_name")  # optional: consistent sorting
        )
