import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 8001

logger = logging.getLogger(__name__)


def get_health_payload() -> bytes:
    """Return the worker health response body."""
    return json.dumps({"status": "ok", "service": "Forge AI Worker"}).encode()


class WorkerHealthHandler(BaseHTTPRequestHandler):
    """HTTP handler exposing worker liveness for Docker health checks."""

    server_version = "ForgeAIWorker/0.1.0"

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404, "Not Found")
            return

        payload = get_health_payload()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        logger.info(format, *args)


def get_port() -> int:
    """Return the configured worker health port."""
    raw_port = os.getenv("FORGE_AI_WORKER_PORT", str(DEFAULT_PORT))
    return int(raw_port)


def run() -> None:
    """Start the worker health server."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=os.getenv("FORGE_AI_LOG_LEVEL", "INFO"),
    )
    port = get_port()
    logger.info("Forge AI worker started", extra={"port": port})

    with ThreadingHTTPServer((HOST, port), WorkerHealthHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    run()
