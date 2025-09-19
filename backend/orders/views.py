from django.utils.dateparse import parse_date
import logging
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import SearchFilter

from .serializers import (OrderSerializer,
                          ShippingAddressSerializer,
                        CartCheckoutInputSerializer,
                        ReferralCheckoutInputSerializer,
                        OrderPreviewInputSerializer,
                        OrderPreviewOutputSerializer,
                        CustomerOrderListSerializer,
                        OrderItemSerializer,
                        OrderSummarySerializer,
                        OrderDetailSerializer,
                        OrderSerializer)

from rest_framework.generics import (ListAPIView,RetrieveAPIView,ListCreateAPIView,
                                    RetrieveUpdateDestroyAPIView)

from accounts.permissions import (IsCustomer,
                                IsAdminOrCustomer,
                                IsWarehouseStaffOrAdmin)

from delivery.permissions import IsDeliveryManOrAdmin
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from cart.models import CartItem
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import Order,OrderItem,ShippingAddress
from django.db import transaction
import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404
import logging
from .utils import (create_order_with_items,
                    validate_payment_method,
                    process_refund)

from .helpers import( validate_shipping_address,
                    prepare_order_response,
                    validate_promoter,
                    calculate_order_preview)


from delivery.permissions import IsDeliveryManOrAdmin
from django.db import models
from rest_framework.filters import OrderingFilter


def get_or_create_shipping_address(user, address_data):
    normalized = {k: v.strip() for k, v in address_data.items()}

    return ShippingAddress.objects.get_or_create(
        user=user,
        full_name=normalized["full_name"],
        phone_number=normalized["phone_number"],
        address=normalized["address"],
        locality=normalized["locality"],
        city=normalized["city"],
        district=normalized.get("district", ""),
        state=normalized["state"],
        region=normalized.get("region", ""),
        postal_code=normalized["postal_code"],
        country=normalized["country"]
    )[0]


class ReferralCheckoutAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        serializer = ReferralCheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate shipping address
        shipping_address = validate_shipping_address(user, data.get("shipping_address") or data.get("shipping_address_id"))

        # Validate promoter
        promoter = validate_promoter(request.query_params.get("ref"))

        # Validate payment method
        payment_method = validate_payment_method(data.get("payment_method"))

        # Create order
        order, razorpay_order = create_order_with_items(
            user=user,
            items=data.get("items"),
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter
        )

        return Response(prepare_order_response(order, razorpay_order), status=status.HTTP_201_CREATED if not razorpay_order else status.HTTP_200_OK)

class CartCheckoutAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(cart__user=user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CartCheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        shipping_address = validate_shipping_address(user, data.get("shipping_address") or data.get("shipping_address_id"))
        promoter = validate_promoter(data.get("referral_code"))
        payment_method = validate_payment_method(data.get("payment_method"))

        order, razorpay_order = create_order_with_items(
            user=user,
            items=cart_items,
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter
        )

        if payment_method == "Cash on Delivery":
            cart_items.delete()

        return Response(prepare_order_response(order, razorpay_order), status=status.HTTP_201_CREATED if not razorpay_order else status.HTTP_200_OK)


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
        user = request.user
        order = get_object_or_404(Order, id=id, user=user)

        if order.is_paid:
            raise ValidationError("Order is already paid")

        method = request.data.get("payment_method", "Cash on Delivery").strip()
        validate_payment_method(method)

        order.payment_method = method
        order.razorpay_payment_id = request.data.get("razorpay_payment_id")

        if method == "Cash on Delivery":
            order.status = "pending"
        else:
            order.is_paid = True
            order.paid_at = timezone.now()
            order.status = "processing"
            from promoter.utils import apply_promoter_commission
            apply_promoter_commission(order)

        order.save()
        return Response({
            "message": "Order confirmed",
            "order_id": order.id,
            "payment_method": order.payment_method,
            "is_paid": order.is_paid,
            "paid_at": order.paid_at,
            "status": order.status
        })


class CancelOrderAPIView(APIView):
    permission_classes = [IsAdminOrCustomer]

    @transaction.atomic
    def post(self, request, id):
        user = request.user
        role = getattr(user,'role',None)
        try:
            order=Order.objects.get(id=id) if role == 'admin' else Order.objects.get(id=id,user=user)
        except Order.DoesNotExist:
            raise ValidationError('order not found')

        if order.status in ["cancelled", "delivered", "shipped"]:
            return Response({"message": f"Cannot cancel order once it's {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        if order.is_paid:
            process_refund(order)
        
        for item in order.orderitem_set.all():
            product_variant=item.product_variant
            product_variant.stock += item.quantity
            product_variant.save(update_fields=["stock"])

            item.status='cancelled'
            item.save(update_fields=['status'])

        order.status = "cancelled"
        order.cancel_reason = request.data.get('cancel_reason','')
        order.cancelled_at = timezone.now()
        order.cancelled_by = user
        order.cancelled_by_role = 'admin' if role == 'admin' else 'customer'
        order.is_restocked=True
        order.save(update_fields=[
            "status", "cancel_reason", "cancelled_at",
            "cancelled_by", "cancelled_by_role",
            "is_refunded", "refunded_at", "refund_status",'refund_id','is_restocked'
        ])

        return Response(
        {
            "success": True,
            "message": "Order cancelled successfully",
            "order": {
                "id": order.id,
                "status": order.status,
                "payment_method": order.payment_method,
                "is_paid": order.is_paid,
                "is_refunded": order.is_refunded,
                "refund_status": order.refund_status if order.payment_method == "Razorpay" else None,
                "refund_id": order.refund_id if order.payment_method == "Razorpay" else None,
                "cancel_reason": order.cancel_reason,
                "cancelled_by": order.cancelled_by.email,
                "cancelled_by_role": order.cancelled_by_role,
            },
        }
    )


    
class RazorpayOrderCreateAPIView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        if order.is_paid or order.status.lower() in ["processing", "delivered", "cancelled"]:
            raise ValidationError("Cannot initiate payment for this order")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(order.total * 100),
            "currency": "INR",
            "receipt": f"order_rcptid_{order.id}",
            "payment_capture": 1
        })
        order.razorpay_order_id = razorpay_order.get("id")
        order.save()
        return Response({
            "razorpay_order_id": razorpay_order.get("id"),
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": razorpay_order.get("amount"),
            "currency": razorpay_order.get("currency"),
            "order": OrderSerializer(order).data
        })

class RazorpayPaymentVerifyAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")
        order_id = request.data.get("order_id")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, order_id]):
            raise ValidationError("Missing Razorpay payment details")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            raise ValidationError("Invalid payment signature")

        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.is_paid:
            return Response({"message": "Order already marked as paid"})

        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_order_id = razorpay_order_id
        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = "processing"
        order.payment_method = "Razorpay"
        order.save()

        from promoter.utils import apply_promoter_commission
        apply_promoter_commission(order)
        CartItem.objects.filter(cart__user=request.user).delete()

        return Response({"message": "Payment verified and order updated"})
 
class OrderItemListAPIView(ListAPIView):
    permission_classes = [IsWarehouseStaffOrAdmin]
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'order__id']
    search_fields = ['product_variant__product__name', 'order__id']

    def get_queryset(self):
        logger = logging.getLogger(__name__)
        statuses = self.request.query_params.getlist('status')
        include_cancelled = self.request.query_params.get('include_cancelled', 'false').lower() == 'true'

        # Default statuses if none provided
        if not statuses:
            statuses = ['pending', 'picked', 'packed']
            logger.info(f"No status filter provided. Defaulting to {statuses}")

        queryset = OrderItem.objects.select_related('order', 'product_variant__product')

        if include_cancelled:
            # Include items from cancelled orders
            queryset = queryset.filter(
                models.Q(status__in=statuses) | models.Q(order__status='cancelled')
            )
        else:
            # Exclude cancelled orders
            queryset = queryset.filter(
                status__in=statuses,
                order__status__in=['pending', 'processing', 'shipped']
            )

        queryset = queryset.order_by('status', 'id')

        logger.debug(f"Warehouse item list fetched by {self.request.user.email} "
                     f"with statuses: {statuses}, include_cancelled={include_cancelled}")
        return queryset



  
