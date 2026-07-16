import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.architecture_violations import ArchitectureViolationService
from backend.app.services.pull_request_review import PullRequestReviewService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.technical_debt import TechnicalDebtService
from fastapi.testclient import TestClient
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
                "def authenticate_user(token):",
                "    if token:",
                "        return token == 'valid'",
                "    return False",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "main.py",
        "\n".join(
            [
                "from app.auth import authenticate_user",
                "",
                "def request_handler(token):",
                "    return authenticate_user(token)",
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


def create_service() -> PullRequestReviewService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    dependency_graph = DependencyGraphService(scanner=scanner, parser=parser)
    return PullRequestReviewService(
        scanner=scanner,
        dependency_graph=dependency_graph,
        technical_debt=TechnicalDebtService(
            scanner=scanner,
            parser=parser,
            dependency_graph=dependency_graph,
        ),
        architecture_violations=ArchitectureViolationService(dependency_graph=dependency_graph),
    )


def test_pull_request_review_service_reviews_changed_files(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)

    review = create_service().review(
        repository_path=tmp_path,
        changed_files=("app/main.py",),
        title="Update auth route",
        diff_text="+    return authenticate_user(token)\n",
    )

    assert review.title == "Update auth route"
    assert review.changed_files == ("app/main.py",)
    assert review.stats.changed_file_count == 1
    assert review.stats.impacted_file_count >= 2
    assert review.stats.finding_count >= 1
    assert any(finding.category == "testing" for finding in review.findings)
    assert "app/auth.py" in {file.path for file in review.impacted_files}


def test_pull_request_review_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/pr-review",
        json={
            "repository_path": str(tmp_path),
            "changed_files": ["app/main.py"],
            "title": "Update auth route",
            "diff_text": "+changed\n",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["changed_files"] == ["app/main.py"]
    assert body["stats"]["risk_score"] > 0
    assert body["recommendations"]


def test_pull_request_review_api_for_imported_repository(tmp_path: Path) -> None:
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
    import_id = import_response.json()["import_id"]
    review_response = client.post(
        f"/api/repositories/imports/{import_id}/pr-review",
        json={"changed_files": ["app/main.py"], "title": "Update auth route"},
    )

    assert import_response.status_code == 201
    assert review_response.status_code == 200
    assert review_response.json()["stats"]["changed_file_count"] == 1
