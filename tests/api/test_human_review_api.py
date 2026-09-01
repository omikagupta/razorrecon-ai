from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# =========================================================
# TEST DATA
# =========================================================

VALID_REVIEW = {
    "reviewer": "test_reviewer",
    "action": "APPROVE",
    "reason": "Evidence confirms the exception is resolved.",
}


# =========================================================
# TEST 1 — EXCEPTION NOT FOUND
# =========================================================

def test_review_exception_not_found():
    response = client.post(
        "/api/v1/exceptions/EXC_DOES_NOT_EXIST/review",
        json=VALID_REVIEW,
    )

    assert response.status_code == 404

    data = response.json()

    assert data["error"] == "EXCEPTION_NOT_FOUND"
    assert data["exception_id"] == "EXC_DOES_NOT_EXIST"


# =========================================================
# TEST 2 — INVALID ACTION
# =========================================================

def test_review_invalid_action():
    payload = {
        "reviewer": "test_reviewer",
        "action": "INVALID_ACTION",
        "reason": "Testing invalid action validation.",
    }

    response = client.post(
        "/api/v1/exceptions/EXC_TEST_001/review",
        json=payload,
    )

    assert response.status_code == 422


# =========================================================
# TEST 3 — EMPTY REVIEWER
# =========================================================

def test_review_empty_reviewer():
    payload = {
        "reviewer": "   ",
        "action": "APPROVE",
        "reason": "Testing reviewer validation.",
    }

    response = client.post(
        "/api/v1/exceptions/EXC_TEST_001/review",
        json=payload,
    )

    assert response.status_code == 422


# =========================================================
# TEST 4 — EMPTY REASON
# =========================================================

def test_review_empty_reason():
    payload = {
        "reviewer": "test_reviewer",
        "action": "APPROVE",
        "reason": "   ",
    }

    response = client.post(
        "/api/v1/exceptions/EXC_TEST_001/review",
        json=payload,
    )

    assert response.status_code == 422


# =========================================================
# TEST 5 — SUCCESSFUL APPROVE REVIEW
# =========================================================

def test_review_approve_success():
    list_response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    if not exceptions:
        return

    exception_id = exceptions[0]["exception_id"]

    payload = {
        "reviewer": "test_reviewer",
        "action": "APPROVE",
        "reason": "Evidence confirms the issue is resolved.",
    }

    response = client.post(
        f"/api/v1/exceptions/{exception_id}/review",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["exception_id"] == exception_id
    assert data["action"] == "APPROVE"
    assert data["previous_state"] == "OPEN"
    assert data["new_state"] == "RESOLVED"
    assert data["reviewer"] == "test_reviewer"
    assert data["resolved_at"] is not None


# =========================================================
# TEST 6 — REVIEWING CLOSED EXCEPTION
# =========================================================

def test_review_already_reviewed_exception():
    list_response = client.get(
        "/api/v1/exceptions"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    closed_exception = next(
        (
            exception
            for exception in exceptions
            if exception["status"] != "OPEN"
        ),
        None,
    )

    if closed_exception is None:
        return

    exception_id = closed_exception["exception_id"]

    payload = {
        "reviewer": "test_reviewer",
        "action": "APPROVE",
        "reason": "Attempting duplicate review.",
    }

    response = client.post(
        f"/api/v1/exceptions/{exception_id}/review",
        json=payload,
    )

    assert response.status_code == 409

    data = response.json()

    assert data["error"] == "INVALID_EXCEPTION_STATE"
    assert data["exception_id"] == exception_id


# =========================================================
# TEST 7 — ACTION NORMALIZATION
# =========================================================

def test_review_action_is_normalized():
    list_response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert list_response.status_code == 200

    exceptions = list_response.json()["exceptions"]

    if not exceptions:
        return

    exception_id = exceptions[0]["exception_id"]

    payload = {
        "reviewer": "test_reviewer",
        "action": "escalate",
        "reason": "Requires additional investigation.",
    }

    response = client.post(
        f"/api/v1/exceptions/{exception_id}/review",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "ESCALATE"
    assert data["previous_state"] == "OPEN"
    assert data["new_state"] == "ESCALATED"