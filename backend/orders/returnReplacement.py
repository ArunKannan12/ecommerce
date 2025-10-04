# views.py
from django.utils import timezone
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import status
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework.exceptions import NotFound
from .models import ReturnRequest, ReplacementRequest, Order,OrderStatus,OrderItem
from .returnReplacementSerializer import (
    ReturnRequestSerializer,
    ReplacementRequestSerializer,
)
from accounts.permissions import (
    IsCustomer,
    IsAdmin,
    IsWarehouseStaff,
    IsAdminOrCustomer,
)
from delivery.permissions import IsDeliveryMan
from delivery.models import DeliveryMan
from .utils import process_refund, check_refund_status


# ---------------- RETURN REQUEST ----------------

class ReturnRequestCreateAPIView(CreateAPIView):
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="pending")


class ReturnRequestUpdateAPIView(UpdateAPIView):
    queryset = ReturnRequest.objects.all() 
    serializer_class = ReturnRequestSerializer 
    def get_permissions(self): 
        role = getattr(self.request.user, 'role', None) 
        if role == 'admin': 
            return [IsAdmin()]
        elif role == 'warehouse': 
            return [IsWarehouseStaff()] 
        elif role == 'deliveryman': 
            return [IsDeliveryMan()] 
        elif role == 'customer': 
            return [IsCustomer()] 
        return super().get_permissions() 
    def perform_update(self, serializer): 
        user = self.request.user 
        role = getattr(user, 'role', None) 
        instance = serializer.instance # current return request 
        # ---------------- DELIVERYMAN ---------------- 
        if role == 'deliveryman': 
            if instance.pickup_status != 'pending': 
                raise ValidationError("You cannot update this return request at this stage.") 
            pickup_status = self.request.data.get('pickup_status') 
            if not pickup_status: 
                raise ValidationError({"pickup_status": "This field is required."}) 
            pickup_comment = self.request.data.get('pickup_comment', '') 
            deliveryman = DeliveryMan.objects.filter(user=user).first() 
            if not deliveryman: 
                raise ValidationError("This user is not linked to any delivery profile.") 
            # Save only deliveryman fields 
            instance = serializer.save( pickup_status=pickup_status, 
                                       pickup_comment=pickup_comment, 
                                       pickup_verified_by=deliveryman if pickup_status.lower() == 'collected' else None ) 
            # Optional: auto-update status 
            if pickup_status.lower() == 'collected': 
                instance.pickup_collected_at=timezone.now()
                instance.status = 'pending' 
                instance.save(update_fields=['status','pickup_collected_at']) 
                return # ---------------- WAREHOUSE ---------------- 
            elif role == 'warehouse': 
                if instance.pickup_status != 'collected': 
                    raise ValidationError("Cannot make warehouse decision until the item is collected by the deliveryman.") 
                warehouse_decision = self.request.data.get('warehouse_decision') 
                if not warehouse_decision: 
                    raise ValidationError({"warehouse_decision": "This field is required."}) 
                warehouse_comment = self.request.data.get('warehouse_comment', instance.warehouse_comment) 
                # Save only warehouse fields 
                instance = serializer.save( warehouse_decision=warehouse_decision, 
                                           warehouse_comment=warehouse_comment ) 
                instance.warehouse_processed_at=timezone.now()
                # Auto-update status and restore stock if approved 
                if warehouse_decision.lower() == 'approved': 
                    instance.status = 'approved' 
                    instance.save(update_fields=['status']) 
                    order_item = instance.order_item 
                    if order_item and order_item.product_variant: 
                        order_item.product_variant.stock += order_item.quantity 
                        order_item.product_variant.save(update_fields=['stock']) 
                        return 
                    # ---------------- ADMIN ---------------- 
                elif role == 'admin': 
                    if instance.warehouse_decision.lower() != 'approved': 
                        raise ValidationError("Admin cannot process refund until warehouse has approved the returned item.") 
                    admin_decision = self.request.data.get('admin_decision') 
                    if not admin_decision: 
                        raise ValidationError({"admin_decision": "This field is required."}) 
                    refund_amount = self.request.data.get('refund_amount', instance.refund_amount) 
                    admin_comment = self.request.data.get('admin_comment', instance.admin_comment) 
                    user_upi = self.request.data.get('user_upi') 
                    if user_upi: 
                        user_upi = user_upi.strip() 
                    else: 
                        user_upi = instance.user_upi 
                    if instance.order.payment_method.lower() in ["cod","cash on delivery"] and not user_upi: 
                        raise ValidationError("Cannot approve COD refund: user UPI address is required") 
                    # Save only admin fields 
                    instance = serializer.save( admin_decision=admin_decision, 
                                               refund_amount=refund_amount, 
                                               admin_comment=admin_comment, 
                                               user_upi=user_upi ) 
                    instance.admin_processed_at=timezone.now()
                    instance.save(update_fields=['admin_processed_at'])
                    # Trigger refund if approved 
                    if admin_decision.lower() == "approved" and instance.refund_amount and instance.refund_amount > 0: 
                        refund_id = process_refund(instance) 
                        order = instance.order 
                        order.refund_id = refund_id or f"RET-{instance.id}" 
                        if order.payment_method.lower() in ['razorpay']: 
                            order.refund_status = "pending" 
                            order.is_refunded=False 
                            order.refund_finalized=False 
                            order.refunded_at=None 
                        elif order.payment_method.lower() in ['cod','cash on delivery']: 
                            order.refund_status='pending' 
                            order.is_refunded=False 
                            order.refund_finalized=False 
                            order.refunded_at=None 
                        order.save(update_fields=[ "is_refunded", "refund_id", "refund_status", "refund_finalized", "refunded_at" ]) 
                        return 
                    # ---------------- OTHER ROLES ---------------- 
                    else:
                         # No other role can update 
                         raise PermissionDenied("You do not have permission to update this return request.") 

