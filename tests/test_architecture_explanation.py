import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_explanation import ArchitectureExplanationService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.repository_summary import RepositorySummaryService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "auth.py",
        "\n".join(
            [
                "class AuthService:",
                "    def authenticate_user(self, token):",
                "        return token == 'valid'",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "main.py",
        "\n".join(
            [
                "from app.auth import AuthService",
                "",
                "def request_handler(token):",
                "    return AuthService().authenticate_user(token)",
                "",
            ]
        ),
    )


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
    create_repository_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_explanation_service(database_path: Path) -> ArchitectureExplanationService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    summary_service = RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        call_graph=CallGraphService(scanner=scanner, parser=parser),
        vector_repository=VectorStoreRepository(str(database_path)),
    )
    return ArchitectureExplanationService(summary_service=summary_service)


def test_architecture_explanation_describes_components_and_flows(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_explanation_service(tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3")

    explanation = service.explain(tmp_path)

    assert explanation.repository_path == str(tmp_path.resolve())
    assert explanation.focus is None
    assert explanation.components
    assert any(component.path == "app/auth.py" for component in explanation.components)
    assert any("internal file dependencies" in item for item in explanation.dependency_flow)
    assert any("call sites" in item for item in explanation.call_flow)
    assert "app/auth.py" in explanation.evidence_paths
    assert explanation.confidence > 0


def test_architecture_explanation_can_focus_on_subsystem(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_explanation_service(tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3")

    explanation = service.explain(tmp_path, focus="auth")

    assert explanation.focus == "auth"
    assert "focus 'auth'" in explanation.overview
    assert explanation.components[0].path == "app/auth.py"
    assert explanation.confidence < 0.82


def test_architecture_explanation_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/architecture-explanation",
        json={"repository_path": str(tmp_path), "focus": "auth"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["focus"] == "auth"
    assert body["components"]
    assert body["evidence_paths"]
    assert body["confidence"] > 0


def test_architecture_explanation_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    app = create_app(
        Settings(
            environment="test",
            repository_storage_path=tmp_path / "imports",
            vector_database_path=tmp_path / "vectors.sqlite3",
        )
    )
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )
    import_id = import_response.json()["import_id"]
    explanation_response = client.post(
        f"/api/repositories/imports/{import_id}/architecture-explanation",
        json={"focus": "auth"},
    )

    assert import_response.status_code == 201
    assert explanation_response.status_code == 200
    assert explanation_response.json()["components"]


def test_architecture_explanation_api_rejects_missing_repository(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test"))
    client = TestClient(app)

    response = client.post(
        "/api/repositories/architecture-explanation",
        json={"repository_path": str(tmp_path / "missing")},
    )

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]
