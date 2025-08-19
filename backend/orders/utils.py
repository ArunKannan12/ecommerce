# orders/utils.py
from django.utils import timezone
from .models import OrderItem,Order
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from products.models import ProductVariant
import razorpay
from django.conf import settings
import logging


logger=logging.getLogger(__name__)
def create_order_with_items(user, items, shipping_address, payment_method, promoter=None):
    order = Order.objects.create(
        user=user,
        shipping_address=shipping_address,
        total=Decimal("0.00"),
        payment_method=payment_method,
        is_paid=False,
        promoter=promoter
    )

    total_price = Decimal("0.00")

    for item in items:
        if isinstance(item, dict):
            variant_id = item.get("product_variant_id")
            quantity = int(item.get("quantity", 1))
            if not variant_id:
                raise ValidationError("Missing product_variant_id in item.")
            variant = get_object_or_404(ProductVariant, id=variant_id)
        else:
            # It's a CartItem instance
            variant = item.product_variant
            quantity = item.quantity

        if variant.stock < quantity:
            raise ValidationError(f"Not enough stock for {variant}")

        variant.stock -= quantity
        variant.save()

        item_total = variant.product.price * quantity
        total_price += item_total

        OrderItem.objects.create(
            order=order,
            product_variant=variant,
            quantity=quantity,
            price=variant.product.price
        )

    order.total = total_price
    order.save()

    razorpay_order = None
    if payment_method == "Razorpay":
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': int(total_price * 100),  # Convert to paise
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
    item_statuses = order.orderitem_set.values_list('status', flat=True)

    if all(status == 'shipped' for status in item_statuses):
        order.status = 'shipped'
        order.shipped_at = timezone.now()

    elif all(status in ['picked', 'packed'] for status in item_statuses):
        order.status = 'processing'

    elif any(status in ['picked', 'packed'] for status in item_statuses):
        order.status = 'processing'

    else:
        order.status = 'pending'

    order.save(update_fields=['status', 'shipped_at'])



# utils/pincode.py

import requests

def get_pincode_details(pincode):
    try:
        response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}")
        data = response.json()

        if not data or data[0]['Status'] != 'Success':
            return {
                "localities": [],
                "state": None,
                "district": None
            }

        post_offices = data[0].get('PostOffice', [])
        localities = [(po['Name'], po['Name']) for po in post_offices if 'Name' in po]

        # Extract state and district from the first post office
        state = post_offices[0].get('State')
        district = post_offices[0].get('District')

        return {
            "localities": localities,
            "state": state,
            "district": district
        }

    except Exception:
        return {
            "localities": [],
            "state": None,
            "district": None
        }
    
def update_item_status(item_id, expected_status, new_status, user, timestamp_field=None):
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

    logger = logging.getLogger(__name__)
    logger.info(f"Item {item.id} marked as {new_status} by {user.email}")
    return item
