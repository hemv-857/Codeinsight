import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_docs import ArchitectureDocsService
from backend.app.services.architecture_explanation import ArchitectureExplanationService
from backend.app.services.developer_onboarding import DeveloperOnboardingService
from backend.app.services.mermaid_diagrams import MermaidDiagramService
from backend.app.services.readme_generator import ReadmeGeneratorService
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
    write_file(path / "requirements.txt", "fastapi\n")
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
                "    service = AuthService()",
                "    return service.authenticate_user(token)",
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


def create_service(database_path: Path) -> DeveloperOnboardingService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    dependency_graph = DependencyGraphService(scanner=scanner, parser=parser)
    call_graph = CallGraphService(scanner=scanner, parser=parser)
    summary_service = RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=dependency_graph,
        call_graph=call_graph,
        vector_repository=VectorStoreRepository(str(database_path)),
    )
    architecture_docs = ArchitectureDocsService(
        architecture_service=ArchitectureExplanationService(summary_service=summary_service)
    )
    return DeveloperOnboardingService(
        readme_generator=ReadmeGeneratorService(summary_service=summary_service),
        architecture_docs=architecture_docs,
        mermaid_diagrams=MermaidDiagramService(
            architecture_docs=architecture_docs,
            dependency_graph=dependency_graph,
            call_graph=call_graph,
        ),
    )


def test_developer_onboarding_service_generates_guide(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)

    guide = create_service(tmp_path / "vectors.sqlite3").generate(tmp_path, focus="auth")

    assert guide.title == f"{tmp_path.name} Developer Onboarding: auth"
    assert guide.focus == "auth"
    assert "## Repository Snapshot" in guide.markdown
    assert "## Local Setup" in guide.markdown
    assert "python -m pip install -r requirements.txt" in guide.markdown
    assert "```mermaid" in guide.markdown
    assert guide.stats.section_count == 8
    assert guide.stats.diagram_count == 3


def test_developer_onboarding_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/developer-onboarding",
        json={"repository_path": str(tmp_path), "focus": "auth"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["focus"] == "auth"
    assert body["stats"]["section_count"] == 8
    assert "Follow-Up Questions" in body["markdown"]
    assert body["evidence_paths"]


def test_developer_onboarding_api_for_imported_repository(tmp_path: Path) -> None:
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
    guide_response = client.post(
        f"/api/repositories/imports/{import_id}/developer-onboarding",
        json={"focus": "auth"},
    )

    assert import_response.status_code == 201
    assert guide_response.status_code == 200
    assert "Developer Onboarding" in guide_response.json()["title"]
