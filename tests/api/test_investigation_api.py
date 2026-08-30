
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# =========================================================
# TEST DATA
# =========================================================


VALID_AI_ANALYSIS = {
    "summary": (
        "The settlement amount differs from the payment "
        "amount and requires human review."
    ),
    "root_cause": (
        "Settlement amount does not match the original "
        "payment amount."
    ),
    "risk_level": "HIGH",
    "recommended_action": "HUMAN_REVIEW",
    "confidence": 0.95,
    "key_evidence": [
        "Payment amount differs from settlement amount."
    ],
    "unresolved_questions": [
        "Why did the settlement amount differ?"
    ],
}


VALID_INVESTIGATION_RESULT = {
    "exception_id": "EXC_TEST_001",
    "investigation_mode": "AI_ASSISTED",
    "ai_provider_status": "SUCCESS",
    "evidence_count": 15,
    "deterministic_analysis": {
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
    },
    "ai_analysis": VALID_AI_ANALYSIS,
}


FALLBACK_INVESTIGATION_RESULT = {
    "exception_id": "EXC_TEST_001",
    "investigation_mode": "DETERMINISTIC_FALLBACK",
    "ai_provider_status": "UNAVAILABLE",
    "evidence_count": 15,
    "deterministic_analysis": {
        "classification": "UNEXPLAINED_AMOUNT_MISMATCH",
        "severity": "HIGH",
        "confidence": 0.95,
    },
    "ai_analysis": None,
    "fallback_reason": (
        "Gemini generation failed: API unavailable"
    ),
}


# =========================================================
# TEST 1 — NOT FOUND
# =========================================================


def test_investigation_exception_not_found():
    response = client.post(
        "/api/v1/exceptions/EXC_DOES_NOT_EXIST/investigate"
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data

    assert (
        data["detail"]["error"]
        == "EXCEPTION_NOT_FOUND"
    )

    assert (
        data["detail"]["exception_id"]
        == "EXC_DOES_NOT_EXIST"
    )


# =========================================================
# TEST 2 — AI ASSISTED RESPONSE
# =========================================================


@patch(
    "app.api.v1.exceptions.investigate_exception"
)
def test_investigation_ai_assisted(
    mock_investigate,
):
    """
    Verify that the endpoint exposes a clean structured
    AI-assisted response.
    """

    # -----------------------------------------------------
    # Find an existing exception from the real test database
    # -----------------------------------------------------

    list_response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    if not exceptions:
        return

    exception_id = exceptions[0]["exception_id"]

    mock_result = {
        **VALID_INVESTIGATION_RESULT,
        "exception_id": exception_id,
    }

    mock_investigate.return_value = mock_result

    response = client.post(
        f"/api/v1/exceptions/"
        f"{exception_id}/investigate"
    )

    assert response.status_code == 200

    data = response.json()

    # -----------------------------------------------------
    # Top-level response
    # -----------------------------------------------------

    assert data["exception_id"] == exception_id

    assert (
        data["investigation_mode"]
        == "AI_ASSISTED"
    )

    assert (
        data["ai_provider_status"]
        == "SUCCESS"
    )

    assert data["evidence_count"] == 15

    # -----------------------------------------------------
    # AI response
    # -----------------------------------------------------

    assert data["ai_analysis"] is not None

    assert (
        data["ai_analysis"]["summary"]
    )

    assert (
        data["ai_analysis"]["root_cause"]
    )

    assert (
        data["ai_analysis"]["risk_level"]
        == "HIGH"
    )

    assert (
        data["ai_analysis"]["recommended_action"]
        == "HUMAN_REVIEW"
    )

    assert (
        data["ai_analysis"]["confidence"]
        == 0.95
    )

    # -----------------------------------------------------
    # Verify service call
    # -----------------------------------------------------

    mock_investigate.assert_called_once()


# =========================================================
# TEST 3 — DETERMINISTIC FALLBACK
# =========================================================


@patch(
    "app.api.v1.exceptions.investigate_exception"
)
def test_investigation_deterministic_fallback(
    mock_investigate,
):
    """
    Verify that a deterministic fallback is exposed
    cleanly through the API.
    """

    list_response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    if not exceptions:
        return

    exception_id = exceptions[0]["exception_id"]

    mock_result = {
        **FALLBACK_INVESTIGATION_RESULT,
        "exception_id": exception_id,
    }

    mock_investigate.return_value = mock_result

    response = client.post(
        f"/api/v1/exceptions/"
        f"{exception_id}/investigate"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["investigation_mode"]
        == "DETERMINISTIC_FALLBACK"
    )

    assert (
        data["ai_provider_status"]
        == "UNAVAILABLE"
    )

    assert data["ai_analysis"] is None

    assert data["fallback_reason"]


# =========================================================
# TEST 4 — API RESPONSE STRUCTURE
# =========================================================


@patch(
    "app.api.v1.exceptions.investigate_exception"
)
def test_investigation_response_has_production_structure(
    mock_investigate,
):
    """
    Verify that the API does not expose an arbitrary
    dictionary structure.
    """

    list_response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    if not exceptions:
        return

    exception_id = exceptions[0]["exception_id"]

    mock_investigate.return_value = {
        **VALID_INVESTIGATION_RESULT,
        "exception_id": exception_id,
    }

    response = client.post(
        f"/api/v1/exceptions/"
        f"{exception_id}/investigate"
    )

    assert response.status_code == 200

    data = response.json()

    # Required top-level fields
    required_fields = {
        "exception_id",
        "investigation_mode",
        "ai_provider_status",
        "evidence_count",
        "deterministic_analysis",
        "ai_analysis",
    }

    assert required_fields.issubset(
        data.keys()
    )

    # Correct types
    assert isinstance(
        data["exception_id"],
        str,
    )

    assert isinstance(
        data["investigation_mode"],
        str,
    )

    assert isinstance(
        data["ai_provider_status"],
        str,
    )

    assert isinstance(
        data["evidence_count"],
        int,
    )

    assert isinstance(
        data["deterministic_analysis"],
        dict,
    )

