from decimal import Decimal


def amounts_match(
    payment_amount: Decimal,
    settlement_amount: Decimal,
) -> bool:
    """
    Check whether payment and settlement amounts match exactly.

    Financial reconciliation uses exact currency values. A difference
    of even 0.01 is treated as a genuine mismatch and should be
    investigated or explained by fees/adjustments.
    """
    if payment_amount is None or settlement_amount is None:
        return False

    payment = Decimal(str(payment_amount))
    settlement = Decimal(str(settlement_amount))

    return payment == settlement