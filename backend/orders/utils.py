# orders/utils.py
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
import razorpay
from django.conf import settings

from .models import Order, OrderItem, ShippingAddress
from products.models import ProductVariant
from promoter.models import Promoter
from cart.models import CartItem


from .serializers import OrderSerializer

logger = logging.getLogger(__name__)



def get_or_create_shipping_address(user, shipping_data):
    """Validate and get or create shipping address."""
    normalized = {k: v.strip() if isinstance(v, str) else v for k, v in shipping_data.items()}

    return ShippingAddress.objects.get_or_create(
        user=user,
        full_name=normalized["full_name"],
        phone_number=normalized["phone_number"],
        address=normalized["address"],
        locality=normalized["locality"],
        city=normalized["city"],
        district=normalized.get("district", ""),
        state=normalized.get("state", ""),
        region=normalized.get("region", ""),
        postal_code=normalized["postal_code"],
        country=normalized.get("country", "India")
    )[0]


def get_valid_promoter(referral_code):
    """Validate promoter referral code."""
    if not referral_code:
        return None
    promoter = Promoter.objects.filter(referral_code=referral_code, application_status="approved").first()
    if not promoter:
        raise ValidationError({"referral_code": "Invalid or inactive referral code."})
    return promoter


def validate_payment_method(method):
    """Validate payment method."""
    if method not in ["Cash on Delivery", "Razorpay"]:
        raise ValidationError({"payment_method": "Invalid payment method."})
    return method


def clear_user_cart(user):
    """Clear all cart items for the user."""
    CartItem.objects.filter(cart__user=user).delete()


def format_razorpay_response(razorpay_order, order):
    """Return standardized Razorpay response."""
    return {
        "order_id": razorpay_order.get("id"),
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": razorpay_order.get("amount"),
        "currency": razorpay_order.get("currency"),
        "order": OrderSerializer(order).data
    }


# -----------------------------
# Order Creation & Updates
# -----------------------------
def create_order_with_items(user, items, shipping_address, payment_method, promoter=None):
    """Create an Order and associated OrderItems, handle stock and Razorpay."""
    order = Order.objects.create(
        user=user,
        shipping_address=shipping_address,
        subtotal=Decimal("0.00"),
        delivery_charge=Decimal("0.00"),
        total=Decimal("0.00"),
        payment_method=payment_method,
        is_paid=False,
        promoter=promoter
    )

    subtotal = Decimal("0.00")

    for item in items:
        if isinstance(item, dict):
            variant_id = item.get("product_variant_id")
            quantity = int(item.get("quantity", 1))
            if not variant_id:
                raise ValidationError("Missing product_variant_id in item.")
            variant = get_object_or_404(ProductVariant, id=variant_id)
        else:
            variant = item.product_variant
            quantity = item.quantity

        if variant.stock < quantity:
            raise ValidationError(f"Not enough stock for {variant}")

        variant.stock -= quantity
        variant.save()

        price = variant.offer_price if variant.offer_price else variant.base_price
        subtotal += price * quantity

        OrderItem.objects.create(
            order=order,
            product_variant=variant,
            quantity=quantity,
            price=price
        )

    delivery_charge = calculate_delivery_charge(subtotal, shipping_address)
    order.subtotal = subtotal
    order.delivery_charge = delivery_charge
    order.total = subtotal + delivery_charge
    order.save()

    razorpay_order = None
    if payment_method == "Razorpay":
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': int(order.total * 100),
                'currency': 'INR',
                'receipt': f"order_rcptid_{order.id}",
                'payment_capture': 1
            })
            order.tracking_number = razorpay_order.get('id')
            order.save()
            logger.info(f"Razorpay order created: {razorpay_order.get('id')} for Order {order.id}")
        except Exception as e:
            logger.error(f"Razorpay order creation failed for Order {order.id}: {str(e)}")
            raise ValidationError(f"Razorpay order creation failed: {str(e)}")

    return order, razorpay_order


def update_order_status_from_items(order):
    """Update order status based on associated item statuses."""
    item_statuses = order.orderitem_set.values_list('status', flat=True)

    if all(status == 'shipped' for status in item_statuses):
        order.status = 'shipped'
        order.shipped_at = timezone.now()
    elif any(status in ['picked', 'packed'] for status in item_statuses):
        order.status = 'processing'
    else:
        order.status = 'pending'

    order.save(update_fields=['status', 'shipped_at'])


def update_item_status(item_id, expected_status, new_status, user, timestamp_field=None):
    """Mark an OrderItem as picked/packed/shipped."""
    try:
        item = OrderItem.objects.get(id=item_id)
    except OrderItem.DoesNotExist:
        raise ValidationError("Item not found")

    if item.status != expected_status:
        raise ValidationError(f"Only items with status '{expected_status}' can be marked as '{new_status}'")

    item.status = new_status
    if timestamp_field:
        setattr(item, timestamp_field, timezone.now())
    item.save(update_fields=['status'] + ([timestamp_field] if timestamp_field else []))

    update_order_status_from_items(item.order)
    logger.info(f"Item {item.id} marked as {new_status} by {user.email}")
    return item


# -----------------------------
# Delivery Charge Calculation
# -----------------------------
def calculate_delivery_charge(subtotal,shipping_address=None):
    """
    Simple flat delivery charge rule:
    - subtotal >= 500 → free delivery
    - subtotal < 500 → ₹50 delivery charge
    """
    if subtotal >= 500:
        return Decimal("0.00")
    return Decimal("50.00")


def calculate_order_totals(items, shipping_address=None):
    """Calculate subtotal, delivery charge, and total for a list of items."""
    subtotal = Decimal("0.00")

    for item in items:
        if isinstance(item, dict):
            variant_id = item.get("product_variant_id")
            quantity = int(item.get("quantity", 1))
            if not variant_id or quantity <= 0:
                continue
            variant = ProductVariant.objects.filter(id=variant_id, is_active=True).first()
            if not variant:
                continue
            price = variant.offer_price if variant.offer_price else variant.base_price
            subtotal += price * quantity
        else:
            variant = getattr(item, "product_variant", None)
            quantity = getattr(item, "quantity", 1)
            if not variant:
                continue
            price = variant.offer_price if variant.offer_price else variant.base_price
            subtotal += price * quantity

    delivery_charge = calculate_delivery_charge(subtotal)
    total = subtotal + delivery_charge

    return {"subtotal": subtotal, "delivery_charge": delivery_charge, "total": total}
