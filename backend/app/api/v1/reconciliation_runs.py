
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.reconciliation.engine import (
    run_payment_settlement_reconciliation,
)
from app.services.reconciliation.persistence import (
    persist_reconciliation_results,
)
from app.services.reconciliation.run_manager import (
    get_reconciliation_run_details,
    list_reconciliation_runs,
)


router = APIRouter(
    prefix="/api/v1/reconciliation-runs",
    tags=["Reconciliation Runs"],
)


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# RUN RECONCILIATION
# =========================================================

@router.post("")
def run_reconciliation(
    db: Session = Depends(get_db),
):
    """
    Execute payment-settlement reconciliation.

    The reconciliation engine compares all payments
    against their settlements and persists:

    - Reconciliation results
    - Exceptions
    - Evidence
    - Audit logs
    - Reconciliation run metadata
    """

    try:
        # Run reconciliation engine
        results = run_payment_settlement_reconciliation(
            db=db,
        )

        # Persist complete reconciliation run
        run = persist_reconciliation_results(
            db=db,
            results=results,
        )

        return {
            "message": "Reconciliation completed successfully.",
            "run": {
                "run_id": run.run_id,
                "status": run.status,
                "total_records": run.total_records,
                "matched_records": run.matched_records,
                "exception_count": run.exception_count,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "RECONCILIATION_VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "RECONCILIATION_FAILED",
                "message": str(exc),
            },
        )


# =========================================================
# LIST RECONCILIATION RUNS
# =========================================================

@router.get("")
def get_reconciliation_runs(
    db: Session = Depends(get_db),
):
    """
    Return reconciliation run history.
    """

    runs = list_reconciliation_runs(db)

    return {
        "total": len(runs),
        "runs": [
            {
                "run_id": run.run_id,
                "status": run.status,
                "total_records": run.total_records,
                "matched_records": run.matched_records,
                "exception_count": run.exception_count,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
            }
            for run in runs
        ],
    }


# =========================================================
# GET DETAILED RECONCILIATION RUN
# =========================================================

@router.get("/{run_id}")
def get_reconciliation_run_details_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
):
    """
    Return detailed information for a reconciliation run.

    Includes:
    - Run metadata
    - Reconciliation results
    - Status distribution
    - Financial difference summary
    """

    details = get_reconciliation_run_details(
        db=db,
        run_id=run_id,
    )

    if details is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "RECONCILIATION_RUN_NOT_FOUND",
                "message": (
                    f"Reconciliation run {run_id} was not found."
                ),
                "run_id": run_id,
            },
        )

    return details
