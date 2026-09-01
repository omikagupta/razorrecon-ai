import pytest

from app.models.reconciliation import Investigation
from app.services.investigation.persistence import (
    persist_investigation,
)


def create_investigation_result():
    return {
        "exception_id": "EXC_TEST_001",
        "investigation_mode": "AI_ASSISTED",
        "ai_provider_status": "SUCCESS",
        "evidence_count": 2,
        "deterministic_analysis": {
            "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
            "confidence": 0.95,
        },
        "ai_analysis": {
            "summary": "Settlement amount differs from payment amount.",
            "root_cause": "Settlement mismatch.",
            "risk_level": "HIGH",
            "recommended_action": "HUMAN_REVIEW",
            "confidence": 0.95,
            "key_evidence": [
                "Payment amount does not match settlement amount."
            ],
            "unresolved_questions": [
                "Why was the settlement amount different?"
            ],
        },
        "fallback_reason": None,
    }


def test_persist_investigation_success(db):
    result = persist_investigation(
        db=db,
        investigation_result=create_investigation_result(),
    )

    assert result.investigation_id.startswith("INV_")
    assert result.exception_id == "EXC_TEST_001"
    assert result.investigation_mode == "AI_ASSISTED"
    assert result.ai_provider_status == "SUCCESS"
    assert result.evidence_count == 2

    stored = (
        db.query(Investigation)
        .filter(
            Investigation.investigation_id
            == result.investigation_id
        )
        .one()
    )

    assert stored.exception_id == "EXC_TEST_001"
    assert stored.deterministic_analysis[
        "classification"
    ] == "UNEXPLAINED_AMOUNT_MISMATCH"

    assert stored.ai_analysis["risk_level"] == "HIGH"


def test_persist_investigation_fallback_without_ai_analysis(db):
    result_data = create_investigation_result()

    result_data["investigation_mode"] = (
        "DETERMINISTIC_FALLBACK"
    )
    result_data["ai_provider_status"] = "UNAVAILABLE"
    result_data["ai_analysis"] = None
    result_data["fallback_reason"] = (
        "Gemini generation failed: API unavailable"
    )

    result = persist_investigation(
        db=db,
        investigation_result=result_data,
    )

    assert result.investigation_mode == (
        "DETERMINISTIC_FALLBACK"
    )

    assert result.ai_provider_status == "UNAVAILABLE"
    assert result.ai_analysis is None
    assert result.fallback_reason == (
        "Gemini generation failed: API unavailable"
    )


def test_persist_investigation_serializes_non_json_values(db):
    from datetime import datetime
    from decimal import Decimal

    result_data = create_investigation_result()

    result_data["deterministic_analysis"] = {
        "amount": Decimal("100.50"),
        "timestamp": datetime.now(),
    }

    result = persist_investigation(
        db=db,
        investigation_result=result_data,
    )

    assert result.deterministic_analysis["amount"] == (
        "100.50"
    )

    assert isinstance(
        result.deterministic_analysis["timestamp"],
        str,
    )


def test_persist_investigation_rolls_back_on_database_failure():
    from unittest.mock import MagicMock

    db = MagicMock()

    db.commit.side_effect = RuntimeError(
        "Database commit failed"
    )

    with pytest.raises(
        RuntimeError,
        match="Database commit failed",
    ):
        persist_investigation(
            db=db,
            investigation_result=create_investigation_result(),
        )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_called_once()