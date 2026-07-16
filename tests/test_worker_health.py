import json

from pytest import MonkeyPatch
from workers.main import get_health_payload, get_port


def test_worker_port_uses_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_AI_WORKER_PORT", "9101")

    assert get_port() == 9101


def test_worker_health_payload() -> None:
    payload = json.loads(get_health_payload())

    assert payload == {"status": "ok", "service": "Forge AI Worker"}