class OrderSummaryListAPIView(ListAPIView):
    serializer_class = OrderSummarySerializer
    permission_classes = [IsWarehouseStaffOrAdmin | IsDeliveryManOrAdmin]

    def get_queryset(self):
        user = self.request.user
        logger = logging.getLogger(__name__)
        queryset = Order.objects.all().order_by('-created_at')

        # Date range filtering
        start_date = parse_date(self.request.query_params.get('start'))
        end_date = parse_date(self.request.query_params.get('end'))
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=(start_date, end_date))
            logger.info(f"Order summary filtered by date range: {start_date} to {end_date}")

        # Status filtering
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            logger.info(f"Order summary filtered by status: {status_filter}")

        # Role-based filtering (optional: delivery staff sees only assigned orders)
        if hasattr(user, 'is_delivery_man') and user.is_delivery_man:
            queryset = queryset.filter(delivery_agent=user)
            logger.info(f"Delivery agent {user.email} viewing assigned orders only")

        return queryset

class ShippingAddressListCreateView(ListCreateAPIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        logger = logging.getLogger(__name__)

        # Optional: deduplication check
        new_data = serializer.validated_data
        existing = ShippingAddress.objects.filter(
            user=user,
            postal_code=new_data.get('postal_code'),
            locality=new_data.get('locality'),
            address=new_data.get('address'),
            city=new_data.get('city'),
            state=new_data.get('state')
        ).first()

        if existing:
            logger.info(f"Duplicate address attempt by {user.email} for pincode {new_data.get('pincode')}")
            raise ValidationError("This address already exists in your saved list.")

        serializer.save(user=user)
        logger.info(f"New shipping address created for {user.email}")

class ShippingAddressRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsCustomer]
    lookup_field = 'id'

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        logger = logging.getLogger(__name__)
        serializer.save()
        logger.info(f"Shipping address {serializer.instance.id} updated by {self.request.user.email}")

    def perform_destroy(self, instance):
        logger = logging.getLogger(__name__)
        instance.delete()
        logger.info(f"Shipping address {instance.id} deleted by {self.request.user.email}")

class BuyNowAPIView(APIView):
    permission_classes = [IsCustomer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        items = request.data.get("items", [])
        shipping_address_input = request.data.get("shipping_address") or request.data.get("shipping_address_id")
        payment_method = request.data.get("payment_method", "").strip()

        # Validate items
        if not items or not isinstance(items, list):
            return Response({"detail": "No valid items provided."}, status=status.HTTP_400_BAD_REQUEST)

        for item in items:
            if "product_variant_id" not in item or "quantity" not in item or int(item["quantity"]) <= 0:
                return Response({"detail": "Invalid items or quantity"}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address = validate_shipping_address(user, shipping_address_input)
        validate_payment_method(payment_method)

        order, razorpay_order = create_order_with_items(
            user=user,
            items=items,
            shipping_address=shipping_address,
            payment_method=payment_method
        )

        return Response(prepare_order_response(order, razorpay_order), status=status.HTTP_201_CREATED if not razorpay_order else status.HTTP_200_OK)

class OrderListAPIView(ListAPIView):
    serializer_class = CustomerOrderListSerializer
    permission_classes = [IsCustomer]
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "delivered_at", "updated_at"]
    ordering = ["-created_at"]  # default: latest first

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(user=user)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by refund status
        refunded_filter = self.request.query_params.get("is_refunded")
        if refunded_filter in ["true", "false"]:
            queryset = queryset.filter(is_refunded=(refunded_filter == "true"))

        # Filter by date range
        start_date = self.request.query_params.get("start")
        end_date = self.request.query_params.get("end")
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=(parse_date(start_date), parse_date(end_date))
            )

        return queryset

class OrderPreviewAPIView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = OrderPreviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = calculate_order_preview(data["items"], data["postal_code"])
        return Response(OrderPreviewOutputSerializer(result).data, status=status.HTTP_200_OK)


