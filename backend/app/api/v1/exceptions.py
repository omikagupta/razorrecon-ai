from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
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
    Investigation,
)
from app.services.reconciliation.analytics import (
    get_exception_analytics,
)
from app.services.reconciliation.exception_service import (
    ExceptionService,
)
from app.services.reconciliation.intelligence import (
    analyze_exception,
)


# =========================================================
# ROUTER
# =========================================================

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
    reviewer: str = Field(
        min_length=1,
        max_length=100,
        description="Name or identifier of the reviewer.",
    )
    action: str = Field(
        min_length=1,
        max_length=50,
        description="Review action: APPROVE, REJECT, or ESCALATE.",
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
            raise ValueError("Reviewer cannot be empty.")
        return value

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Review reason cannot be empty.")
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

@router.get(
    "",
    summary="List reconciliation exceptions",
)
def list_exceptions(
    status_filter: str | None = Query(
        default=None,
        alias="status_filter",
        description="Filter by exception status.",
    ),
    status_param: str | None = Query(
        default=None,
        alias="status",
        description="Filter by exception status.",
    ),
    severity: str | None = Query(
        default=None,
        description="Filter by exception severity.",
    ),
    exception_type: str | None = Query(
        default=None,
        description="Filter by exception type.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-based).",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of exceptions per page.",
    ),
    db: Session = Depends(get_db),
):
    """
    List reconciliation exceptions with filtering and pagination.

    Supported query parameters:
    - status_filter
    - status
    - severity
    - exception_type

    Pagination:
    - page: 1-based page number
    - page_size: number of records per page.
    """
    service = ExceptionService(db)

    # Support both ?status_filter=OPEN and ?status=OPEN
    raw_status = (
        status_filter
        if status_filter is not None
        else status_param
    )

    normalized_status = (
        raw_status.strip().upper()
        if raw_status
        else None
    )
    normalized_severity = (
        severity.strip().upper()
        if severity
        else None
    )
    normalized_exception_type = (
        exception_type.strip().upper()
        if exception_type
        else None
    )

    offset = (page - 1) * page_size

    exceptions, total = service.list_exceptions(
        status=normalized_status,
        severity=normalized_severity,
        exception_type=normalized_exception_type,
        limit=page_size,
        offset=offset,
    )

    pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
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
# INVESTIGATION HISTORY
# (Placed before /{exception_id} to prevent path shadowing)
# =========================================================

@router.get(
    "/{exception_id}/investigations",
    summary="Get investigation history",
)
def get_investigation_history(
    exception_id: str,
    db: Session = Depends(get_db),
):
    """
    Return all persisted AI investigation records
    for a reconciliation exception.
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
                "message": f"Exception {exception_id} not found.",
                "exception_id": exception_id,
            },
        )

    investigations = (
        db.query(Investigation)
        .filter(
            Investigation.exception_id == exception_id
        )
        .order_by(
            Investigation.created_at.desc()
        )
        .all()
    )

    return {
        "exception_id": exception_id,
        "total": len(investigations),
        "investigations": [
            {
                "investigation_id": investigation.investigation_id,
                "investigation_mode": investigation.investigation_mode,
                "ai_provider_status": investigation.ai_provider_status,
                "evidence_count": investigation.evidence_count,
                "deterministic_analysis": investigation.deterministic_analysis,
                "ai_analysis": investigation.ai_analysis,
                "fallback_reason": investigation.fallback_reason,
                "created_at": investigation.created_at,
            }
            for investigation in investigations
        ],
    }


# =========================================================
# EXCEPTION DETAILS
# =========================================================

@router.get("/{exception_id}")
def get_exception(
    exception_id: str,
    db: Session = Depends(get_db),
):
    """
    Return complete investigation information
    for a single exception.
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
            HumanReview.exception_id == exception.exception_id
        )
        .order_by(HumanReview.id)
        .all()
    )

    audit_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.transaction_id == exception.transaction_id
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
                "message": f"Exception {exception_id} not found.",
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
                "message": "The investigation could not be completed.",
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
        validated_response = InvestigationResponse.model_validate(result)
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
)
def review_exception(
    exception_id: str,
    review: HumanReviewRequest,
    db: Session = Depends(get_db),
) -> HumanReviewResponse:
    """
    Perform a production-grade human review.
    """
    service = ExceptionService(db)

    exception = service.get_exception_by_id(exception_id)

    if exception is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "EXCEPTION_NOT_FOUND",
                "message": f"Exception {exception_id} not found.",
                "exception_id": exception_id,
            },
        )

    if exception.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "INVALID_EXCEPTION_STATE",
                "message": "Only OPEN exceptions can be reviewed.",
                "exception_id": exception_id,
                "current_status": exception.status,
            },
        )

    previous_state = exception.status

    try:
        result = service.review_exception(
            exception=exception,
            reviewer=review.reviewer,
            action=review.action,
            reason=review.reason,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "HUMAN_REVIEW_PERSISTENCE_FAILED",
                "message": "The human review could not be saved.",
                "exception_id": exception_id,
                "reason": str(error),
            },
        ) from error

    reviewed_exception = result["exception"]

    return HumanReviewResponse(
        message="Exception review recorded successfully.",
        exception_id=reviewed_exception.exception_id,
        transaction_id=reviewed_exception.transaction_id,
        reviewer=review.reviewer,
        action=review.action,
        previous_state=previous_state,
        new_state=result["new_state"],
        reason=review.reason,
        resolved_at=reviewed_exception.resolved_at,
    )