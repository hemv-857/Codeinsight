import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_compose_config() -> dict[str, Any]:
    result = subprocess.run(
        ["docker-compose", "config", "--format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    config = json.loads(result.stdout)
    if not isinstance(config, dict):
        raise TypeError("docker-compose config did not return a JSON object")
    return config


def test_compose_includes_required_services() -> None:
    config = load_compose_config()

    assert set(config["services"]) == {"backend", "frontend", "neo4j", "redis", "worker"}


def test_compose_services_have_healthchecks() -> None:
    config = load_compose_config()

    missing_healthchecks = [
        name for name, service in config["services"].items() if "healthcheck" not in service
    ]

    assert missing_healthchecks == []


def test_compose_declares_persistent_volumes() -> None:
    config = load_compose_config()

    assert set(config["volumes"]) == {
        "graph-data",
        "neo4j-data",
        "redis-data",
        "repository-data",
    }
