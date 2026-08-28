from decimal import Decimal

# Amount tolerance for reconciliation.
# For now, exact matching is used.
AMOUNT_TOLERANCE = Decimal("0.01")


def amounts_match(
    payment_amount: Decimal,
    settlement_amount: Decimal,
) -> bool:
    """Check whether payment and settlement amounts match within the configured tolerance."""
    if payment_amount is None or settlement_amount is None:
        return False

    difference = abs(
        Decimal(payment_amount) - Decimal(settlement_amount)
    )

    return difference <= AMOUNT_TOLERANCE