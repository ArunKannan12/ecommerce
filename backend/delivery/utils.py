from collections import OrderedDict

def build_orders_dict(order_items_qs):
    """
    Converts a queryset of OrderItems into a grouped dictionary by order
    suitable for API responses.
    """
    orders_dict = OrderedDict()
    for item in order_items_qs:
        order = item.order
        if order.id not in orders_dict:
            shipping_address = getattr(order, "shipping_address", None)
            orders_dict[order.id] = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "customer_name": order.user.get_full_name() or order.user.email,
                "assigned_at": order.assigned_at,
                "shipping_address": {
                    "full_name": getattr(shipping_address, "full_name", ""),
                    "phone_number": getattr(shipping_address, "phone_number", ""),
                    "address": getattr(shipping_address, "address", ""),
                    "locality": getattr(shipping_address, "locality", ""),
                    "city": getattr(shipping_address, "city", ""),
                    "district": getattr(shipping_address, "district", ""),
                    "state": getattr(shipping_address, "state", ""),
                    "region": getattr(shipping_address, "region", ""),
                    "postal_code": getattr(shipping_address, "postal_code", ""),
                    "country": getattr(shipping_address, "country", "India")
                },
                "items": []
            }

        orders_dict[order.id]["items"].append({
            "id": item.id,
            "product_name": getattr(item.product_variant, "variant_name", ""),
            "status": item.status,
            "pending_otp": not item.notifications.filter(event="otp_delivery", otp_verified=True).exists()
        })

    return list(orders_dict.values())
