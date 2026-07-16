import logging
from inspect import iscoroutinefunction
from typing import Any

from backend.app.api.routes.repositories import router as repositories_router
from backend.app.core.config import Settings
from backend.app.core.logging import configure_logging
from backend.app.main import create_app
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def test_health_endpoint_returns_backend_status() -> None:
    settings = Settings(app_name="Forge AI Test", environment="test", version="1.2.3")
    client = TestClient(create_app(settings))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Forge AI Test",
        "environment": "test",
        "version": "1.2.3",
    }


def test_backend_allows_local_dashboard_cors_preflight() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3002"


def test_repository_endpoints_run_on_event_loop() -> None:
    sync_endpoints = [
        route.name
        for route in repositories_router.routes
        if isinstance(route, APIRoute) and not iscoroutinefunction(route.endpoint)
    ]

    assert sync_endpoints == []


def test_openapi_uses_configured_metadata() -> None:
    settings = Settings(app_name="Forge AI Test", environment="test", version="1.2.3")
    client = TestClient(create_app(settings))

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"] == {"title": "Forge AI Test", "version": "1.2.3"}


def test_create_app_uses_default_settings() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["service"] == "Forge AI"


def test_configure_logging_applies_configured_level(monkeypatch: MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def capture_basic_config(**kwargs: Any) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(logging, "basicConfig", capture_basic_config)

    configure_logging(Settings(environment="test", log_level="ERROR"))

    assert calls[0]["level"] == "ERROR"
    assert "%(levelname)s" in calls[0]["format"]
