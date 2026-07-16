import logging

from backend.app.core.config import Settings
from backend.app.core.errors import REQUEST_ID_HEADER
from backend.app.main import create_app
from fastapi.testclient import TestClient
from pytest import LogCaptureFixture


def test_not_found_errors_use_public_error_envelope() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/api/missing")

    assert response.status_code == 404
    assert response.headers[REQUEST_ID_HEADER]
    assert response.json() == {
        "error": "not_found",
        "detail": "Not Found",
        "status_code": 404,
        "request_id": response.headers[REQUEST_ID_HEADER],
    }


def test_error_envelope_preserves_request_id_header() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/api/missing", headers={REQUEST_ID_HEADER: "demo-request"})

    assert response.status_code == 404
    assert response.headers[REQUEST_ID_HEADER] == "demo-request"
    assert response.json()["request_id"] == "demo-request"


def test_validation_errors_are_readable_and_structured() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post("/api/repositories/scan", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["status_code"] == 422
    assert body["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert "repository_path" in body["detail"]
    assert "Traceback" not in body["detail"]


def test_unhandled_errors_are_logged_and_sanitized(caplog: LogCaptureFixture) -> None:
    app = create_app(Settings(environment="test"))

    @app.get("/api/boom")
    def boom() -> None:
        raise RuntimeError("database password leaked")

    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR):
        response = client.get("/api/boom", headers={REQUEST_ID_HEADER: "failure-request"})

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER] == "failure-request"
    assert response.json() == {
        "error": "internal_server_error",
        "detail": "Internal server error.",
        "status_code": 500,
        "request_id": "failure-request",
    }
    assert "database password leaked" not in response.text
    assert any(
        getattr(record, "request_id", None) == "failure-request" for record in caplog.records
    )
