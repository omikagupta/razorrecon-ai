from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
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
    """
    Request payload for a human review action.
    """

    reviewer: str = Field(
        min_length=1,
        max_length=100,
        description="Name or identifier of the reviewer.",
    )

    action: str = Field(
        min_length=1,
        max_length=50,
        description=(
            "Review action: APPROVE, REJECT, or ESCALATE."
        ),
    )

    reason: str = Field(
        min_length=1,
        description="Reason supporting the review decision.",
    )

    @field_validator("reviewer")
    @classmethod
    def validate_reviewer(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Reviewer cannot be empty."
            )

        return value

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Review reason cannot be empty."
            )

        return value

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        action = value.upper().strip()

        allowed_actions = {
            "APPROVE",
            "REJECT",
            "ESCALATE",
        }

        if action not in allowed_actions:
            raise ValueError(
                "Invalid review action. "
                "Allowed actions: APPROVE, REJECT, ESCALATE."
            )

        return action


# =========================================================
# HUMAN REVIEW RESPONSE MODEL
# =========================================================

class HumanReviewResponse(BaseModel):
    """
    Structured response returned after a human review.
    """

    message: str

    exception_id: str

    transaction_id: str

    reviewer: str

    action: str

    previous_state: str

    new_state: str

    reason: str

    resolved_at: datetime | None = None


# =========================================================
# AI INVESTIGATION RESPONSE MODELS
# =========================================================

class AIInvestigationResponse(BaseModel):
    """
    Structured AI investigation result exposed by the API.
    """

    summary: str = Field(
        min_length=1,
        description="Concise investigation summary.",
    )

    root_cause: str = Field(
        min_length=1,
        description="Most likely root cause based on evidence.",
    )

    risk_level: str = Field(
        description="Risk level assigned by the AI investigation.",
    )

    recommended_action: str = Field(
        description="Recommended operational action.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="AI confidence score between 0 and 1.",
    )

    key_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting the investigation.",
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        description="Questions that remain unresolved.",
    )


class InvestigationResponse(BaseModel):
    """
    Production API response for an exception investigation.
    """

    exception_id: str = Field(
        description="Unique reconciliation exception ID.",
    )

    investigation_mode: str = Field(
        description=(
            "Investigation mode: AI_ASSISTED or "
            "DETERMINISTIC_FALLBACK."
        ),
    )

    ai_provider_status: str = Field(
        description=(
            "AI provider state: SUCCESS, UNAVAILABLE, "
            "or INVALID_RESPONSE."
        ),
    )

    evidence_count: int = Field(
        ge=0,
        description="Number of evidence records considered.",
    )

    deterministic_analysis: dict

    ai_analysis: AIInvestigationResponse | None = None

    fallback_reason: str | None = None


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

@router.post(
    "/{exception_id}/investigate",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Investigate a reconciliation exception",
)
def investigate_exception_endpoint(
    exception_id: str,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    """
    Perform a production-grade investigation of an exception.
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "EXCEPTION_NOT_FOUND",
                "message": (
                    f"Exception {exception_id} not found."
                ),
                "exception_id": exception_id,
            },
        )

    try:
        result = investigate_exception(
            db=db,
            exception=exception,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INVESTIGATION_RUNTIME_ERROR",
                "message": (
                    "The investigation could not be completed."
                ),
                "exception_id": exception_id,
                "reason": str(error),
            },
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INVESTIGATION_FAILED",
                "message": (
                    "An unexpected error occurred while "
                    "investigating the exception."
                ),
                "exception_id": exception_id,
                "reason": str(error),
            },
        ) from error

    try:
        validated_response = (
            InvestigationResponse.model_validate(result)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INVALID_INVESTIGATION_RESULT",
                "message": (
                    "The investigation service returned "
                    "an invalid structured result."
                ),
                "exception_id": exception_id,
                "reason": str(error),
            },
        ) from error

    return validated_response


# =========================================================
# HUMAN REVIEW
# =========================================================

@router.post(
    "/{exception_id}/review",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Review a reconciliation exception",
    description=(
        "Record a human decision for an open reconciliation "
        "exception and update its lifecycle state."
    ),
    responses={
        404: {
            "description": "Exception not found.",
        },
        409: {
            "description": "Exception is not open for review.",
        },
        500: {
            "description": "Failed to persist review.",
        },
    },
)
def review_exception(
    exception_id: str,
    review: HumanReviewRequest,
    db: Session = Depends(get_db),
) -> HumanReviewResponse:
    """
    Perform a production-grade human review.

    State transitions:

    APPROVE:
        OPEN -> RESOLVED

    REJECT:
        OPEN -> ESCALATED

    ESCALATE:
        OPEN -> ESCALATED

    The operation is persisted atomically:

        Exception update
            +
        Human review record
            +
        Audit log
            =
        Single database transaction
    """

    # -----------------------------------------------------
    # 1. Find exception
    # -----------------------------------------------------

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.exception_id == exception_id
        )
        .first()
    )

    if exception is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "EXCEPTION_NOT_FOUND",
                "message": (
                    f"Exception {exception_id} not found."
                ),
                "exception_id": exception_id,
            },
        )

    # -----------------------------------------------------
    # 2. Validate current lifecycle state
    # -----------------------------------------------------

    if exception.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "INVALID_EXCEPTION_STATE",
                "message": (
                    "Only OPEN exceptions can be reviewed."
                ),
                "exception_id": exception_id,
                "current_status": exception.status,
            },
        )

    # -----------------------------------------------------
    # 3. Determine state transition
    # -----------------------------------------------------

    previous_state = exception.status

    action_mapping = {
        "APPROVE": {
            "new_state": "RESOLVED",
            "audit_action": "EXCEPTION_RESOLVED",
        },
        "REJECT": {
            "new_state": "ESCALATED",
            "audit_action": "EXCEPTION_REJECTED",
        },
        "ESCALATE": {
            "new_state": "ESCALATED",
            "audit_action": "EXCEPTION_ESCALATED",
        },
    }

    transition = action_mapping[review.action]

    new_state = transition["new_state"]
    audit_action = transition["audit_action"]

    # -----------------------------------------------------
    # 4. Apply changes atomically
    # -----------------------------------------------------

    try:
        exception.status = new_state

        if new_state == "RESOLVED":
            exception.resolved_at = datetime.now(UTC)

        human_review = HumanReview(
            exception_id=exception.exception_id,
            reviewer=review.reviewer,
            action=review.action,
            reason=review.reason,
           created_at=datetime.now(UTC),
        )

        db.add(human_review)

        audit_log = AuditLog(
            transaction_id=exception.transaction_id,
            actor=review.reviewer,
            action=audit_action,
            previous_state=previous_state,
            new_state=new_state,
            reason=review.reason,
            confidence=exception.confidence,
            created_at=datetime.now(UTC),
        )

        db.add(audit_log)

        db.commit()
        db.refresh(exception)

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "HUMAN_REVIEW_PERSISTENCE_FAILED",
                "message": (
                    "The human review could not be saved."
                ),
                "exception_id": exception_id,
                "reason": str(error),
            },
        ) from error

    # -----------------------------------------------------
    # 5. Return structured response
    # -----------------------------------------------------

    return HumanReviewResponse(
        message=(
            "Exception review recorded successfully."
        ),
        exception_id=exception.exception_id,
        transaction_id=exception.transaction_id,
        reviewer=review.reviewer,
        action=review.action,
        previous_state=previous_state,
        new_state=new_state,
        reason=review.reason,
        resolved_at=exception.resolved_at,
    )