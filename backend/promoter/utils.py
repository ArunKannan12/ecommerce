from promoter.models import PromoterCommission

def apply_promoter_commission(order):
    promoter = order.promoter

    if not promoter or order.commission_applied or promoter.application_status.lower() != 'approved':
        return

    total_commission = 0

    for item in order.orderitem_set.all():
        variant = item.product_variant
        rate = variant.promoter_commission_rate or 0  # Correct source

        if rate > 0:
            commission_amount = item.quantity * item.price * (rate / 100)

            PromoterCommission.objects.create(
                promoter=promoter,
                order=order,
                product_variant=variant,
                amount=commission_amount
            )

            total_commission += commission_amount

    # Update promoter stats
    promoter.total_sales_count += 1
    promoter.total_commission_earned += total_commission
    promoter.wallet_balance += total_commission
    promoter.is_eligible_for_withdrawal = promoter.wallet_balance >= 500
    promoter.save(update_fields=[
        'total_sales_count',
        'total_commission_earned',
        'wallet_balance',
        'is_eligible_for_withdrawal'
    ])

    # Mark commission as applied
    order.commission_applied = True
    order.commission = total_commission
    order.save(update_fields=['commission_applied', 'commission'])
