
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.ai.investigation.exception_analyzer import (
    investigate_exception,
)


# =========================================================
# TEST HELPERS
# =========================================================


def create_test_exception():
    """
    Create a lightweight fake ExceptionRecord.

    We don't need a real database record for these tests
    because the deterministic intelligence layer is mocked.
    """

    return SimpleNamespace(
        exception_id="EXC_TEST_001",
        transaction_id="TXN_TEST_001",
        exception_type="AMOUNT_MISMATCH",
        severity="HIGH",
        status="OPEN",
        description="Test amount mismatch exception.",
    )


def create_test_db():
    """
    Create a mocked SQLAlchemy session.

    The investigation layer still queries Evidence,
    so we provide the expected SQLAlchemy query chain.
    """

    db = MagicMock()

    evidence_query = db.query.return_value
    evidence_query.filter.return_value = evidence_query
    evidence_query.order_by.return_value = evidence_query
    evidence_query.all.return_value = []

    return db


def create_valid_ai_response():
    """
    Return a valid Gemini response matching
    AIInvestigationReport exactly.
    """

    return json.dumps(
        {
            "summary": (
                "The settlement amount differs from the "
                "payment amount and requires investigation."
            ),
            "root_cause": (
                "The recorded settlement does not fully "
                "match the payment amount."
            ),
            "risk_level": "HIGH",
            "recommended_action": "HUMAN_REVIEW",
            "confidence": 0.95,
            "key_evidence": [
                "Payment and settlement amounts do not match."
            ],
            "unresolved_questions": [
                "Why was the settlement amount different?"
            ],
        }
    )


# =========================================================
# TEST 1 — AI ASSISTED INVESTIGATION
# =========================================================


@patch(
    "app.ai.investigation.exception_analyzer.get_ai_provider"
)
@patch(
    "app.ai.investigation.exception_analyzer.build_exception_analysis_prompt"
)
@patch(
    "app.ai.investigation.exception_analyzer.analyze_exception"
)
def test_ai_assisted_investigation(
    mock_analyze_exception,
    mock_build_prompt,
    mock_get_provider,
):
    """
    Verify the complete successful AI investigation path.

    Expected flow:

        deterministic analysis
                ↓
        prompt construction
                ↓
        mocked Gemini
                ↓
        JSON parsing
                ↓
        Pydantic validation
                ↓
        AI_ASSISTED / SUCCESS
    """

    db = create_test_db()
    exception = create_test_exception()

    mock_analyze_exception.return_value = {
        "exception_id": "EXC_TEST_001",
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
        "recommended_action": "HUMAN_REVIEW",
        "root_cause": "Settlement amount does not match payment amount.",
    }

    mock_build_prompt.return_value = "test investigation prompt"

    mock_provider = MagicMock()
    mock_provider.generate.return_value = (
        create_valid_ai_response()
    )

    mock_get_provider.return_value = mock_provider

    result = investigate_exception(
        db=db,
        exception=exception,
    )

    # -----------------------------------------------------
    # Core result assertions
    # -----------------------------------------------------

    assert result["exception_id"] == "EXC_TEST_001"

    assert result["investigation_mode"] == "AI_ASSISTED"

    assert result["ai_provider_status"] == "SUCCESS"

    assert result["ai_analysis"] is not None

    # -----------------------------------------------------
    # Structured AI response assertions
    # -----------------------------------------------------

    ai_analysis = result["ai_analysis"]

    assert ai_analysis["summary"]

    assert ai_analysis["root_cause"]

    assert ai_analysis["risk_level"] == "HIGH"

    assert (
        ai_analysis["recommended_action"]
        == "HUMAN_REVIEW"
    )

    assert ai_analysis["confidence"] == 0.95

    assert isinstance(
        ai_analysis["key_evidence"],
        list,
    )

    assert isinstance(
        ai_analysis["unresolved_questions"],
        list,
    )

    # -----------------------------------------------------
    # Verify deterministic analysis was preserved
    # -----------------------------------------------------

    assert (
        result["deterministic_analysis"]["classification"]
        == "UNEXPLAINED_AMOUNT_MISMATCH"
    )

    # -----------------------------------------------------
    # Verify Gemini was actually mocked and called
    # -----------------------------------------------------

    mock_provider.generate.assert_called_once_with(
        "test investigation prompt"
    )

    mock_get_provider.assert_called_once()

    mock_build_prompt.assert_called_once()

    mock_analyze_exception.assert_called_once_with(
        db=db,
        exception=exception,
    )


# =========================================================
# TEST 2 — GEMINI UNAVAILABLE
# =========================================================


