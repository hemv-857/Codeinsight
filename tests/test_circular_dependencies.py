import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.circular_dependencies import CircularDependencyService
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_cycle_fixture(path: Path) -> None:
    write_file(path / "src" / "a.ts", "import { b } from './b';\nexport const a = b;\n")
    write_file(path / "src" / "b.ts", "import { c } from './c';\nexport const b = c;\n")
    write_file(path / "src" / "c.ts", "import { a } from './a';\nexport const c = a;\n")
    write_file(path / "src" / "d.ts", "export const d = 1;\n")


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
    create_cycle_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service() -> CircularDependencyService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return CircularDependencyService(
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser)
    )


def test_circular_dependency_service_reports_cycles_and_edges(tmp_path: Path) -> None:
    create_cycle_fixture(tmp_path)

    report = create_service().detect(tmp_path)

    assert report.stats.cycle_count == 1
    assert report.stats.affected_file_count == 3
    assert report.stats.max_cycle_length == 3
    assert report.cycles[0].files == ("src/a.ts", "src/b.ts", "src/c.ts")
    assert {(edge.source, edge.target) for edge in report.cycles[0].edges} == {
        ("src/a.ts", "src/b.ts"),
        ("src/b.ts", "src/c.ts"),
        ("src/c.ts", "src/a.ts"),
    }


def test_circular_dependency_api_for_repository_path(tmp_path: Path) -> None:
    create_cycle_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/circular-dependencies",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["cycle_count"] == 1
    assert body["cycles"][0]["length"] == 3


def test_circular_dependency_api_for_imported_repository(tmp_path: Path) -> None:
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

    cycle_response = client.get(f"/api/repositories/imports/{import_id}/circular-dependencies")

    assert cycle_response.status_code == 200
    assert cycle_response.json()["stats"]["affected_file_count"] == 3
