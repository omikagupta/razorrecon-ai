from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.reconciliation import (
    AuditLog,
    ExceptionRecord,
    ReconciliationResult,
    ReconciliationRun,
)
from app.services.reconciliation.evidence import generate_evidence


def persist_reconciliation_results(
    db: Session,
    results: list[dict],
) -> ReconciliationRun:
    """
    Persist a reconciliation run.

    Each invocation creates a new reconciliation run so that historical
    reconciliation runs remain auditable.

    Within the run:
    - MATCHED results are persisted without exceptions.
    - AMOUNT_MISMATCH results create HIGH-severity exceptions.
    - MISSING_SETTLEMENT results create CRITICAL exceptions.
    - Evidence is generated for every created exception.
    - Audit logs are created for reconciliation state changes.
    - Duplicate transaction IDs in the supplied result set are rejected.
    """

    # ---------------------------------------------------------
    # 1. Validate input
    # ---------------------------------------------------------

    if not results:
        raise ValueError(
            "Cannot persist an empty reconciliation result set."
        )

    transaction_ids = [
        result.get("payment_id")
        for result in results
    ]

    if any(transaction_id is None for transaction_id in transaction_ids):
        raise ValueError(
            "Every reconciliation result must contain payment_id."
        )

    if len(transaction_ids) != len(set(transaction_ids)):
        raise ValueError(
            "Duplicate payment_id detected in reconciliation results."
        )

    # ---------------------------------------------------------
    # 2. Create reconciliation run
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

    try:

        # -----------------------------------------------------
        # 3. Persist each reconciliation result
        # -----------------------------------------------------

        for result in results:

            status = result["status"]
            transaction_id = result["payment_id"]

            expected_amount = result["payment_amount"]
            actual_amount = result["settlement_amount"]

            # -------------------------------------------------
            # Calculate financial difference
            # -------------------------------------------------

            if actual_amount is None:
                difference = None
            else:
                difference = (
                    Decimal(str(expected_amount))
                    - Decimal(str(actual_amount))
                )

            # -------------------------------------------------
            # Matching metadata
            # -------------------------------------------------

            confidence = Decimal("1.0000")
            match_method = "PAYMENT_ID"

            # -------------------------------------------------
            # Persist reconciliation result
            # -------------------------------------------------

            reconciliation_result = ReconciliationResult(
                run_id=run.run_id,
                transaction_id=transaction_id,
                status=status,
                expected_amount=expected_amount,
                actual_amount=actual_amount,
                difference=difference,
                match_method=match_method,
                match_confidence=confidence,
                created_at=datetime.utcnow(),
            )

            db.add(reconciliation_result)

            # -------------------------------------------------
            # 4. MATCHED
            # -------------------------------------------------

            if status == "MATCHED":

                matched_count += 1

                db.add(
                    AuditLog(
                        transaction_id=transaction_id,
                        actor="SYSTEM",
                        action="RECONCILIATION_MATCHED",
                        previous_state=None,
                        new_state="MATCHED",
                        reason=(
                            "Payment amount matched settlement amount."
                        ),
                        confidence=confidence,
                        created_at=datetime.utcnow(),
                    )
                )

            # -------------------------------------------------
            # 5. AMOUNT MISMATCH
            # -------------------------------------------------

            elif status == "AMOUNT_MISMATCH":

                exception_count += 1

                exception = ExceptionRecord(
                    exception_id=(
                        f"EXC_{uuid4().hex[:12].upper()}"
                    ),
                    transaction_id=transaction_id,
                    exception_type="AMOUNT_MISMATCH",
                    severity="HIGH",
                    status="OPEN",
                    confidence=confidence,
                    description=(
                        f"Payment amount {expected_amount} does not "
                        f"match settlement amount {actual_amount}. "
                        f"Difference: {difference}."
                    ),
                    created_at=datetime.utcnow(),
                )

                db.add(exception)
                db.flush()

                # -------------------------------------------------
                # Generate financial evidence
                # -------------------------------------------------

                generate_evidence(
                    db=db,
                    exception=exception,
                )

                # -------------------------------------------------
                # Create audit log
                # -------------------------------------------------

                db.add(
                    AuditLog(
                        transaction_id=transaction_id,
                        actor="SYSTEM",
                        action="EXCEPTION_CREATED",
                        previous_state=None,
                        new_state="OPEN",
                        reason=(
                            "Settlement amount differs from "
                            "payment amount."
                        ),
                        confidence=confidence,
                        created_at=datetime.utcnow(),
                    )
                )

            # -------------------------------------------------
            # 6. MISSING SETTLEMENT
            # -------------------------------------------------

            elif status == "MISSING_SETTLEMENT":

                exception_count += 1

                exception = ExceptionRecord(
                    exception_id=(
                        f"EXC_{uuid4().hex[:12].upper()}"
                    ),
                    transaction_id=transaction_id,
                    exception_type="MISSING_SETTLEMENT",
                    severity="CRITICAL",
                    status="OPEN",
                    confidence=confidence,
                    description=(
                        f"No settlement found for payment "
                        f"{transaction_id}."
                    ),
                    created_at=datetime.utcnow(),
                )

                db.add(exception)
                db.flush()

                # -------------------------------------------------
                # Generate financial evidence
                # -------------------------------------------------

                generate_evidence(
                    db=db,
                    exception=exception,
                )

                # -------------------------------------------------
                # Create audit log
                # -------------------------------------------------

                db.add(
                    AuditLog(
                        transaction_id=transaction_id,
                        actor="SYSTEM",
                        action="EXCEPTION_CREATED",
                        previous_state=None,
                        new_state="OPEN",
                        reason=(
                            "Payment has no corresponding settlement."
                        ),
                        confidence=confidence,
                        created_at=datetime.utcnow(),
                    )
                )

            # -------------------------------------------------
            # 7. Unknown status
            # -------------------------------------------------

            else:

                raise ValueError(
                    f"Unsupported reconciliation status: {status}"
                )

        # -----------------------------------------------------
        # 8. Complete reconciliation run
        # -----------------------------------------------------

        run.matched_records = matched_count
        run.exception_count = exception_count
        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()

        db.commit()

        return run

    except Exception:
        # -----------------------------------------------------
        # Roll back the entire reconciliation run if anything
        # fails so we never leave partially persisted data.
        # -----------------------------------------------------

        db.rollback()
        raise