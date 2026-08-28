
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.reconciliation import (
    ExceptionRecord,
    ReconciliationResult,
)


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
):
    """
    Return the high-level financial reconciliation
    metrics required by the finance dashboard.
    """

    results = (
        db.query(ReconciliationResult)
        .all()
    )

    exceptions = (
        db.query(ExceptionRecord)
        .all()
    )

    total_transactions = len(results)

    matched_transactions = sum(
        1
        for result in results
        if result.status == "MATCHED"
    )

    mismatched_transactions = sum(
        1
        for result in results
        if result.status == "AMOUNT_MISMATCH"
    )

    missing_settlements = sum(
        1
        for result in results
        if result.status == "MISSING_SETTLEMENT"
    )

    total_expected = Decimal("0.00")
    total_actual = Decimal("0.00")
    total_difference = Decimal("0.00")

    for result in results:
        if result.expected_amount is not None:
            total_expected += Decimal(
                str(result.expected_amount)
            )

        if result.actual_amount is not None:
            total_actual += Decimal(
                str(result.actual_amount)
            )

        if result.difference is not None:
            total_difference += abs(
                Decimal(str(result.difference))
            )

    open_exceptions = sum(
        1
        for exception in exceptions
        if exception.status == "OPEN"
    )

    resolved_exceptions = sum(
        1
        for exception in exceptions
        if exception.status == "RESOLVED"
    )

    escalated_exceptions = sum(
        1
        for exception in exceptions
        if exception.status == "ESCALATED"
    )

    high_severity = sum(
        1
        for exception in exceptions
        if exception.severity == "HIGH"
    )

    critical_severity = sum(
        1
        for exception in exceptions
        if exception.severity == "CRITICAL"
    )

    resolution_rate = (
        resolved_exceptions / len(exceptions)
        if exceptions
        else 0
    )

    match_rate = (
        matched_transactions / total_transactions
        if total_transactions
        else 0
    )

    return {
        "transactions": {
            "total": total_transactions,
            "matched": matched_transactions,
            "amount_mismatch": mismatched_transactions,
            "missing_settlement": missing_settlements,
            "match_rate": round(match_rate, 4),
        },
        "financials": {
            "total_expected_amount": f"{total_expected:.2f}",
            "total_actual_settlement": f"{total_actual:.2f}",
            "total_difference": f"{total_difference:.2f}",
        },
        "exceptions": {
            "total": len(exceptions),
            "open": open_exceptions,
            "resolved": resolved_exceptions,
            "escalated": escalated_exceptions,
            "resolution_rate": round(
                resolution_rate,
                4,
            ),
            "high_severity": high_severity,
            "critical_severity": critical_severity,
        },
    }


@router.get("/exception-trends")
def exception_trends(
    db: Session = Depends(get_db),
):
    """
    Return exception counts grouped by exception type
    and severity.
    """

    exceptions = (
        db.query(ExceptionRecord)
        .all()
    )

    by_type = {}
    by_severity = {}
    by_status = {}

    for exception in exceptions:

        exception_type = exception.exception_type
        severity = exception.severity
        status = exception.status

        by_type[exception_type] = (
            by_type.get(exception_type, 0) + 1
        )

        by_severity[severity] = (
            by_severity.get(severity, 0) + 1
        )

        by_status[status] = (
            by_status.get(status, 0) + 1
        )

    return {
        "by_exception_type": by_type,
        "by_severity": by_severity,
        "by_status": by_status,
    }

