import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_docs import ArchitectureDocsService
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
        ["git", "config", "user.name", "CodeInsight"],
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


def create_service(database_path: Path) -> ArchitectureDocsService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    summary_service = RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        call_graph=CallGraphService(scanner=scanner, parser=parser),
        vector_repository=VectorStoreRepository(str(database_path)),
    )
    return ArchitectureDocsService(
        architecture_service=ArchitectureExplanationService(summary_service=summary_service)
    )


def test_architecture_docs_service_generates_markdown(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)

    document = create_service(tmp_path / "vectors.sqlite3").generate(tmp_path, focus="auth")

    assert document.title == f"{tmp_path.name} Architecture: auth"
    assert document.focus == "auth"
    assert document.markdown.startswith(f"# {tmp_path.name} Architecture: auth")
    assert "## Core Components" in document.markdown
    assert "`app/auth.py`" in document.markdown
    assert "## Dependency Flow" in document.markdown
    assert "## Call Flow" in document.markdown
    assert document.stats.section_count == 7
    assert document.stats.component_count >= 1
    assert 0.0 <= document.stats.confidence <= 1.0


def test_architecture_docs_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/architecture-docs",
        json={"repository_path": str(tmp_path), "focus": "auth"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["focus"] == "auth"
    assert body["stats"]["section_count"] == 7
    assert "Architecture Observations" in body["markdown"]
    assert body["evidence_paths"]


def test_architecture_docs_api_for_imported_repository(tmp_path: Path) -> None:
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
    docs_response = client.post(
        f"/api/repositories/imports/{import_id}/architecture-docs",
        json={"focus": "auth"},
    )

    assert import_response.status_code == 201
    assert docs_response.status_code == 200
    assert "Generated By CodeInsight" in docs_response.json()["markdown"]
