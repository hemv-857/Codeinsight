import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.architecture_violations import ArchitectureViolationService
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_violation_fixture(path: Path) -> None:
    write_file(
        path / "api" / "routes" / "users.py",
        (
            "from repositories.user import UserRepository\n\n\n"
            "def route():\n    return UserRepository\n"
        ),
    )
    write_file(
        path / "repositories" / "user.py",
        "from api.routes.users import route\n\n\nclass UserRepository:\n    pass\n",
    )
    write_file(path / "services" / "billing.py", "from components.panel import Panel\n")
    write_file(path / "components" / "panel.py", "class Panel:\n    pass\n")
    write_file(path / "core" / "job.py", "from tests.helpers import helper\n")
    write_file(path / "tests" / "helpers.py", "def helper():\n    return 1\n")


def create_git_repository(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "forge@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CodeInsight"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    create_violation_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service() -> ArchitectureViolationService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return ArchitectureViolationService(
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser)
    )


def test_architecture_violation_service_reports_layer_violations(tmp_path: Path) -> None:
    create_violation_fixture(tmp_path)

    report = create_service().detect(tmp_path)

    rule_ids = {violation.rule_id for violation in report.violations}
    assert "api-skips-service-layer" in rule_ids
    assert "persistence-depends-on-interface" in rule_ids
    assert "production-imports-test" in rule_ids
    assert "service-depends-on-ui" in rule_ids
    assert report.stats.violation_count == len(report.violations)
    assert report.stats.critical_count >= 1


def test_architecture_violation_api_for_repository_path(tmp_path: Path) -> None:
    create_violation_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/architecture-violations",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["violation_count"] >= 4
    assert any(
        violation["rule_id"] == "api-skips-service-layer" for violation in body["violations"]
    )


def test_architecture_violation_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    client = TestClient(
        create_app(Settings(environment="test", repository_storage_path=tmp_path / "imports"))
    )

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    violation_response = client.get(
        f"/api/repositories/imports/{import_id}/architecture-violations"
    )

    assert violation_response.status_code == 200
    assert violation_response.json()["stats"]["violation_count"] >= 4
