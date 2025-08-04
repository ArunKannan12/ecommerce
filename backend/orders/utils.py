# orders/utils.py
from django.utils import timezone
from .models import OrderItem,Order
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from products.models import ProductVariant
import razorpay
from django.conf import settings

def create_order_with_items(user, items, shipping_address, payment_method, promoter=None):
    order = Order.objects.create(
        user=user,
        shipping_address=shipping_address,
        total=0,
        payment_method=payment_method,
        is_paid=False,
        promoter=promoter
    )

    total_price = Decimal("0.00")

    for item in items:
        if isinstance(item, dict):
            variant_id = item.get("product_variant_id")
            quantity = item.get("quantity", 1)
            if not variant_id:
                raise ValidationError("Missing product_variant_id in item.")
            variant = get_object_or_404(ProductVariant, id=variant_id)
        else:
            # It's a CartItem
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
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            'amount': int(total_price * 100),
            'currency': 'INR',
            'receipt': f"order_rcptid_{order.id}",
            'payment_capture': 1
        })
        order.tracking_number = razorpay_order.get('id')
        order.save()

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
