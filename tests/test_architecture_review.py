import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_review import ArchitectureReviewService
from backend.app.services.architecture_violations import ArchitectureViolationService
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
    write_file(path / "api" / "__init__.py", "")
    write_file(path / "database" / "__init__.py", "")
    write_file(
        path / "database" / "models.py",
        "\n".join(
            [
                "class User:",
                "    def __init__(self, name):",
                "        self.name = name",
                "",
            ]
        ),
    )
    write_file(
        path / "api" / "routes.py",
        "\n".join(
            [
                "from database.models import User",
                "",
                "def list_users():",
                "    return [User('Ada')]",
                "",
            ]
        ),
    )
    write_file(
        path / "services" / "users.py",
        "\n".join(
            [
                "from api.routes import list_users",
                "",
                "def user_names():",
                "    return [user.name for user in list_users()]",
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


def create_service(vector_database_path: Path) -> ArchitectureReviewService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    dependency_graph = DependencyGraphService(scanner=scanner, parser=parser)
    return ArchitectureReviewService(
        scanner=scanner,
        dependency_graph=dependency_graph,
        summary=RepositorySummaryService(
            scanner=scanner,
            parser=parser,
            dependency_graph=dependency_graph,
            call_graph=CallGraphService(scanner=scanner, parser=parser),
            vector_repository=VectorStoreRepository(str(vector_database_path)),
        ),
        architecture_violations=ArchitectureViolationService(dependency_graph=dependency_graph),
    )


def test_architecture_review_scopes_boundary_findings(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)

    review = create_service(tmp_path / "vectors.db").review(
        repository_path=tmp_path,
        changed_files=("api/routes.py",),
        focus="service boundary",
    )

    assert review.focus == "service boundary"
    assert review.changed_files == ("api/routes.py",)
    assert review.stats.changed_file_count == 1
    assert review.stats.violation_count >= 1
    assert review.stats.risk_score > 0
    assert "database/models.py" in {file.path for file in review.impacted_files}
    assert any(
        finding.category == "boundary:api-skips-service-layer" for finding in review.findings
    )


def test_architecture_review_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    client = TestClient(
        create_app(Settings(environment="test", vector_database_path=tmp_path / "vectors.db"))
    )

    response = client.post(
        "/api/repositories/architecture-review",
        json={
            "repository_path": str(tmp_path),
            "changed_files": ["api/routes.py"],
            "focus": "service boundary",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["changed_files"] == ["api/routes.py"]
    assert body["stats"]["violation_count"] >= 1
    assert body["recommendations"]


def test_architecture_review_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    client = TestClient(
        create_app(
            Settings(
                environment="test",
                repository_storage_path=tmp_path / "imports",
                vector_database_path=tmp_path / "vectors.db",
            )
        )
    )

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )
    import_id = import_response.json()["import_id"]
    review_response = client.post(
        f"/api/repositories/imports/{import_id}/architecture-review",
        json={"changed_files": ["api/routes.py"], "focus": "service boundary"},
    )

    assert import_response.status_code == 201
    assert review_response.status_code == 200
    assert review_response.json()["stats"]["changed_file_count"] == 1
