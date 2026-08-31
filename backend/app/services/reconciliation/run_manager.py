from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.reconciliation import (
    ReconciliationResult,
    ReconciliationRun,
)


def create_reconciliation_run(
    db: Session,
    total_records: int = 0,
) -> ReconciliationRun:
    """
    Create a new reconciliation run.

    The caller owns the database transaction.
    No commit is performed here.
    """

    run = ReconciliationRun(
        run_id=f"RUN_{uuid4().hex[:12].upper()}",
        status="CREATED",
        total_records=total_records,
        matched_records=0,
        exception_count=0,
        started_at=datetime.now(UTC),
        completed_at=None,
    )

    db.add(run)
    db.flush()

    return run


def mark_run_running(
    db: Session,
    run: ReconciliationRun,
) -> ReconciliationRun:
    """
    Mark a reconciliation run as actively processing.

    The caller owns the database transaction.
    """

    run.status = "RUNNING"
    run.started_at = datetime.now(UTC)

    db.flush()

    return run


def complete_reconciliation_run(
    db: Session,
    run: ReconciliationRun,
    total_records: int,
    matched_records: int,
    exception_count: int,
) -> ReconciliationRun:
    """
    Mark a reconciliation run as successfully completed.

    The caller owns the database transaction.
    """

    run.status = "COMPLETED"
    run.total_records = total_records
    run.matched_records = matched_records
    run.exception_count = exception_count
    run.completed_at = datetime.now(UTC)

    db.flush()

    return run


def fail_reconciliation_run(
    db: Session,
    run: ReconciliationRun,
) -> ReconciliationRun:
    """
    Mark a reconciliation run as failed.

    The caller owns the database transaction.
    """

    run.status = "FAILED"
    run.completed_at = datetime.now(UTC)

    db.flush()

    return run


def get_reconciliation_run(
    db: Session,
    run_id: str,
) -> ReconciliationRun | None:
    """
    Retrieve a reconciliation run by its public run ID.
    """

    return (
        db.query(ReconciliationRun)
        .filter(
            ReconciliationRun.run_id == run_id
        )
        .first()
    )


def list_reconciliation_runs(
    db: Session,
) -> list[ReconciliationRun]:
    """
    Return reconciliation runs ordered by newest first.
    """

    return (
        db.query(ReconciliationRun)
        .order_by(ReconciliationRun.id.desc())
        .all()
    )


def get_reconciliation_run_details(
    db: Session,
    run_id: str,
) -> dict | None:
    """
    Return detailed information for a reconciliation run.

    Includes:
    - Run metadata
    - All reconciliation results
    - Status distribution
    - Financial difference summary
    """

    run = get_reconciliation_run(
        db=db,
        run_id=run_id,
    )

    if run is None:
        return None

    results = (
        db.query(ReconciliationResult)
        .filter(
            ReconciliationResult.run_id == run_id
        )
        .order_by(ReconciliationResult.id)
        .all()
    )

    status_distribution = {
        "MATCHED": 0,
        "AMOUNT_MISMATCH": 0,
        "MISSING_SETTLEMENT": 0,
    }

    from decimal import Decimal

    total_financial_difference = Decimal("0.00")

    serialized_results = []

    for result in results:
        status = result.status

        if status not in status_distribution:
            status_distribution[status] = 0

        status_distribution[status] += 1

        if result.difference is not None:
            total_financial_difference += abs(
                Decimal(str(result.difference))
            )

        serialized_results.append(
            {
                "transaction_id": result.transaction_id,
                "status": result.status,
                "expected_amount": (
                    str(result.expected_amount)
                    if result.expected_amount is not None
                    else None
                ),
                "actual_amount": (
                    str(result.actual_amount)
                    if result.actual_amount is not None
                    else None
                ),
                "difference": (
                    str(result.difference)
                    if result.difference is not None
                    else None
                ),
                "match_method": result.match_method,
                "match_confidence": (
                    float(result.match_confidence)
                    if result.match_confidence is not None
                    else None
                ),
                "created_at": result.created_at,
            }
        )

    return {
        "run": {
            "run_id": run.run_id,
            "status": run.status,
            "total_records": run.total_records,
            "matched_records": run.matched_records,
            "exception_count": run.exception_count,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        },
        "summary": {
            "total_results": len(results),
            "matched": status_distribution.get(
                "MATCHED",
                0,
            ),
            "amount_mismatch": status_distribution.get(
                "AMOUNT_MISMATCH",
                0,
            ),
            "missing_settlement": status_distribution.get(
                "MISSING_SETTLEMENT",
                0,
            ),
            "total_financial_difference": (
                f"{total_financial_difference:.2f}"
            ),
        },
        "status_distribution": status_distribution,
        "results": serialized_results,
    }