@patch(
    "app.ai.investigation.exception_analyzer.get_ai_provider"
)
@patch(
    "app.ai.investigation.exception_analyzer.build_exception_analysis_prompt"
)
@patch(
    "app.ai.investigation.exception_analyzer.analyze_exception"
)
def test_deterministic_fallback_when_gemini_unavailable(
    mock_analyze_exception,
    mock_build_prompt,
    mock_get_provider,
):
    """
    Verify that Gemini/API unavailability does not crash
    the investigation.

    Expected:

        RuntimeError
            ↓
        DETERMINISTIC_FALLBACK
            ↓
        UNAVAILABLE
    """

    db = create_test_db()
    exception = create_test_exception()

    mock_analyze_exception.return_value = {
        "exception_id": "EXC_TEST_001",
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
        "recommended_action": "HUMAN_REVIEW",
        "root_cause": "Settlement amount does not match payment amount.",
    }

    mock_build_prompt.return_value = "test investigation prompt"

    mock_provider = MagicMock()

    mock_provider.generate.side_effect = RuntimeError(
        "Gemini generation failed: API unavailable"
    )

    mock_get_provider.return_value = mock_provider

    result = investigate_exception(
        db=db,
        exception=exception,
    )

    # -----------------------------------------------------
    # Fallback assertions
    # -----------------------------------------------------

    assert (
        result["investigation_mode"]
        == "DETERMINISTIC_FALLBACK"
    )

    assert (
        result["ai_provider_status"]
        == "UNAVAILABLE"
    )

    assert result["ai_analysis"] is None

    assert result["fallback_reason"]

    assert (
        "API unavailable"
        in result["fallback_reason"]
    )

    # -----------------------------------------------------
    # Deterministic analysis must survive the AI failure
    # -----------------------------------------------------

    assert (
        result["deterministic_analysis"]["classification"]
        == "UNEXPLAINED_AMOUNT_MISMATCH"
    )

    # -----------------------------------------------------
    # Verify Gemini was called exactly once
    # -----------------------------------------------------

    mock_provider.generate.assert_called_once_with(
        "test investigation prompt"
    )


# =========================================================
# TEST 3 — INVALID JSON FROM GEMINI
# =========================================================


@patch(
    "app.ai.investigation.exception_analyzer.get_ai_provider"
)
@patch(
    "app.ai.investigation.exception_analyzer.build_exception_analysis_prompt"
)
@patch(
    "app.ai.investigation.exception_analyzer.analyze_exception"
)
def test_deterministic_fallback_when_gemini_returns_invalid_json(
    mock_analyze_exception,
    mock_build_prompt,
    mock_get_provider,
):
    """
    Verify that malformed Gemini output is safely handled.

    Expected:

        Invalid JSON
            ↓
        JSONDecodeError
            ↓
        DETERMINISTIC_FALLBACK
            ↓
        INVALID_RESPONSE
    """

    db = create_test_db()
    exception = create_test_exception()

    mock_analyze_exception.return_value = {
        "exception_id": "EXC_TEST_001",
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
        "recommended_action": "HUMAN_REVIEW",
        "root_cause": "Settlement amount does not match payment amount.",
    }

    mock_build_prompt.return_value = "test investigation prompt"

    mock_provider = MagicMock()

    mock_provider.generate.return_value = (
        "This is not valid JSON."
    )

    mock_get_provider.return_value = mock_provider

    result = investigate_exception(
        db=db,
        exception=exception,
    )

    # -----------------------------------------------------
    # Fallback assertions
    # -----------------------------------------------------

    assert (
        result["investigation_mode"]
        == "DETERMINISTIC_FALLBACK"
    )

    assert (
        result["ai_provider_status"]
        == "INVALID_RESPONSE"
    )

    assert result["ai_analysis"] is None

    assert result["fallback_reason"]

    assert (
        "Invalid AI response"
        in result["fallback_reason"]
    )

    # -----------------------------------------------------
    # Deterministic analysis remains available
    # -----------------------------------------------------

    assert (
        result["deterministic_analysis"]["classification"]
        == "UNEXPLAINED_AMOUNT_MISMATCH"
    )

    mock_provider.generate.assert_called_once_with(
        "test investigation prompt"
    )


# =========================================================
# TEST 4 — PYDANTIC STRUCTURED RESPONSE VALIDATION
# =========================================================


@patch(
    "app.ai.investigation.exception_analyzer.get_ai_provider"
)
@patch(
    "app.ai.investigation.exception_analyzer.build_exception_analysis_prompt"
)
@patch(
    "app.ai.investigation.exception_analyzer.analyze_exception"
)
def test_deterministic_fallback_when_ai_response_fails_validation(
    mock_analyze_exception,
    mock_build_prompt,
    mock_get_provider,
):
    """
    Verify that syntactically valid JSON is still rejected
    when it does not satisfy AIInvestigationReport.

    This protects the API from structurally invalid LLM output.
    """

    db = create_test_db()
    exception = create_test_exception()

    mock_analyze_exception.return_value = {
        "exception_id": "EXC_TEST_001",
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
        "recommended_action": "HUMAN_REVIEW",
        "root_cause": "Settlement amount does not match payment amount.",
    }

    mock_build_prompt.return_value = "test investigation prompt"

    mock_provider = MagicMock()

    # Valid JSON, but INVALID AIInvestigationReport.
    # "summary" is intentionally missing.
    mock_provider.generate.return_value = json.dumps(
        {
            "root_cause": "Settlement mismatch.",
            "risk_level": "HIGH",
            "recommended_action": "HUMAN_REVIEW",
            "confidence": 0.95,
            "key_evidence": [],
            "unresolved_questions": [],
        }
    )

    mock_get_provider.return_value = mock_provider

    result = investigate_exception(
        db=db,
        exception=exception,
    )

    # -----------------------------------------------------
    # Validation failure must become safe fallback
    # -----------------------------------------------------

    assert (
        result["investigation_mode"]
        == "DETERMINISTIC_FALLBACK"
    )

    assert (
        result["ai_provider_status"]
        == "INVALID_RESPONSE"
    )

    assert result["ai_analysis"] is None

    assert result["fallback_reason"]

    assert (
        "Invalid AI response"
        in result["fallback_reason"]
    )

    # -----------------------------------------------------
    # Deterministic result remains available
    # -----------------------------------------------------

    assert (
        result["deterministic_analysis"]["classification"]
        == "UNEXPLAINED_AMOUNT_MISMATCH"
    )

    mock_provider.generate.assert_called_once_with(
        "test investigation prompt"
    )

