import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.dead_code import DeadCodeService
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_dead_code_fixture(path: Path) -> None:
    write_file(
        path / "app.py",
        "from util import used\n\n\ndef start():\n    used()\n",
    )
    write_file(
        path / "util.py",
        "def used():\n    return 1\n\n\ndef unused_helper():\n    return 2\n",
    )
    write_file(path / "orphan.py", "def orphaned():\n    return 3\n")
    write_file(path / "tests" / "test_util.py", "def test_placeholder():\n    assert True\n")


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
        ["git", "config", "user.name", "Forge AI"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    create_dead_code_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service() -> DeadCodeService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return DeadCodeService(
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        call_graph=CallGraphService(scanner=scanner, parser=parser),
    )


def test_dead_code_service_reports_unused_files_and_callables(tmp_path: Path) -> None:
    create_dead_code_fixture(tmp_path)

    report = create_service().detect(tmp_path)

    findings = {(finding.kind, finding.path, finding.symbol_name) for finding in report.findings}
    assert ("unused_file", "orphan.py", None) in findings
    assert ("unused_callable", "util.py", "unused_helper") in findings
    assert ("unused_callable", "util.py", "used") not in findings
    assert all("tests/" not in finding.path for finding in report.findings)
    assert report.stats.unused_file_count >= 1
    assert report.stats.unused_callable_count >= 1


def test_dead_code_api_for_repository_path(tmp_path: Path) -> None:
    create_dead_code_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post("/api/repositories/dead-code", json={"repository_path": str(tmp_path)})

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["finding_count"] >= 2
    assert any(finding["kind"] == "unused_file" for finding in body["findings"])
    assert any(finding["symbol_name"] == "unused_helper" for finding in body["findings"])


def test_dead_code_api_for_imported_repository(tmp_path: Path) -> None:
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

    dead_code_response = client.get(f"/api/repositories/imports/{import_id}/dead-code")

    assert dead_code_response.status_code == 200
    assert dead_code_response.json()["stats"]["unused_callable_count"] >= 1
