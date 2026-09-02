from sqlalchemy.orm import Session

from app.ai.parsers.response_parser import (
    parse_ai_json_response,
)
from app.services.investigation.persistence import (
    persist_investigation,
)
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
    evidence_records = (
        db.query(Evidence)
        .filter(Evidence.exception_id == exception_id)
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

        # Parse potentially imperfect AI JSON output.
        parsed_response = parse_ai_json_response(ai_response)

        # Strict schema validation.
        validated_report = AIInvestigationReport.model_validate(parsed_response)

        result = {
            "exception_id": exception.exception_id,
            "investigation_mode": "AI_ASSISTED",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": validated_report.model_dump(),
            "ai_provider_status": "SUCCESS",
            "fallback_reason": None,
        }

    except RuntimeError as error:
        result = {
            "exception_id": exception.exception_id,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": None,
            "fallback_reason": str(error),
            "ai_provider_status": "UNAVAILABLE",
        }

    except ValueError as error:
        result = {
            "exception_id": exception.exception_id,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "deterministic_analysis": intelligence,
            "evidence_count": len(evidence),
            "ai_analysis": None,
            "fallback_reason": f"Invalid AI response: {str(error)}",
            "ai_provider_status": "INVALID_RESPONSE",
        }

    # ---------------------------------------------------------
    # 5. Persist investigation
    # ---------------------------------------------------------

    persisted_investigation = persist_investigation(
        db=db,
        investigation_result=result,
    )

    result["investigation_id"] = persisted_investigation.investigation_id

    return result


def investigate_all_open_exceptions(
    db: Session,
) -> list[dict]:
    exceptions = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.status == "OPEN")
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