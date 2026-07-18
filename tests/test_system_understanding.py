import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_docs import ArchitectureDocsService
from backend.app.services.architecture_explanation import ArchitectureExplanationService
from backend.app.services.mermaid_diagrams import MermaidDiagramService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.repository_summary import RepositorySummaryService
from backend.app.services.system_understanding import SystemUnderstandingService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import SafeSourceParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "models.py",
        "\n".join(
            [
                "class User:",
                "    def __init__(self, email):",
                "        self.email = email",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "user_service.py",
        "\n".join(
            [
                "from app.models import User",
                "",
                "class UserService:",
                "    def create_user(self, email):",
                "        return User(email)",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "main.py",
        "\n".join(
            [
                "from app.user_service import UserService",
                "",
                "def handle_request(email):",
                "    return UserService().create_user(email)",
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


def create_service(database_path: Path) -> SystemUnderstandingService:
    scanner = RepositoryScannerService()
    parser = SafeSourceParserService()
    dependency_graph = DependencyGraphService(scanner=scanner, parser=parser)
    call_graph = CallGraphService(scanner=scanner, parser=parser)
    summary_service = RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=dependency_graph,
        call_graph=call_graph,
        vector_repository=VectorStoreRepository(str(database_path)),
    )
    architecture_service = ArchitectureExplanationService(summary_service=summary_service)
    architecture_docs = ArchitectureDocsService(architecture_service=architecture_service)
    mermaid_service = MermaidDiagramService(
        architecture_docs=architecture_docs,
        dependency_graph=dependency_graph,
        call_graph=call_graph,
    )
    return SystemUnderstandingService(
        summary_service=summary_service,
        architecture_service=architecture_service,
        mermaid_service=mermaid_service,
    )


def test_system_understanding_service_generates_grounded_report(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    db_path = tmp_path.parent / f"{tmp_path.name}_vectors.sqlite3"

    report = create_service(db_path).generate(tmp_path)

    assert report.title == f"{tmp_path.name} System Understanding"
    assert "internal dependencies" in report.application_overview
    assert report.main_components
    assert report.important_files
    assert report.related_symbols
    assert any(symbol.name == "UserService" for symbol in report.important_services)
    assert "flowchart" in report.architecture_diagram
    assert "flowchart" in report.dependency_visualization
    assert "Suggested Learning Path" in report.markdown
    assert report.stats.file_count == 3
    assert report.stats.diagram_count == 3


def test_system_understanding_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/system-understanding",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["main_components"]
    assert body["important_files"]
    assert body["stats"]["diagram_count"] == 3


def test_system_understanding_api_for_imported_repository(tmp_path: Path) -> None:
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
    report_response = client.get(f"/api/repositories/imports/{import_id}/system-understanding")

    assert import_response.status_code == 201
    assert report_response.status_code == 200
    assert "System Understanding" in report_response.json()["title"]
