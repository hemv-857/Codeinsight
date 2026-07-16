import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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
    write_file(path / "app" / "main.py", "from app.service import Service\n")
    write_file(path / "app" / "service.py", "class Service:\n    pass\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_dependency_graph_fixture(path: Path) -> None:
    write_file(path / "app" / "main.py", "import os\nfrom app.service import Service\n")
    write_file(path / "app" / "service.py", "class Service:\n    pass\n")
    write_file(path / "src" / "a.ts", "import { b } from './b';\nexport const a = b;\n")
    write_file(path / "src" / "b.ts", "import { a } from './a';\nexport const b = a;\n")


def test_dependency_graph_resolves_internal_external_and_circular_edges(tmp_path: Path) -> None:
    create_dependency_graph_fixture(tmp_path)
    service = DependencyGraphService(
        scanner=RepositoryScannerService(),
        parser=TreeSitterParserService(),
    )

    graph = service.build(tmp_path)

    assert [node.path for node in graph.nodes] == [
        "app/main.py",
        "app/service.py",
        "src/a.ts",
        "src/b.ts",
    ]
    internal_edges = {(edge.source, edge.target) for edge in graph.edges if edge.target}
    assert internal_edges == {
        ("app/main.py", "app/service.py"),
        ("src/a.ts", "src/b.ts"),
        ("src/b.ts", "src/a.ts"),
    }
    assert graph.external_dependencies == ("os",)
    assert graph.unresolved_imports == ("os",)
    assert graph.circular_dependencies == (("src/a.ts", "src/b.ts"),)
    assert graph.stats.file_count == 4
    assert graph.stats.internal_dependency_count == 3
    assert graph.stats.external_dependency_count == 1


def test_dependency_graph_api_for_repository_path(tmp_path: Path) -> None:
    create_dependency_graph_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/dependency-graph",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["file_count"] == 4
    assert body["stats"]["circular_dependency_count"] == 1
    assert "os" in body["external_dependencies"]


def test_dependency_graph_api_for_imported_repository(tmp_path: Path) -> None:
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

    graph_response = client.get(f"/api/repositories/imports/{import_id}/dependency-graph")

    assert graph_response.status_code == 200
    body = graph_response.json()
    assert body["stats"]["internal_dependency_count"] == 1
    assert body["edges"][0]["target"] == "app/service.py"
