from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from .models import ShippingAddress
from products.models import ProductVariant
from promoter.models import Promoter
from .utils import  calculate_delivery_charge


def validate_shipping_address(user, shipping_input):
    """
    Validate or create a ShippingAddress object.
    Accepts either:
      - an integer (existing address ID)
      - a dict (new address data, already validated by frontend)
    """
    if isinstance(shipping_input, int):
        # Existing saved address
        return get_object_or_404(ShippingAddress, id=shipping_input, user=user)

    elif isinstance(shipping_input, dict):
        # ✅ Trust frontend for pincode → state/district/locality mapping
        required_fields = ["postal_code", "locality", "address", "city", "state"]
        missing = [f for f in required_fields if not shipping_input.get(f)]
        if missing:
            raise ValidationError({"shipping_address": f"Missing fields: {', '.join(missing)}"})

        # Check if identical address already exists for user
        existing = ShippingAddress.objects.filter(
            user=user,
            postal_code=shipping_input.get("postal_code"),
            locality=shipping_input.get("locality"),
            address=shipping_input.get("address"),
            city=shipping_input.get("city"),
            state=shipping_input.get("state")
        ).first()

        return existing or ShippingAddress.objects.create(user=user, **shipping_input)

    else:
        raise ValidationError({"shipping_address": "Invalid format"})


def validate_promoter(referral_code):
    """Return promoter object if valid, else None."""
    if not referral_code:
        return None

    promoter = Promoter.objects.filter(
        referral_code=referral_code,
        application_status="approved"
    ).first()

    if not promoter:
        raise ValidationError({"referral_code": "Invalid or inactive referral code."})

    return promoter


def validate_payment_method(method):
    """Ensure payment method is valid."""
    valid_methods = ["Cash on Delivery", "Razorpay", "Wallet"]
    if method not in valid_methods:
        raise ValidationError({"payment_method": "Invalid payment method."})
    return method


def prepare_order_response(order, razorpay_order=None):
    from .serializers import OrderSerializer
    from django.conf import settings

    order_data = OrderSerializer(order).data
    order_data.update({
        "subtotal": str(order.subtotal),
        "delivery_charge": str(order.delivery_charge),
        "total": str(order.total)
    })

    response = {"order": order_data}

    if razorpay_order:
        response.update({
            "razorpay_order_id": razorpay_order.get("id"),
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": razorpay_order.get("amount"),
            "currency": razorpay_order.get("currency"),
        })

    return response



def calculate_order_preview(items, postal_code=None, shipping_address_id=None):
    """
    Calculate subtotal, delivery charge, and total for a preview.
    Items: list of dicts with 'product_variant_id' and 'quantity'.
    postal_code: optional string
    shipping_address_id: optional, use saved address if provided
    """
    subtotal = Decimal("0.00")

    for item in items:
        try:
            variant = ProductVariant.objects.get(id=item["product_variant_id"])
        except ProductVariant.DoesNotExist:
            raise ValidationError(
                {"items": f"ProductVariant with id {item['product_variant_id']} does not exist"}
            )
        price = variant.offer_price if variant.offer_price else variant.base_price
        subtotal += price * item["quantity"]

    # Delivery charge is no longer applicable
    delivery_charge =calculate_delivery_charge(subtotal)

    return {
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "total": subtotal + delivery_charge,
    }
