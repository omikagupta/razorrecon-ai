from sqlalchemy.orm import Session

from app.ai.prompts.exception_analysis import (
    build_exception_analysis_prompt,
)
from app.ai.providers.provider import get_ai_provider
from app.models.reconciliation import (
    Evidence,
    ExceptionRecord,
)
from app.services.reconciliation.intelligence import (
    analyze_exception,
)


def investigate_exception(
    db: Session,
    exception: ExceptionRecord,
) -> dict:
    """
    Perform an AI-assisted investigation of a reconciliation exception.

    The investigation pipeline combines:
    1. Deterministic reconciliation intelligence
    2. Supporting financial evidence
    3. Structured prompt construction
    4. Configured AI provider

    The system gracefully falls back to deterministic analysis when
    no external AI provider is configured.
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

    evidence_records = (
        db.query(Evidence)
        .filter(
            Evidence.exception_id == exception.exception_id
        )
        .order_by(Evidence.id)
        .all()
    )

    evidence = [
        {
            "evidence_type": item.evidence_type,
            "source_table": item.source_table,
            "source_record_id": item.source_record_id,
            "description": item.description,
        }
        for item in evidence_records
    ]

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

    provider = get_ai_provider()

    try:
        ai_response = provider.generate(prompt)

        return {
            "exception_id": exception.exception_id,
            "investigation_mode": "AI_ASSISTED",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": ai_response,
        }

    except RuntimeError as error:

        # -----------------------------------------------------
        # Graceful deterministic fallback
        # -----------------------------------------------------

        return {
            "exception_id": exception.exception_id,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": None,
            "fallback_reason": str(error),
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