from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from .models import ShippingAddress
from products.models import ProductVariant
from promoter.models import Promoter
from promoter.utils import apply_promoter_commission
from cart.models import CartItem
from .utils import  calculate_delivery_charge,create_order_with_items
from django.conf import settings
import razorpay
from django.utils import timezone


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
        "order_number":order.order_number,
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


def verify_razorpay_payment(order, razorpay_order_id, razorpay_payment_id, razorpay_signature, user, client):
    """
    Verifies Razorpay payment signature and updates the order.
    """
    if order.is_paid:
        return {
            "message": "Order already marked as paid",
            "order_number": order.order_number,
            "status": order.status,
            "is_paid": order.is_paid
        }

    # Verify Razorpay signature
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise ValidationError("Invalid payment signature")

    # Update order
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_order_id = razorpay_order_id
    order.is_paid = True
    order.paid_at = timezone.now()
    order.status = "processing"
    order.payment_method = "Razorpay"
    order.save()

    # Apply promoter commission
    apply_promoter_commission(order)

    # Clear cart items if any
    CartItem.objects.filter(cart__user=user).delete()

    return {
        "message": "Payment verified and order updated",
        "order_number": order.order_number,
        "status": order.status,
        "is_paid": order.is_paid
    }


def process_checkout(
    user,
    items=None,
    shipping_address_input=None,
    payment_method=None,
    promoter_code=None,
    is_cart=False,
    existing_order=None
):
    """
    Unified checkout handler for:
    - Referral checkout
    - Cart checkout
    - Buy Now
    - Existing order payment (existing_order)
    
    Returns a dict with keys:
    - 'order': the Order instance
    - 'response': the serialized response dict for API
    """
    razorpay_order = None  # ensure defined

    # ---------------- Handle existing order ----------------
    if existing_order:
        order = existing_order

        # Update payment method if provided and different
        if payment_method and order.payment_method != payment_method:
            validate_payment_method(payment_method)
            order.payment_method = payment_method
            order.save(update_fields=["payment_method"])

        # Create Razorpay order only if unpaid and method is Razorpay
        if not order.is_paid and order.payment_method == "Razorpay":
            if not order.razorpay_order_id:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    "amount": int(order.total * 100),
                    "currency": "INR",
                    "receipt": f"order_rcptid_{order.order_number}",
                    "payment_capture": 1
                })
                order.razorpay_order_id = razorpay_order.get("id")
                order.save(update_fields=["razorpay_order_id"])
            else:
                # reuse existing Razorpay order id
                razorpay_order = {
                    "id": order.razorpay_order_id,
                    "amount": int(order.total * 100),
                    "currency": "INR"
                }

        response_data = prepare_order_response(order, razorpay_order)
        return {"order": order, "response": response_data}

    # ---------------- New order creation ----------------
    shipping_address = validate_shipping_address(user, shipping_address_input)
    promoter = validate_promoter(promoter_code) if promoter_code else None
    validate_payment_method(payment_method)

    order, _ = create_order_with_items(
        user=user,
        items=items,
        shipping_address=shipping_address,
        payment_method=payment_method,
        promoter=promoter
    )

    # ---------------- Handle Cash on Delivery ----------------
    if order.payment_method == "Cash on Delivery":
        order.status = "pending"
        order.is_paid = False
        order.save(update_fields=["status", "is_paid", "payment_method"])

        if is_cart and items:
            items.delete()

        response_data = prepare_order_response(order, razorpay_order=None)
        return {"order": order, "response": response_data}

    # ---------------- Razorpay handling for new orders ----------------
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": int(order.total * 100),
        "currency": "INR",
        "receipt": f"order_rcptid_{order.order_number}",
        "payment_capture": 1
    })
    order.razorpay_order_id = razorpay_order.get("id")
    order.save(update_fields=["razorpay_order_id", "payment_method"])

    response_data = prepare_order_response(order, razorpay_order)
    return {"order": order, "response": response_data}
