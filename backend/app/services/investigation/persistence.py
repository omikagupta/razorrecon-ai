import json
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.reconciliation import Investigation


def _make_json_serializable(value):
    """
    Convert nested values into JSON-safe Python structures.

    This protects persistence when deterministic analysis contains
    Decimal, datetime, or other non-JSON-native values.
    """

    return json.loads(
        json.dumps(
            value,
            default=str,
        )
    )


def persist_investigation(
    db: Session,
    investigation_result: dict,
) -> Investigation:
    """
    Persist an exception investigation result.

    The investigation service is responsible for generating the
    result; this service is responsible only for durable storage.
    """

    investigation = Investigation(
        investigation_id=(
            f"INV_{uuid4().hex[:16].upper()}"
        ),
        exception_id=investigation_result["exception_id"],
        investigation_mode=investigation_result[
            "investigation_mode"
        ],
        ai_provider_status=investigation_result[
            "ai_provider_status"
        ],
        evidence_count=investigation_result[
            "evidence_count"
        ],
        deterministic_analysis=_make_json_serializable(
            investigation_result["deterministic_analysis"]
        ),
        ai_analysis=_make_json_serializable(
            investigation_result["ai_analysis"]
        )
        if investigation_result.get("ai_analysis")
        else None,
        fallback_reason=investigation_result.get(
            "fallback_reason"
        ),
    )

    try:
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

    except Exception:
        db.rollback()
        raise

    return investigation