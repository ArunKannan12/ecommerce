from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter    
from orders.serializers import OrderItemSerializer,OrderSummarySerializer,OrderDetailSerializer,OrderSerializer
from .serializers import OrderSerializer,ShippingAddressSerializer,CartCheckoutInputSerializer,ShippingAddressInputSerializer,ReferralCheckoutInputSerializer,CustomerOrderListSerializer
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
import logging
from decimal import Decimal
from products.models import ProductVariant
from .utils import create_order_with_items,update_order_status_from_items,get_pincode_details,update_item_status
from datetime import timedelta
from django.utils import timezone
from delivery.permissions import IsDeliveryManOrAdmin


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

        items = data.get("items")
        payment_method = data.get("payment_method")

        # Step 1: Validate shipping address
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

            # Autofill state/district from pincode
            details = get_pincode_details(shipping_data["postal_code"])
            shipping_data["state"] = details["state"]
            shipping_data["district"] = details["district"]

            # Validate locality against pincode
            valid_localities = [loc for loc, _ in details["localities"]]
            if shipping_data["locality"] not in valid_localities:
                raise ValidationError({"locality": "Invalid locality for this pincode."})

            shipping_address = get_or_create_shipping_address(user, shipping_data)

        # Step 2: Validate referral code
        promoter = None
        referral_code = request.query_params.get('ref')
        if referral_code:
            promoter = Promoter.objects.filter(
                referral_code=referral_code,
                application_status="approved"
            ).first()
            if not promoter:
                raise ValidationError({"referral_code": "Invalid or inactive referral code."})

        # Step 3: Validate payment method
        if payment_method not in ["Cash on Delivery", "Razorpay"]:
            raise ValidationError({"payment_method": "Invalid payment method."})

        # Step 4: Create order
        order, razorpay_order = create_order_with_items(
            user=user,
            items=items,
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter
        )

        # Step 5: Attach Razorpay metadata if applicable
        if razorpay_order:
            order.razorpay_order_id = razorpay_order.get("id")
            order.save()
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
        cart_items = CartItem.objects.filter(cart__user=user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CartCheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Step 1: Handle shipping address
        shipping_address = None
        if data.get("shipping_address_id"):
            try:
                shipping_address = ShippingAddress.objects.get(id=data["shipping_address_id"], user=user)
            except ShippingAddress.DoesNotExist:
                raise ValidationError({"shipping_address_id": "Invalid address for this user."})
        else:
            shipping_input = data.get("shipping_address")
            if not shipping_input:
                raise ValidationError({"shipping_address": "This field is required."})

            # Autofill state/district from pincode
            details = get_pincode_details(shipping_input["postal_code"])
            shipping_input["state"] = details["state"]
            shipping_input["district"] = details["district"]

            # Validate locality
            valid_localities = [loc for loc, _ in details["localities"]]
            if shipping_input["locality"] not in valid_localities:
                raise ValidationError({"locality": "Invalid locality for this pincode."})

            shipping_address = get_or_create_shipping_address(user, shipping_input)

        # Step 2: Handle referral code
        promoter = None
        referral_code = data.get("referral_code")
        if referral_code:
            promoter = Promoter.objects.filter(
                referral_code=referral_code,
                application_status="approved"
            ).first()
            if not promoter:
                raise ValidationError({"referral_code": "Invalid or inactive referral code."})

        # Step 3: Validate payment method
        payment_method = data.get("payment_method")
        if payment_method not in ["Cash on Delivery", "Razorpay"]:
            raise ValidationError({"payment_method": "Invalid payment method."})

        # Step 4: Create order
        order, razorpay_order = create_order_with_items(
            user=user,
            shipping_address=shipping_address,
            payment_method=payment_method,
            promoter=promoter,
            items=cart_items
        )

        # Step 5: Clear cart if COD
        if payment_method == "Cash on Delivery":
            cart_items.delete()

        # Step 6: Prepare response
        if razorpay_order:
            order.razorpay_order_id = razorpay_order.get("id")
            order.save()
            return Response({
                "order_id": razorpay_order.get("id"),
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": razorpay_order.get("amount"),
                "currency": razorpay_order.get("currency"),
                "order": OrderSerializer(order).data
            }, status=status.HTTP_200_OK)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


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
        order = Order.objects.get(id=id, user=user)

        if order.is_paid:
            raise ValidationError('Order is already paid')

        method = request.data.get('payment_method', 'Cash on Delivery').strip()
        if method not in ['Cash on Delivery', 'Razorpay']:
            raise ValidationError('Invalid payment method')

        order.payment_method = method
        order.razorpay_payment_id = request.data.get("razorpay_payment_id")

        if method == 'Cash on Delivery':
            order.status = 'pending'
        else:
            order.is_paid = True
            order.paid_at = timezone.now()
            order.status = 'processing'
            apply_promoter_commission(order)

        order.save()
        return Response({
            'message': 'Order confirmed',
            'order_id': order.id,
            'payment_method': order.payment_method,
            'is_paid': order.is_paid,
            'paid_at': order.paid_at,
            'status': order.status
        }, status=status.HTTP_200_OK)

class CancelOrderAPIView(APIView):
    permission_classes = [IsAdminOrCustomer]

    @transaction.atomic
    def post(self, request, id):
        user = request.user
        try:
            order = Order.objects.get(id=id) if user.is_staff else Order.objects.get(id=id, user=user)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")

        if order.status == 'cancelled':
            return Response({'message': 'Order is already cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status in ['delivered', 'shipped']:
            return Response({'message': f"Cannot cancel order once it's {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('cancel_reason', '')

        # Refund logic for Razorpay
        if order.is_paid and order.payment_method == "Razorpay":
            if not order.razorpay_payment_id:
                raise ValidationError("Cannot process refund: Razorpay payment ID missing")

            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                refund = client.payment.refund(order.razorpay_payment_id, {
                    "amount": int(order.total * 100),
                    "notes": {
                        "reason": reason,
                        "cancelled_by": str(user)
                    }
                })
                order.refund_id = refund.get("id")
                order.refund_status = refund.get("status")
                order.refunded_at = timezone.now()
                order.refund_reason = reason
                order.is_refunded = True
            except Exception as e:
                order.refund_status = 'failed'
                order.save()
                logger = logging.getLogger(__name__)
                logger.error(f"Refund failed for order {order.id} by {user.email}. Error: {str(e)}")
                return Response({
                    'message': 'Order cancelled, but refund failed',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Final cancellation update
        order.status = 'cancelled'
        order.cancel_reason = reason
        order.cancelled_at = timezone.now()
        order.cancelled_by = user
        order.cancelled_by_role = "admin" if user.is_staff else "customer"
        order.save()  # triggers restock_items() if needed

        response_data = {'message': 'Order cancelled successfully'}

        if user.is_staff:
            # Include restocked items only if restocking occurred
            restocked_items = []
            for item in order.orderitem_set.all():
                restocked_items.append({
                    "variant": str(item.product_variant),
                    "restocked_quantity": item.quantity
                })
            response_data['restocked_items'] = restocked_items

        return Response(response_data, status=status.HTTP_200_OK)
class RazorpayOrderCreateAPIView(APIView):
    permission_classes=[IsCustomer]

    def post(self,request,id):
        try:
            order=Order.objects.get(id=id,user=self.request.user)

        except Order.DoesNotExist:
            raise ValidationError("order not found")
        if order.is_paid:
            raise ValidationError('Order is already paid')
        if order.status in ['processing','delivered']:
            raise ValidationError("Cannot initiate payment for an already  processed order")
        if order.status.lower() == 'cancelled':
            raise ValidationError('Cannot pay for a cancelled order')
        
        client=razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        razorpay_order=client.order.create({
            'amount':int(order.total * 100),
            'currency':'INR',
            'receipt':f"order_rcptid_{order.id}",
            'payment_capture':1
        })
        order.razorpay_order_id=razorpay_order.get('id')
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

    @transaction.atomic
    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_id = request.data.get('order_id')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, order_id]):
            raise ValidationError("Missing Razorpay payment details")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        logger = logging.getLogger(__name__)

        # Step 1: Verify signature
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            logger.warning(f"Signature verification failed for order {order_id}")
            raise ValidationError("Invalid payment signature")

        # Step 2: Fetch and validate order
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            raise ValidationError("Order not found")

        if order.is_paid:
            logger.info(f"Repeated payment verification attempt for order {order.id} by {request.user.email}")
            return Response({'message': 'Order already marked as paid'}, status=status.HTTP_200_OK)

        # Step 3: Mark order as paid
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_order_id = razorpay_order_id
        order.is_paid = True
        order.paid_at = timezone.now()
        order.status = 'processing'
        order.payment_method = 'Razorpay'
        order.refund_reason = None  # Clear any stale refund intent
        order.save()

        # Step 4: Apply commission and clear cart
        apply_promoter_commission(order)
        CartItem.objects.filter(cart__user=request.user).delete()

        logger.info(f"Payment verified for order {order.id} by {request.user.email}")
        return Response({'message': 'Payment verified and order updated'}, status=status.HTTP_200_OK)
class RefundStatusAPIView(APIView):
    permission_classes = [IsAdminOrCustomer]

    @transaction.atomic
    def get(self, request, id):
        user = request.user
        logger = logging.getLogger(__name__)

        # Fetch order based on role
        try:
            order = Order.objects.get(id=id) if user.is_staff else Order.objects.get(id=id, user=user)
        except Order.DoesNotExist:
            logger.warning(f"Refund status check failed: Order {id} not found for user {user.email}")
            raise ValidationError("Order not found")

        # No refund initiated
        if not order.refund_id:
            logger.info(f"No refund initiated for order {order.id} by {user.email}")
            return Response({
                "message": "No refund has been initiated for this order.",
                "order_status": order.status,
                "is_paid": order.is_paid,
                "payment_method": order.payment_method
            }, status=status.HTTP_200_OK)

        # Refund info response
        return Response({
            "order_id": order.id,
            "refund_id": order.refund_id,
            "refund_status": order.refund_status,
            "refunded_at": order.refunded_at,
            "payment_method": order.payment_method,
            "is_paid": order.is_paid,
            "cancel_reason": order.cancel_reason,
            "refund_reason": order.refund_reason
        }, status=status.HTTP_200_OK)


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
    
class OrderItemListAPIView(ListAPIView):
    permission_classes = [IsWarehouseStaffOrAdmin]
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'order__id']
    search_fields = ['product_variant__product__name', 'order__id']

    def get_queryset(self):
        logger = logging.getLogger(__name__)
        statuses = self.request.query_params.getlist('status')

        if not statuses:
            statuses = ['pending', 'picked', 'packed']
            logger.info(f"No status filter provided. Defaulting to {statuses}")

        queryset = OrderItem.objects.filter(status__in=statuses).select_related(
            'order', 'product_variant__product'
        ).order_by('status', 'id')

        logger.debug(f"Warehouse item list fetched by {self.request.user.email} with statuses: {statuses}")
        return queryset
from django.utils.dateparse import parse_date
  
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

    def post(self, request):
        user = request.user
        items = request.data.get("items", [])
        shipping_address_data = request.data.get("shipping_address")
        payment_method = request.data.get("payment_method", "").strip().title()
        logger = logging.getLogger(__name__)

        # Validate items
        if not items or not isinstance(items, list):
            return Response({"detail": "No valid items provided."}, status=status.HTTP_400_BAD_REQUEST)

        for item in items:
            if "product_variant_id" not in item or "quantity" not in item:
                return Response({"detail": "Each item must have product_variant_id and quantity."},
                                status=status.HTTP_400_BAD_REQUEST)
            if int(item["quantity"]) <= 0:
                return Response({"detail": "Quantity must be greater than 0."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Validate shipping address
        if not shipping_address_data:
            return Response({"detail": "Shipping address is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if isinstance(shipping_address_data, int):
                shipping_address = get_object_or_404(ShippingAddress, id=shipping_address_data, user=user)
            elif isinstance(shipping_address_data, dict):
                # Optional: deduplication check
                existing = ShippingAddress.objects.filter(
                    user=user,
                    pincode=shipping_address_data.get("pincode"),
                    locality=shipping_address_data.get("locality"),
                    address_line=shipping_address_data.get("address_line"),
                    city=shipping_address_data.get("city"),
                    state=shipping_address_data.get("state")
                ).first()
                shipping_address = existing or ShippingAddress.objects.create(user=user, **shipping_address_data)
            else:
                return Response({"detail": "Invalid shipping address format."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.warning(f"Shipping address error for user {user.email}: {str(e)}")
            return Response({"detail": "Failed to process shipping address."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate payment method
        if payment_method not in ["Razorpay", "Cash On Delivery", "Wallet"]:
            return Response({"detail": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                order, razorpay_order = create_order_with_items(
                    user=user,
                    items=items,
                    shipping_address=shipping_address,
                    payment_method=payment_method
                )

                if razorpay_order:
                    order.razorpay_order_id = razorpay_order.get("id")
                    order.save(update_fields=["razorpay_order_id"])

                logger.info(f"Order {order.id} created by {user.email} with payment method {payment_method}")

        except Exception as e:
            logger.error(f"Order creation failed for {user.email}: {str(e)}")
            return Response({"detail": "Order creation failed. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order)
        data = serializer.data
        if razorpay_order:
            data["razorpay_order"] = razorpay_order

        return Response(data, status=status.HTTP_201_CREATED)
    
class OrderListAPIView(ListAPIView):
    serializer_class = CustomerOrderListSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        user = self.request.user
        logger = logging.getLogger(__name__)
        queryset = Order.objects.filter(user=user).order_by('-created_at')

        # Optional: filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            logger.info(f"User {user.email} filtered orders by status: {status_filter}")

        # Optional: filter by date range
        start_date = parse_date(self.request.query_params.get('start'))
        end_date = parse_date(self.request.query_params.get('end'))
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=(start_date, end_date))
            logger.info(f"User {user.email} filtered orders from {start_date} to {end_date}")

        return queryset