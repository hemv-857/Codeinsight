import json
from io import BytesIO
from typing import cast

from pytest import MonkeyPatch
from workers.main import WorkerHealthHandler, get_health_payload, get_port


def test_worker_port_uses_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_WORKER_PORT", "9101")

    assert get_port() == 9101


def test_worker_health_payload() -> None:
    payload = json.loads(get_health_payload())

    assert payload == {"status": "ok", "service": "CodeInsight Worker"}


def test_worker_health_handler_serves_health_and_404() -> None:
    health_handler = handler_for_path("/health")
    missing_handler = handler_for_path("/missing")

    health_handler.do_GET()
    missing_handler.do_GET()

    assert health_handler.status_code == 200
    assert json.loads(cast(BytesIO, health_handler.wfile).getvalue().decode()) == {
        "status": "ok",
        "service": "CodeInsight Worker",
    }
    assert missing_handler.status_code == 404


class InMemoryWorkerHealthHandler(WorkerHealthHandler):
    status_code: int | None
    headers_sent: dict[str, str]
    headers_ended: bool
    error_message: str | None

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status_code = code

    def send_header(self, keyword: str, value: str) -> None:
        self.headers_sent[keyword] = value

    def end_headers(self) -> None:
        self.headers_ended = True

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        self.status_code = code
        self.error_message = message


def handler_for_path(path: str) -> InMemoryWorkerHealthHandler:
    handler = InMemoryWorkerHealthHandler.__new__(InMemoryWorkerHealthHandler)
    handler.path = path
    handler.wfile = BytesIO()
    handler.status_code = None
    handler.headers_sent = {}
    handler.headers_ended = False
    handler.error_message = None
    return handler
