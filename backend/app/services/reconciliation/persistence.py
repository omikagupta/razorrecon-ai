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
from app.services.reconciliation.run_manager import (
    complete_reconciliation_run,
    create_reconciliation_run,
    fail_reconciliation_run,
    mark_run_running,
)

def persist_reconciliation_results(
    db: Session,
    results: list[dict],
) -> ReconciliationRun:
    """
    Persist reconciliation results within a managed
    reconciliation run lifecycle.

    Lifecycle:

        CREATED
           ↓
        RUNNING
           ↓
        COMPLETED

    If processing fails:

        CREATED/RUNNING
           ↓
        FAILED
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

    if any(
        transaction_id is None
        for transaction_id in transaction_ids
    ):
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

    run = create_reconciliation_run(
        db=db,
        total_records=len(results),
    )

    try:

        # -----------------------------------------------------
        # 3. Mark run as RUNNING
        # -----------------------------------------------------

        run = mark_run_running(
            db=db,
            run=run,
        )

        matched_count = 0
        exception_count = 0

        # -----------------------------------------------------
        # 4. Persist each reconciliation result
        # -----------------------------------------------------

        for result in results:

            result_status = result["status"]
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

            confidence = Decimal("1.0000")
            match_method = "PAYMENT_ID"

            # -------------------------------------------------
            # Persist reconciliation result
            # -------------------------------------------------

            reconciliation_result = ReconciliationResult(
                run_id=run.run_id,
                transaction_id=transaction_id,
                status=result_status,
                expected_amount=expected_amount,
                actual_amount=actual_amount,
                difference=difference,
                match_method=match_method,
                match_confidence=confidence,
                created_at=datetime.utcnow(),
            )

            db.add(reconciliation_result)

            # -------------------------------------------------
            # MATCHED
            # -------------------------------------------------

            if result_status == "MATCHED":

                matched_count += 1

                db.add(
                    AuditLog(
                        transaction_id=transaction_id,
                        actor="SYSTEM",
                        action="RECONCILIATION_MATCHED",
                        previous_state=None,
                        new_state="MATCHED",
                        reason=(
                            "Payment amount matched "
                            "settlement amount."
                        ),
                        confidence=confidence,
                        created_at=datetime.utcnow(),
                    )
                )

            # -------------------------------------------------
            # AMOUNT MISMATCH
            # -------------------------------------------------

            elif result_status == "AMOUNT_MISMATCH":

                exception_count += 1

                from uuid import uuid4

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

                generate_evidence(
                    db=db,
                    exception=exception,
                )

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
            # MISSING SETTLEMENT
            # -------------------------------------------------

            elif result_status == "MISSING_SETTLEMENT":

                exception_count += 1

                from uuid import uuid4

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

                generate_evidence(
                    db=db,
                    exception=exception,
                )

                db.add(
                    AuditLog(
                        transaction_id=transaction_id,
                        actor="SYSTEM",
                        action="EXCEPTION_CREATED",
                        previous_state=None,
                        new_state="OPEN",
                        reason=(
                            "Payment has no corresponding "
                            "settlement."
                        ),
                        confidence=confidence,
                        created_at=datetime.utcnow(),
                    )
                )

            # -------------------------------------------------
            # Unknown status
            # -------------------------------------------------

            else:
                raise ValueError(
                    "Unsupported reconciliation status: "
                    f"{result_status}"
                )

        # -----------------------------------------------------
        # 5. Commit persisted results
        # -----------------------------------------------------

        db.commit()

        # -----------------------------------------------------
        # 6. Complete reconciliation run
        # -----------------------------------------------------

        run = complete_reconciliation_run(
            db=db,
            run=run,
            total_records=len(results),
            matched_records=matched_count,
            exception_count=exception_count,
        )

        return run

    except Exception:

        # Roll back failed reconciliation changes.
        db.rollback()

        # Mark the run as FAILED.
        try:
            fail_reconciliation_run(
                db=db,
                run=run,
            )
        except Exception:
            db.rollback()

        raise