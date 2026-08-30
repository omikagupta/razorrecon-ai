from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
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