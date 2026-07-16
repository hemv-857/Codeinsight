import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.security_review import SecurityReviewService
from fastapi.testclient import TestClient


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "security.py",
        "\n".join(
            [
                "import hashlib",
                "import pickle",
                "",
                "API_KEY = 'super-secret-demo-key'",
                "",
                "def run_user_code(payload):",
                "    return eval(payload)",
                "",
                "def load_payload(raw):",
                "    return pickle.loads(raw)",
                "",
                "def weak_hash(value):",
                "    return hashlib.md5(value).hexdigest()",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "db.py",
        "\n".join(
            [
                "def find_user(cursor, user_id):",
                '    return cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
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


def test_security_review_service_flags_changed_file_risks(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)

    review = SecurityReviewService(scanner=RepositoryScannerService()).review(
        repository_path=tmp_path,
        changed_files=("app/security.py", "app/db.py"),
        focus="credential and injection risk",
    )

    categories = {finding.category for finding in review.findings}

    assert review.focus == "credential and injection risk"
    assert review.stats.changed_file_count == 2
    assert review.stats.reviewed_file_count == 2
    assert review.stats.risk_score > 0
    assert "hardcoded_secret" in categories
    assert "dangerous_code_execution" in categories
    assert "unsafe_deserialization" in categories
    assert "weak_crypto" in categories
    assert "dynamic_sql" in categories
    assert review.recommendations


def test_security_review_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/security-review",
        json={
            "repository_path": str(tmp_path),
            "changed_files": ["app/security.py", "app/db.py"],
            "focus": "credential and injection risk",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_path"] == str(tmp_path.resolve())
    assert body["stats"]["finding_count"] >= 4
    assert body["stats"]["high_count"] >= 3
    assert body["recommendations"]


def test_security_review_api_for_imported_repository(tmp_path: Path) -> None:
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
        f"/api/repositories/imports/{import_id}/security-review",
        json={"changed_files": ["app/security.py"], "focus": "credential risk"},
    )

    assert import_response.status_code == 201
    assert review_response.status_code == 200
    assert review_response.json()["stats"]["reviewed_file_count"] == 1
