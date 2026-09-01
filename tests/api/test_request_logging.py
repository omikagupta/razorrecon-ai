from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_logging import RequestLoggingMiddleware


def create_test_app():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    def ping():
        return {"message": "pong"}

    return app


def test_request_id_generated_when_missing():
    app = create_test_app()
    client = TestClient(app)

    response = client.get("/ping")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) > 0


def test_existing_request_id_is_preserved():
    app = create_test_app()
    client = TestClient(app)

    request_id = "test-request-123"

    response = client.get(
        "/ping",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_logging_records_lifecycle(caplog):
    app = create_test_app()
    client = TestClient(app)

    with caplog.at_level("INFO"):
        response = client.get(
            "/ping",
            headers={
                "X-Request-ID": "logging-test-123",
            },
        )

    assert response.status_code == 200

    log_messages = [
        record.getMessage()
        for record in caplog.records
    ]

    assert any(
        "request_started" in message
        for message in log_messages
    )

    assert any(
        "request_completed" in message
        for message in log_messages
    )