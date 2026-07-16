from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient


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


def test_openapi_uses_configured_metadata() -> None:
    settings = Settings(app_name="Forge AI Test", environment="test", version="1.2.3")
    client = TestClient(create_app(settings))

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"] == {"title": "Forge AI Test", "version": "1.2.3"}
