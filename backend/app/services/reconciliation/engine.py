from sqlalchemy.orm import Session

from app.models.financial import Payment
from app.services.reconciliation.matcher import reconcile_payment


def run_payment_settlement_reconciliation(
    db: Session,
) -> list[dict]:
    """Reconcile every payment against its settlement.

    Returns a list containing the reconciliation result
    for each payment.
    """
    payments = (
        db.query(Payment)
        .order_by(Payment.id)
        .all()
    )

    results = []

    for payment in payments:
        result = reconcile_payment(
            db=db,
            payment=payment,
        )
        results.append(result)

    return results


def reconciliation_summary(
    results: list[dict],
) -> dict:
    """Generate a summary of reconciliation results."""
    summary = {
        "total": len(results),
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
    }

    for result in results:
        status = result["status"]

        if status == "MATCHED":
            summary["matched"] += 1
        elif status == "AMOUNT_MISMATCH":
            summary["amount_mismatch"] += 1
        elif status == "MISSING_SETTLEMENT":
            summary["missing_settlement"] += 1

    return summary