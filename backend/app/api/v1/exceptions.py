from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.investigation.exception_analyzer import (
    investigate_exception,
)
from app.db.session import SessionLocal
from app.models.reconciliation import (
    AuditLog,
    Evidence,
    ExceptionRecord,
    HumanReview,
)
from app.services.reconciliation.analytics import (
    get_exception_analytics,
)
from app.services.reconciliation.intelligence import (
    analyze_exception,
)


router = APIRouter(
    prefix="/api/v1/exceptions",
    tags=["Exceptions"],
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
# REQUEST MODELS
# =========================================================

class HumanReviewRequest(BaseModel):
    reviewer: str
    action: str
    reason: str


# =========================================================
# EXCEPTION LIST
# =========================================================

@router.get("")
def list_exceptions(
    status: str | None = None,
    severity: str | None = None,
    exception_type: str | None = None,
    db: Session = Depends(get_db),
):
    """
    List reconciliation exceptions.

    Optional filters:
    - status
    - severity
    - exception_type
    """

    query = db.query(ExceptionRecord)

    if status:
        query = query.filter(
            ExceptionRecord.status == status.upper()
        )

    if severity:
        query = query.filter(
            ExceptionRecord.severity == severity.upper()
        )

    if exception_type:
        query = query.filter(
            ExceptionRecord.exception_type
            == exception_type.upper()
        )

    exceptions = (
        query
        .order_by(ExceptionRecord.id)
        .all()
    )

    return {
        "total": len(exceptions),
        "exceptions": [
            {
                "exception_id": exception.exception_id,
                "transaction_id": exception.transaction_id,
                "exception_type": exception.exception_type,
                "severity": exception.severity,
                "status": exception.status,
                "confidence": exception.confidence,
                "description": exception.description,
                "created_at": exception.created_at,
                "resolved_at": exception.resolved_at,
            }
            for exception in exceptions
        ],
    }


# =========================================================
# EXCEPTION ANALYTICS
# =========================================================

@router.get("/analytics/summary")
def exception_analytics(
    db: Session = Depends(get_db),
):
    """
    Return exception and financial analytics
    for the reconciliation dashboard.
    """

    return get_exception_analytics(db)


# =========================================================
# EXCEPTION INVESTIGATION DETAILS
# =========================================================

@router.get("/{exception_id}")
def get_exception(
    exception_id: str,
    db: Session = Depends(get_db),
):
    """
    Return complete investigation information
    for a single exception.

    Includes:
    - Exception details
    - Evidence
    - Intelligence analysis
    - Human reviews
    - Audit history
    """

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.exception_id == exception_id
        )
        .first()
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exception {exception_id} not found.",
        )

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.exception_id == exception.exception_id
        )
        .order_by(Evidence.id)
        .all()
    )

    human_reviews = (
        db.query(HumanReview)
        .filter(
            HumanReview.exception_id
            == exception.exception_id
        )
        .order_by(HumanReview.id)
        .all()
    )

    audit_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.transaction_id
            == exception.transaction_id
        )
        .order_by(AuditLog.id)
        .all()
    )

    intelligence = analyze_exception(
        db=db,
        exception=exception,
    )

    return {
        "exception": {
            "exception_id": exception.exception_id,
            "transaction_id": exception.transaction_id,
            "exception_type": exception.exception_type,
            "severity": exception.severity,
            "status": exception.status,
            "confidence": exception.confidence,
            "description": exception.description,
            "created_at": exception.created_at,
            "resolved_at": exception.resolved_at,
        },
        "intelligence": intelligence,
        "evidence": [
            {
                "id": item.id,
                "evidence_type": item.evidence_type,
                "source_table": item.source_table,
                "source_record_id": item.source_record_id,
                "description": item.description,
                "created_at": item.created_at,
            }
            for item in evidence
        ],
        "human_reviews": [
            {
                "id": review.id,
                "reviewer": review.reviewer,
                "action": review.action,
                "reason": review.reason,
                "created_at": review.created_at,
            }
            for review in human_reviews
        ],
        "audit_logs": [
            {
                "id": log.id,
                "transaction_id": log.transaction_id,
                "actor": log.actor,
                "action": log.action,
                "previous_state": log.previous_state,
                "new_state": log.new_state,
                "reason": log.reason,
                "confidence": log.confidence,
                "created_at": log.created_at,
            }
            for log in audit_logs
        ],
    }


