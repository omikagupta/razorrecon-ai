from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.reconciliation import (
    ExceptionRecord,
    ReconciliationResult,
)


def get_exception_analytics(db: Session) -> dict:
    """Return operational and financial analytics for exceptions."""

    exceptions = (
        db.query(ExceptionRecord)
        .order_by(ExceptionRecord.id)
        .all()
    )

    results = (
        db.query(ReconciliationResult)
        .all()
    )

    total_exceptions = len(exceptions)

    open_count = 0
    resolved_count = 0
    escalated_count = 0

    severity_counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    type_counts = {}

    total_exposure = Decimal("0.00")

    for exception in exceptions:
        status = exception.status.upper()
        severity = exception.severity.upper()
        exception_type = exception.exception_type.upper()

        if status == "OPEN":
            open_count += 1
        elif status == "RESOLVED":
            resolved_count += 1
        elif status == "ESCALATED":
            escalated_count += 1

        if severity in severity_counts:
            severity_counts[severity] += 1

        type_counts[exception_type] = (
            type_counts.get(exception_type, 0) + 1
        )

    # Financial exposure comes from reconciliation differences.
    for result in results:
        if result.status != "MATCHED" and result.difference is not None:
            total_exposure += abs(
                Decimal(str(result.difference))
            )

    resolution_rate = (
        resolved_count / total_exceptions
        if total_exceptions
        else 0
    )

    return {
        "total_exceptions": total_exceptions,
        "open_exceptions": open_count,
        "resolved_exceptions": resolved_count,
        "escalated_exceptions": escalated_count,
        "resolution_rate": round(resolution_rate, 4),
        "severity_distribution": severity_counts,
        "exception_type_distribution": type_counts,
        "financial_exposure": f"{total_exposure:.2f}",
    }