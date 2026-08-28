from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from app.services.reconciliation.evidence import generate_evidence
from sqlalchemy.orm import Session

from app.models.reconciliation import (
    AuditLog,
    ExceptionRecord,
    ReconciliationResult,
    ReconciliationRun,
)


def persist_reconciliation_results(
    db: Session,
    results: list[dict],
) -> ReconciliationRun:
    """
    Persist reconciliation results and create exceptions
    for non-matching transactions.

    MATCHED:
        Stored as a reconciliation result only.

    AMOUNT_MISMATCH:
        Stored as a reconciliation result and exception.

    MISSING_SETTLEMENT:
        Stored as a reconciliation result and exception.
    """

    # ---------------------------------------------------------
    # 1. Create reconciliation run
    # ---------------------------------------------------------

    run = ReconciliationRun(
        run_id=f"RUN_{uuid4().hex[:12].upper()}",
        status="RUNNING",
        total_records=len(results),
        matched_records=0,
        exception_count=0,
        started_at=datetime.utcnow(),
    )

    db.add(run)
    db.flush()

    matched_count = 0
    exception_count = 0

    # ---------------------------------------------------------
    # 2. Persist each reconciliation result
    # ---------------------------------------------------------

    for result in results:
        status = result["status"]

        expected_amount = result["payment_amount"]
        actual_amount = result["settlement_amount"]

        if actual_amount is None:
            difference = None
        else:
            difference = Decimal(str(expected_amount)) - Decimal(
                str(actual_amount)
            )

        # Determine confidence
        if status == "MATCHED":
            confidence = 1.0
            match_method = "PAYMENT_ID"

        elif status == "AMOUNT_MISMATCH":
            confidence = 1.0
            match_method = "PAYMENT_ID"

        else:
            confidence = 1.0
            match_method = "PAYMENT_ID"

        reconciliation_result = ReconciliationResult(
            run_id=run.run_id,
            transaction_id=result["payment_id"],
            status=status,
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            difference=difference,
            match_method=match_method,
            match_confidence=confidence,
            created_at=datetime.utcnow(),
        )

        db.add(reconciliation_result)

        # -----------------------------------------------------
        # 3. MATCHED
        # -----------------------------------------------------

        if status == "MATCHED":
            matched_count += 1

            db.add(
                AuditLog(
                    transaction_id=result["payment_id"],
                    actor="SYSTEM",
                    action="RECONCILIATION_MATCHED",
                    previous_state=None,
                    new_state="MATCHED",
                    reason="Payment amount matched settlement amount.",
                    confidence=confidence,
                    created_at=datetime.utcnow(),
                )
            )

        # -----------------------------------------------------
        # 4. AMOUNT MISMATCH
        # -----------------------------------------------------

        elif status == "AMOUNT_MISMATCH":
            exception_count += 1

            exception = ExceptionRecord(
                exception_id=f"EXC_{uuid4().hex[:12].upper()}",
                transaction_id=result["payment_id"],
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="OPEN",
                confidence=confidence,
                description=(
                    f"Payment amount {expected_amount} does not match "
                    f"settlement amount {actual_amount}. "
                    f"Difference: {difference}."
                ),
                created_at=datetime.utcnow(),
            )

            db.add(exception)
            db.flush()

            db.add(
                AuditLog(
                    transaction_id=result["payment_id"],
                    actor="SYSTEM",
                    action="EXCEPTION_CREATED",
                    previous_state=None,
                    new_state="OPEN",
                    reason="Settlement amount differs from payment amount.",
                    confidence=confidence,
                    created_at=datetime.utcnow(),
                )
            )

        # -----------------------------------------------------
        # 5. MISSING SETTLEMENT
        # -----------------------------------------------------

        elif status == "MISSING_SETTLEMENT":
            exception_count += 1

            exception = ExceptionRecord(
                exception_id=f"EXC_{uuid4().hex[:12].upper()}",
                transaction_id=result["payment_id"],
                exception_type="MISSING_SETTLEMENT",
                severity="CRITICAL",
                status="OPEN",
                confidence=confidence,
                description=(
                    f"No settlement found for payment "
                    f"{result['payment_id']}."
                ),
                created_at=datetime.utcnow(),
            )

            db.add(exception)
            db.flush()

            db.add(
                AuditLog(
                    transaction_id=result["payment_id"],
                    actor="SYSTEM",
                    action="EXCEPTION_CREATED",
                    previous_state=None,
                    new_state="OPEN",
                    reason="Payment has no corresponding settlement.",
                    confidence=confidence,
                    created_at=datetime.utcnow(),
                )
            )

    # ---------------------------------------------------------
    # 6. Update reconciliation run
    # ---------------------------------------------------------

    run.matched_records = matched_count
    run.exception_count = exception_count
    run.status = "COMPLETED"
    run.completed_at = datetime.utcnow()

    db.commit()

    return run