# =========================================================
# AI INVESTIGATION
# =========================================================

@router.post("/{exception_id}/investigate")
def investigate_exception_endpoint(
    exception_id: str,
    db: Session = Depends(get_db),
):
    """
    Perform an AI-assisted investigation of a reconciliation exception.

    The investigation combines deterministic reconciliation intelligence,
    supporting evidence, and an optional AI provider.

    If no AI provider is configured, the endpoint gracefully returns
    deterministic analysis.
    """

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.exception_id == exception_id
        )
        .first()
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exception {exception_id} not found.",
        )

    return investigate_exception(
        db=db,
        exception=exception,
    )


# =========================================================
# HUMAN REVIEW
# =========================================================

@router.post("/{exception_id}/review")
def review_exception(
    exception_id: str,
    review: HumanReviewRequest,
    db: Session = Depends(get_db),
):
    """
    Perform a human review of an exception.

    Supported actions:

    APPROVE:
        OPEN -> RESOLVED

    REJECT:
        OPEN -> ESCALATED

    ESCALATE:
        OPEN -> ESCALATED
    """

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.exception_id == exception_id
        )
        .first()
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exception {exception_id} not found.",
        )

    action = review.action.upper().strip()

    allowed_actions = {
        "APPROVE",
        "REJECT",
        "ESCALATE",
    }

    if action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid review action. "
                "Allowed actions: APPROVE, REJECT, ESCALATE."
            ),
        )

    if exception.status != "OPEN":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Exception {exception_id} is already "
                f"in status {exception.status}."
            ),
        )

    if not review.reviewer.strip():
        raise HTTPException(
            status_code=400,
            detail="Reviewer cannot be empty.",
        )

    if not review.reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Review reason cannot be empty.",
        )

    previous_state = exception.status

    if action == "APPROVE":
        new_state = "RESOLVED"
        audit_action = "EXCEPTION_RESOLVED"

    elif action == "REJECT":
        new_state = "ESCALATED"
        audit_action = "EXCEPTION_REJECTED"

    else:
        new_state = "ESCALATED"
        audit_action = "EXCEPTION_ESCALATED"

    # -----------------------------------------------------
    # Update exception
    # -----------------------------------------------------

    exception.status = new_state

    if new_state == "RESOLVED":
        exception.resolved_at = datetime.utcnow()

    # -----------------------------------------------------
    # Create human review record
    # -----------------------------------------------------

    human_review = HumanReview(
        exception_id=exception.exception_id,
        reviewer=review.reviewer.strip(),
        action=action,
        reason=review.reason.strip(),
        created_at=datetime.utcnow(),
    )

    db.add(human_review)

    # -----------------------------------------------------
    # Create audit log
    # -----------------------------------------------------

    audit_log = AuditLog(
        transaction_id=exception.transaction_id,
        actor=review.reviewer.strip(),
        action=audit_action,
        previous_state=previous_state,
        new_state=new_state,
        reason=review.reason.strip(),
        confidence=exception.confidence,
        created_at=datetime.utcnow(),
    )

    db.add(audit_log)

    db.commit()
    db.refresh(exception)

    return {
        "message": "Exception review recorded successfully.",
        "exception_id": exception.exception_id,
        "transaction_id": exception.transaction_id,
        "reviewer": review.reviewer.strip(),
        "action": action,
        "previous_state": previous_state,
        "new_state": new_state,
        "reason": review.reason.strip(),
        "resolved_at": exception.resolved_at,
    }