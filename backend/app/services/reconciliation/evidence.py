from sqlalchemy.orm import Session

from app.models.financial import (
    Adjustment,
    Fee,
    Order,
    Payment,
    Refund,
    Settlement,
)
from app.models.reconciliation import Evidence, ExceptionRecord


def generate_evidence(
    db: Session,
    exception: ExceptionRecord,
) -> int:
    """
    Generate evidence records for a reconciliation exception.

    Evidence is collected from the financial records associated
    with the transaction/payment.
    """

    payment = (
        db.query(Payment)
        .filter(Payment.payment_id == exception.transaction_id)
        .first()
    )

    if payment is None:
        return 0

    evidence_count = 0

    # ---------------------------------------------------------
    # Payment evidence
    # ---------------------------------------------------------

    db.add(
        Evidence(
            exception_id=exception.exception_id,
            evidence_type="PAYMENT",
            source_table="payments",
            source_record_id=payment.payment_id,
            description=(
                f"Payment {payment.payment_id}: "
                f"amount={payment.amount}, "
                f"status={payment.status}, "
                f"merchant={payment.merchant_id}"
            ),
        )
    )

    evidence_count += 1

    # ---------------------------------------------------------
    # Order evidence
    # ---------------------------------------------------------

    if payment.order_id:
        order = (
            db.query(Order)
            .filter(Order.order_id == payment.order_id)
            .first()
        )

        if order:
            db.add(
                Evidence(
                    exception_id=exception.exception_id,
                    evidence_type="ORDER",
                    source_table="orders",
                    source_record_id=order.order_id,
                    description=(
                        f"Order {order.order_id}: "
                        f"amount={order.amount}, "
                        f"status={order.status}"
                    ),
                )
            )

            evidence_count += 1

    # ---------------------------------------------------------
    # Settlement evidence
    # ---------------------------------------------------------

    settlement = (
        db.query(Settlement)
        .filter(Settlement.payment_id == payment.payment_id)
        .first()
    )

    if settlement:
        db.add(
            Evidence(
                exception_id=exception.exception_id,
                evidence_type="SETTLEMENT",
                source_table="settlements",
                source_record_id=settlement.settlement_id,
                description=(
                    f"Settlement {settlement.settlement_id}: "
                    f"amount={settlement.amount}, "
                    f"merchant={settlement.merchant_id}"
                ),
            )
        )

        evidence_count += 1

    # ---------------------------------------------------------
    # Refund evidence
    # ---------------------------------------------------------

    refunds = (
        db.query(Refund)
        .filter(Refund.payment_id == payment.payment_id)
        .all()
    )

    for refund in refunds:
        db.add(
            Evidence(
                exception_id=exception.exception_id,
                evidence_type="REFUND",
                source_table="refunds",
                source_record_id=refund.refund_id,
                description=(
                    f"Refund {refund.refund_id}: "
                    f"amount={refund.amount}, "
                    f"status={refund.status}"
                ),
            )
        )

        evidence_count += 1

    # ---------------------------------------------------------
    # Fee evidence
    # ---------------------------------------------------------

    fees = (
        db.query(Fee)
        .filter(Fee.payment_id == payment.payment_id)
        .all()
    )

    for fee in fees:
        db.add(
            Evidence(
                exception_id=exception.exception_id,
                evidence_type="FEE",
                source_table="fees",
                source_record_id=fee.fee_id,
                description=(
                    f"Fee {fee.fee_id}: "
                    f"type={fee.fee_type}, "
                    f"amount={fee.amount}"
                ),
            )
        )

        evidence_count += 1

    # ---------------------------------------------------------
    # Adjustment evidence
    # ---------------------------------------------------------

    adjustments = (
        db.query(Adjustment)
        .filter(Adjustment.payment_id == payment.payment_id)
        .all()
    )

    for adjustment in adjustments:
        db.add(
            Evidence(
                exception_id=exception.exception_id,
                evidence_type="ADJUSTMENT",
                source_table="adjustments",
                source_record_id=adjustment.adjustment_id,
                description=(
                    f"Adjustment {adjustment.adjustment_id}: "
                    f"type={adjustment.adjustment_type}, "
                    f"amount={adjustment.amount}"
                ),
            )
        )

        evidence_count += 1

    return evidence_count