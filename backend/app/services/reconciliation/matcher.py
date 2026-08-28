from sqlalchemy.orm import Session

from app.models.financial import Payment, Settlement
from app.services.reconciliation.rules import amounts_match


def reconcile_payment(
    db: Session,
    payment: Payment,
) -> dict:
    """Reconcile a single payment against its settlement.

    Matching hierarchy:
    1. Find settlement using payment_id.
    2. If no settlement exists -> MISSING_SETTLEMENT.
    3. If settlement exists but amount differs -> AMOUNT_MISMATCH.
    4. If amount matches -> MATCHED.
    """
    settlement = (
        db.query(Settlement)
        .filter(Settlement.payment_id == payment.payment_id)
        .first()
    )

    # No settlement found
    if settlement is None:
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": None,
            "status": "MISSING_SETTLEMENT",
            "settlement_id": None,
        }

    # Settlement exists but amount differs
    if not amounts_match(payment.amount, settlement.amount):
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "merchant_id": payment.merchant_id,
            "payment_amount": payment.amount,
            "settlement_amount": settlement.amount,
            "status": "AMOUNT_MISMATCH",
            "settlement_id": settlement.settlement_id,
        }

    # Exact reconciliation
    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "merchant_id": payment.merchant_id,
        "payment_amount": payment.amount,
        "settlement_amount": settlement.amount,
        "status": "MATCHED",
        "settlement_id": settlement.settlement_id,
    }