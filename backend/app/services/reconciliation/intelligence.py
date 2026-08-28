from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.financial import (
    Adjustment,
    Fee,
    Payment,
    Settlement,
)
from app.models.reconciliation import ExceptionRecord


def analyze_exception(
    db: Session,
    exception: ExceptionRecord,
) -> dict:
    """Analyze a reconciliation exception using available financial evidence.

    The goal is to determine whether the exception can be explained
    automatically or requires human investigation.
    """
    payment = (
        db.query(Payment)
        .filter(Payment.payment_id == exception.transaction_id)
        .first()
    )

    if payment is None:
        return {
            "exception_id": exception.exception_id,
            "classification": "UNKNOWN",
            "severity": "CRITICAL",
            "confidence": Decimal("0.9900"),
            "recommended_action": "HUMAN_REVIEW",
            "root_cause": "Payment record could not be found.",
        }

    settlement = (
        db.query(Settlement)
        .filter(Settlement.payment_id == payment.payment_id)
        .first()
    )

    fees = (
        db.query(Fee)
        .filter(Fee.payment_id == payment.payment_id)
        .all()
    )

    adjustments = (
        db.query(Adjustment)
        .filter(Adjustment.payment_id == payment.payment_id)
        .all()
    )

    # ---------------------------------------------------------
    # CASE 1: Missing settlement
    # ---------------------------------------------------------
    if exception.exception_type == "MISSING_SETTLEMENT":
        return {
            "exception_id": exception.exception_id,
            "classification": "MISSING_SETTLEMENT",
            "severity": "HIGH",
            "confidence": Decimal("0.9900"),
            "recommended_action": "HUMAN_REVIEW",
            "root_cause": (
                f"Payment {payment.payment_id} has no corresponding "
                "settlement record."
            ),
        }

    # ---------------------------------------------------------
    # CASE 2: Amount mismatch
    # ---------------------------------------------------------
    if exception.exception_type == "AMOUNT_MISMATCH":
        payment_amount = payment.amount
        settlement_amount = settlement.amount if settlement else Decimal("0.00")

        difference = payment_amount - settlement_amount

        total_fees = sum(
            (fee.amount for fee in fees),
            Decimal("0.00"),
        )

        total_adjustments = sum(
            (adjustment.amount for adjustment in adjustments),
            Decimal("0.00"),
        )

        # -----------------------------------------------------
        # Fee explains the entire difference
        # -----------------------------------------------------
        if difference == total_fees and total_fees != Decimal("0.00"):
            return {
                "exception_id": exception.exception_id,
                "classification": "FEE_EXPLAINED_MISMATCH",
                "severity": "LOW",
                "confidence": Decimal("0.9800"),
                "recommended_action": "AUTO_RESOLVE",
                "root_cause": (
                    f"Settlement is lower than payment by "
                    f"{difference:.2f}. The difference exactly matches "
                    f"the recorded processing fee of {total_fees:.2f}."
                ),
            }

        # -----------------------------------------------------
        # Fee + adjustment explain the difference
        # -----------------------------------------------------
        if (
            difference == total_fees + total_adjustments
            and (total_fees != Decimal("0.00") or total_adjustments != Decimal("0.00"))
        ):
            return {
                "exception_id": exception.exception_id,
                "classification": "FEE_ADJUSTMENT_EXPLAINED_MISMATCH",
                "severity": "LOW",
                "confidence": Decimal("0.9700"),
                "recommended_action": "AUTO_RESOLVE",
                "root_cause": (
                    f"Payment-to-settlement difference of "
                    f"{difference:.2f} is fully explained by recorded "
                    f"fees ({total_fees:.2f}) and adjustments "
                    f"({total_adjustments:.2f})."
                ),
            }

        # -----------------------------------------------------
        # Difference is unexplained
        # -----------------------------------------------------
        return {
            "exception_id": exception.exception_id,
            "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
            "severity": "HIGH",
            "confidence": Decimal("0.9500"),
            "recommended_action": "HUMAN_REVIEW",
            "root_cause": (
                f"Payment amount is {payment_amount:.2f}, while "
                f"settlement amount is {settlement_amount:.2f}. "
                f"The unexplained difference is {difference:.2f}."
            ),
        }

    # ---------------------------------------------------------
    # Unknown exception
    # ---------------------------------------------------------
    return {
        "exception_id": exception.exception_id,
        "classification": "UNKNOWN",
        "severity": "MEDIUM",
        "confidence": Decimal("0.5000"),
        "recommended_action": "HUMAN_REVIEW",
        "root_cause": (
            f"No intelligence rule exists yet for exception type "
            f"{exception.exception_type}."
        ),
    }


def analyze_all_exceptions(
    db: Session,
) -> list[dict]:
    """Analyze all currently stored reconciliation exceptions."""
    exceptions = (
        db.query(ExceptionRecord)
        .order_by(ExceptionRecord.id)
        .all()
    )

    return [
        analyze_exception(db, exception)
        for exception in exceptions
    ]