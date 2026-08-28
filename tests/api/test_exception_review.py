from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.reconciliation import ExceptionRecord


client = TestClient(app)


def get_open_exception():
    db = SessionLocal()

    try:
        return (
            db.query(ExceptionRecord)
            .filter(ExceptionRecord.status == "OPEN")
            .first()
        )
    finally:
        db.close()


def test_exception_investigation():
    exception = get_open_exception()

    assert exception is not None

    response = client.get(
        f"/api/v1/exceptions/{exception.exception_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert "exception" in data
    assert "intelligence" in data
    assert "evidence" in data
    assert "human_reviews" in data
    assert "audit_logs" in data


def test_invalid_review_action():
    exception = get_open_exception()

    assert exception is not None

    response = client.post(
        f"/api/v1/exceptions/{exception.exception_id}/review",
        json={
            "reviewer": "test-reviewer",
            "action": "INVALID",
            "reason": "Testing invalid action.",
        },
    )

    assert response.status_code == 400


def test_empty_reviewer_rejected():
    exception = get_open_exception()

    assert exception is not None

    response = client.post(
        f"/api/v1/exceptions/{exception.exception_id}/review",
        json={
            "reviewer": "",
            "action": "APPROVE",
            "reason": "Testing validation.",
        },
    )

    assert response.status_code == 400


def test_empty_reason_rejected():
    exception = get_open_exception()

    assert exception is not None

    response = client.post(
        f"/api/v1/exceptions/{exception.exception_id}/review",
        json={
            "reviewer": "test-reviewer",
            "action": "APPROVE",
            "reason": "",
        },
    )

    assert response.status_code == 400