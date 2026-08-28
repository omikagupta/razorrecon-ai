from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_exceptions():
    response = client.get("/api/v1/exceptions")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "exceptions" in data
    assert isinstance(data["exceptions"], list)


def test_filter_exceptions_by_status():
    response = client.get(
        "/api/v1/exceptions?status=OPEN"
    )

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "exceptions" in data

    for exception in data["exceptions"]:
        assert exception["status"] == "OPEN"


def test_filter_exceptions_by_severity():
    response = client.get(
        "/api/v1/exceptions?severity=HIGH"
    )

    assert response.status_code == 200

    data = response.json()

    for exception in data["exceptions"]:
        assert exception["severity"] == "HIGH"


def test_exception_analytics():
    response = client.get(
        "/api/v1/exceptions/analytics/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)


def test_dashboard_summary():
    response = client.get(
        "/api/v1/dashboard/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert "transactions" in data
    assert "financials" in data
    assert "exceptions" in data


def test_exception_trends():
    response = client.get(
        "/api/v1/dashboard/exception-trends"
    )

    assert response.status_code == 200

    data = response.json()

    assert "by_exception_type" in data
    assert "by_severity" in data
    assert "by_status" in data