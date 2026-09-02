
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.financial import Payment, Settlement
from app.services.reconciliation.rules import amounts_match


def reconcile_payment(
    db: Session,
    payment: Payment,
) -> dict:
    """Reconcile a single payment against its settlements.

    Matching hierarchy:
    1. Find settlements using payment_id.
    2. If no settlement exists -> MISSING_SETTLEMENT.
    3. If multiple settlements exist -> DUPLICATE_SETTLEMENT.
    4. If currency differs -> CURRENCY_MISMATCH.
    5. If amount differs -> AMOUNT_MISMATCH.
    6. If amount and currency match -> MATCHED.

    All monetary comparisons use Decimal values.
    """

    settlements = (
        db.query(Settlement)
        .filter(
            Settlement.payment_id == payment.payment_id
        )
        .order_by(Settlement.id)
        .all()
    )

    # ---------------------------------------------------------
    # No settlement found
    # ---------------------------------------------------------

    if not settlements:
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": None,
            "difference": None,
            "payment_currency": payment.currency,
            "settlement_currency": None,
            "status": "MISSING_SETTLEMENT",
            "match_method": "PAYMENT_ID",
            "settlement_id": None,
            "settlement_count": 0,
        }

    # ---------------------------------------------------------
    # Multiple settlements found
    # ---------------------------------------------------------

    if len(settlements) > 1:
        settlement_amounts = [
            settlement.amount
            for settlement in settlements
        ]

        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": None,
            "difference": None,
            "payment_currency": payment.currency,
            "settlement_currency": None,
            "status": "DUPLICATE_SETTLEMENT",
            "match_method": "PAYMENT_ID",
            "settlement_id": None,
            "settlement_count": len(settlements),
            "settlement_ids": [
                settlement.settlement_id
                for settlement in settlements
            ],
            "settlement_amounts": settlement_amounts,
        }

    # ---------------------------------------------------------
    # Exactly one settlement
    # ---------------------------------------------------------

    settlement = settlements[0]

    # ---------------------------------------------------------
    # Currency mismatch
    # ---------------------------------------------------------

    if payment.currency != settlement.currency:
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": settlement.amount,
            "difference": None,
            "payment_currency": payment.currency,
            "settlement_currency": settlement.currency,
            "status": "CURRENCY_MISMATCH",
            "match_method": "PAYMENT_ID",
            "settlement_id": settlement.settlement_id,
            "settlement_count": 1,
        }

    # ---------------------------------------------------------
    # Calculate exact financial difference
    # ---------------------------------------------------------

    difference = (
        Decimal(str(payment.amount))
        - Decimal(str(settlement.amount))
    )

    # ---------------------------------------------------------
    # Amount mismatch
    # ---------------------------------------------------------

    if not amounts_match(
        payment.amount,
        settlement.amount,
    ):
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": settlement.amount,
            "difference": difference,
            "payment_currency": payment.currency,
            "settlement_currency": settlement.currency,
            "status": "AMOUNT_MISMATCH",
            "match_method": "PAYMENT_ID",
            "settlement_id": settlement.settlement_id,
            "settlement_count": 1,
        }

    # ---------------------------------------------------------
    # Exact reconciliation
    # ---------------------------------------------------------

    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "merchant_id": payment.merchant_id,
        "payment_amount": payment.amount,
        "settlement_amount": settlement.amount,
        "difference": Decimal("0.00"),
        "payment_currency": payment.currency,
        "settlement_currency": settlement.currency,
        "status": "MATCHED",
        "match_method": "PAYMENT_ID",
        "settlement_id": settlement.settlement_id,
        "settlement_count": 1,
    }
