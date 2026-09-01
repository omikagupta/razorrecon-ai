from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_root():
    response = client.get("/api/v1")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "RazorRecon AI"
    assert data["version"] == "0.2.0"
    assert data["status"] == "running"


def test_liveness_check():
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "alive"
    assert data["service"] == "RazorRecon AI"


@patch("app.main.engine.connect")
def test_health_check_database_healthy(mock_connect):
    mock_connection = Mock()
    mock_connect.return_value.__enter__.return_value = mock_connection

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "healthy"


@patch("app.main.engine.connect")
def test_health_check_database_unhealthy(mock_connect):
    mock_connect.side_effect = Exception("Database unavailable")

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "degraded"
    assert data["database"] == "unhealthy"


@patch("app.main.engine.connect")
def test_readiness_check_database_healthy(mock_connect):
    mock_connection = Mock()
    mock_connect.return_value.__enter__.return_value = mock_connection

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["database"] == "healthy"


@patch("app.main.engine.connect")
def test_readiness_check_database_unhealthy(mock_connect):
    mock_connect.side_effect = Exception("Database unavailable")

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_ready"
    assert data["database"] == "unhealthy"