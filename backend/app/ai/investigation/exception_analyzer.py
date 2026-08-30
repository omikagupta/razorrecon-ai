import json

from sqlalchemy.orm import Session

from app.ai.prompts.exception_analysis import (
    build_exception_analysis_prompt,
)
from app.ai.providers.provider import get_ai_provider
from app.ai.schemas.investigation import (
    AIInvestigationReport,
)
from app.models.reconciliation import (
    Evidence,
    ExceptionRecord,
)
from app.services.reconciliation.intelligence import (
    analyze_exception,
)


def collect_evidence(
    db: Session,
    exception_id: str,
) -> list[dict]:
    """
    Collect structured evidence associated with an exception.
    """

    evidence_records = (
        db.query(Evidence)
        .filter(
            Evidence.exception_id == exception_id
        )
        .order_by(Evidence.id)
        .all()
    )

    return [
        {
            "evidence_type": item.evidence_type,
            "source_table": item.source_table,
            "source_record_id": item.source_record_id,
            "description": item.description,
        }
        for item in evidence_records
    ]


def investigate_exception(
    db: Session,
    exception: ExceptionRecord,
) -> dict:
    """
    Perform an AI-assisted investigation of a reconciliation exception.

    Investigation pipeline:
    1. Deterministic reconciliation intelligence
    2. Supporting financial evidence
    3. Structured prompt construction
    4. AI-generated structured investigation
    5. Pydantic validation
    6. Deterministic fallback on AI failure
    """

    # ---------------------------------------------------------
    # 1. Deterministic intelligence
    # ---------------------------------------------------------

    intelligence = analyze_exception(
        db=db,
        exception=exception,
    )

    # ---------------------------------------------------------
    # 2. Collect evidence
    # ---------------------------------------------------------

    evidence = collect_evidence(
        db=db,
        exception_id=exception.exception_id,
    )

    # ---------------------------------------------------------
    # 3. Build investigation prompt
    # ---------------------------------------------------------

    prompt = build_exception_analysis_prompt(
        exception=exception,
        intelligence=intelligence,
        evidence=evidence,
    )

    # ---------------------------------------------------------
    # 4. Attempt AI investigation
    # ---------------------------------------------------------

    try:
        provider = get_ai_provider()
        ai_response = provider.generate(prompt)

    except RuntimeError as error:
        return {
            "exception_id": exception.exception_id,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": None,
            "fallback_reason": str(error),
            "ai_provider_status": "UNAVAILABLE",
        }

    # ---------------------------------------------------------
    # 5. Parse and validate AI response
    # ---------------------------------------------------------

    try:
        parsed_response = json.loads(ai_response)

        validated_report = (
            AIInvestigationReport.model_validate(
                parsed_response
            )
        )

    except (json.JSONDecodeError, ValueError) as error:
        return {
            "exception_id": exception.exception_id,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": None,
            "fallback_reason": (
                f"Invalid AI response: {str(error)}"
            ),
            "ai_provider_status": "INVALID_RESPONSE",
        }

    # ---------------------------------------------------------
    # 6. Return validated AI investigation
    # ---------------------------------------------------------

    return {
        "exception_id": exception.exception_id,
        "investigation_mode": "AI_ASSISTED",
        "deterministic_analysis": intelligence,
        "evidence_count": len(evidence),
        "ai_analysis": validated_report.model_dump(),
        "ai_provider_status": "SUCCESS",
    }


def investigate_all_open_exceptions(
    db: Session,
) -> list[dict]:
    """
    Run AI-assisted investigation for all currently open exceptions.
    """

    exceptions = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.status == "OPEN"
        )
        .order_by(ExceptionRecord.id)
        .all()
    )

    return [
        investigate_exception(
            db=db,
            exception=exception,
        )
        for exception in exceptions
    ]