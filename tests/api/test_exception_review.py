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

    assert response.status_code == 422


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

    assert response.status_code == 422


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

    assert response.status_code == 422

# =========================================================
# EXCEPTION LIST â€” PAGINATION & FILTERING
# =========================================================


def test_exception_list_default_pagination():
    response = client.get(
        "/api/v1/exceptions"
    )

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data
    assert "exceptions" in data

    assert data["page"] == 1
    assert data["page_size"] == 20

    assert len(data["exceptions"]) <= 20

    if data["total"] > 0:
        expected_pages = (
            (data["total"] + data["page_size"] - 1)
            // data["page_size"]
        )
        assert data["pages"] == expected_pages


def test_exception_list_custom_pagination():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "page": 2,
            "page_size": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["page_size"] == 10
    assert len(data["exceptions"]) <= 10

    if data["total"] > 0:
        expected_pages = (
            (data["total"] + data["page_size"] - 1)
            // data["page_size"]
        )
        assert data["pages"] == expected_pages


def test_exception_list_status_filter():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "status_filter": "OPEN",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1

    for exception in data["exceptions"]:
        assert exception["status"] == "OPEN"


def test_exception_list_severity_filter():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "severity": "HIGH",
        },
    )

    assert response.status_code == 200

    data = response.json()

    for exception in data["exceptions"]:
        assert exception["severity"] == "HIGH"


def test_exception_list_type_filter():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "exception_type": "AMOUNT_MISMATCH",
        },
    )

    assert response.status_code == 200

    data = response.json()

    for exception in data["exceptions"]:
        assert (
            exception["exception_type"]
            == "AMOUNT_MISMATCH"
        )


def test_exception_list_combined_filters_and_pagination():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "status_filter": "OPEN",
            "severity": "HIGH",
            "exception_type": "AMOUNT_MISMATCH",
            "page": 2,
            "page_size": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["page_size"] == 10
    assert len(data["exceptions"]) <= 10

    for exception in data["exceptions"]:
        assert exception["status"] == "OPEN"
        assert exception["severity"] == "HIGH"
        assert (
            exception["exception_type"]
            == "AMOUNT_MISMATCH"
        )


def test_exception_list_invalid_page():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_exception_list_invalid_page_size():
    response = client.get(
        "/api/v1/exceptions",
        params={
            "page_size": 101,
        },
    )

    assert response.status_code == 422
