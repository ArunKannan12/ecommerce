def apply_promoter_commission(order):
    if order.promoter and not order.commission_applied:
        promoter = order.promoter
        promoter.total_sales_count += 1
        commission = order.total * 0.05
        promoter.total_commission_earned += commission
        promoter.wallet_balance += commission
        promoter.is_eligible_for_withdrawal = promoter.wallet_balance >= 500
        promoter.save()

        order.commission_applied = True  # You'll need to add this field
        order.save(update_fields=['commission_applied'])