class ReturnRequestListAPIView(ListAPIView):
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)

        if role == "customer":
            return ReturnRequest.objects.filter(user=user).order_by("-created_at")

        elif user.is_staff or role == "admin":
            queryset = ReturnRequest.objects.all().order_by("-created_at")
            status_param = self.request.query_params.get("status")
            if status_param:
                queryset = queryset.filter(status=status_param)
            order_number = self.request.query_params.get("order_number")
            if order_number:
                queryset = queryset.filter(order__order_number=order_number)
            return queryset

        return ReturnRequest.objects.none()


# views.py
class ReturnRequestDetailAPIView(RetrieveAPIView):
    queryset = ReturnRequest.objects.all()
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        qs = ReturnRequest.objects.all()
        if role == "customer":
            return qs.filter(user=user)
        elif role == "admin" or self.request.user.is_staff:
            return qs
        return ReturnRequest.objects.none()



class RefundStatusAPIView(APIView):
    permission_classes = [IsAdminOrCustomer]

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        self.check_object_permissions(request, order)

        result = check_refund_status(order_number)
        if not result.get("success"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class ConfirmCODRefundAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)

            # Only COD
            if order.payment_method.lower() not in ["cod", "cash on delivery"]:
                return Response(
                    {"detail": "This API is only for COD refunds."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not order.refund_id:
                return Response(
                    {"detail": "No refund initiated for this order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if order.is_refunded:
                return Response(
                    {"detail": "Refund already confirmed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Mark the order as refunded
            order.mark_refunded(refund_id=order.refund_id, finalized=True)

            # Fetch all return requests related to this order
            ReturnRequest.objects.filter(order__order_number=order.order_number).update(
                status="refunded",
                refunded_at=order.refunded_at
            )

            return Response(
                {
                    "success": True,
                    "order_number": order.order_number,
                    "refund_id": order.refund_id,
                    "refund_status": order.refund_status,
                    "amount": float(order.total),
                    "refund_method": "UPI",
                    "is_refunded": order.is_refunded,
                    "refunded_at": order.refunded_at,
                    "message": "COD refund confirmed successfully.",
                },
                status=status.HTTP_200_OK,
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )


# ---------------- REPLACEMENT REQUEST ----------------

class ReplacementRequestCreateAPIView(CreateAPIView):
    serializer_class = ReplacementRequestSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="pending")


class ReplacementRequestUpdateAPIView(UpdateAPIView):
    queryset = ReplacementRequest.objects.all()
    serializer_class = ReplacementRequestSerializer

    def get_permissions(self):
        role = getattr(self.request.user, "role", None)
        if role == "admin":
            return [IsAdmin()]
        elif role == "warehouse":
            return [IsWarehouseStaff()]
        elif role == "deliveryman":
            return [IsDeliveryMan()]
        elif role == "customer":
            return [IsCustomer()]
        return super().get_permissions()

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        role = getattr(user, "role", None)
        validated_data = serializer.validated_data

        # ---------------- DELIVERYMAN ----------------
        if role == "deliveryman":
            if instance.pickup_status != "pending":
                raise ValidationError("You cannot update this replacement request at this stage.")
            pickup_status = validated_data.get("pickup_status")
            print(pickup_status,'pik')
            if not pickup_status:
                raise ValidationError({"pickup_status": "This field is required."})
            pickup_comment = validated_data.get("pickup_comment", "")

            deliveryman = DeliveryMan.objects.filter(user=user).first()
            if not deliveryman:
                raise ValidationError("This user is not linked to any delivery profile.")

            instance.pickup_status = pickup_status
            instance.pickup_comment = pickup_comment
            instance.pickup_verified_by = deliveryman if pickup_status.lower() == "collected" else None

            # Optional: auto-update status
            if pickup_status.lower() == "collected":
                instance.status = "shipped"
                instance.shipped_at = timezone.now()

            instance.save(update_fields=["pickup_status", "pickup_comment", "pickup_verified_by", "status", "shipped_at"])
            return

        # ---------------- WAREHOUSE ----------------
        elif role == "warehouse":
            if instance.pickup_status.lower() != "collected":
                raise ValidationError("Cannot make warehouse decision until the item is collected by the deliveryman.")

            warehouse_decision = validated_data.get("warehouse_decision")
            if not warehouse_decision:
                raise ValidationError({"warehouse_decision": "This field is required."})
            warehouse_comment = validated_data.get("warehouse_comment", instance.warehouse_comment)

            instance.warehouse_decision = warehouse_decision
            instance.warehouse_comment = warehouse_comment

            if warehouse_decision.lower() == "approved":
                instance.status = "approved"

            instance.save(update_fields=["warehouse_decision", "warehouse_comment", "status"])
            return

        # ---------------- ADMIN ----------------
        elif role == "admin":
            if instance.warehouse_decision.lower() != "approved":
                raise ValidationError("Admin cannot approve replacement until warehouse has approved the returned item.")

            admin_decision = validated_data.get("admin_decision")
            if not admin_decision:
                raise ValidationError({"admin_decision": "This field is required."})
            admin_comment = validated_data.get("admin_comment", instance.admin_comment)

            instance.admin_decision = admin_decision
            instance.admin_comment = admin_comment

            # Create replacement order if approved and not already created
            if admin_decision.lower() == "approved" and not instance.new_order:
                old_item = instance.order_item
                subtotal = old_item.price * old_item.quantity
                total = subtotal + instance.order.delivery_charge

                new_order = Order.objects.create(
                    user=instance.user,
                    shipping_address=instance.order.shipping_address,
                    subtotal=subtotal,
                    total=total,
                    delivery_charge=Decimal('0.00'),  # 🚚 free for replacements
                    is_paid=True,  
                    paid_at=timezone.now(),  # 💰 mark as already paid
                    payment_method=instance.order.payment_method,
                    status=OrderStatus.PENDING,
                    promoter=None,                # ❌ no promoter
                    commission=Decimal('0.00'),   # ❌ no commission
                    commission_applied=True,      # mark it so calc won’t run
                )

                OrderItem.objects.create(
                    order=new_order,
                    product_variant=old_item.product_variant,
                    quantity=old_item.quantity,
                    price=old_item.price,
                )

                instance.new_order = new_order
            else:
                new_order=instance.new_order
                if not new_order.is_paid:
                    new_order.is_paid = True
                    new_order.paid_at = timezone.now()
                    new_order.status = OrderStatus.PROCESSING
                    new_order.save(update_fields=["is_paid", "paid_at", "status"])

            instance.save(update_fields=["admin_decision", "admin_comment", "new_order"])
            return

        # ---------------- OTHER ROLES ----------------
        else:
            raise PermissionDenied("You do not have permission to update this replacement request.")


class ReplacementRequestListAPIView(ListAPIView):
    serializer_class = ReplacementRequestSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)

        qs = ReplacementRequest.objects.all().order_by("-created_at")

        if role == "customer":
            return qs.filter(user=user)
        elif user.is_staff or role == "admin":
            return qs
        return ReplacementRequest.objects.none()


class ReplacementRequestDetailAPIView(RetrieveAPIView):
    serializer_class = ReplacementRequestSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)

        qs = ReplacementRequest.objects.all()
        if role == "customer":
            return qs.filter(user=user)
        elif user.is_staff or role == "admin":
            return qs
        return ReplacementRequest.objects.none()
