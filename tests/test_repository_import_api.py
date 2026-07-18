import subprocess
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient


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
    (path / "README.md").write_text("# Demo\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_client(storage_root: Path) -> TestClient:
    settings = Settings(
        environment="test",
        repository_storage_path=storage_root,
        repository_clone_timeout_seconds=30,
    )
    return TestClient(create_app(settings))


def test_import_local_repository_api(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    client = create_client(tmp_path / "imports")

    response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["source_type"] == "local"
    assert Path(body["repository_path"]).joinpath("README.md").is_file()

    progress_response = client.get(f"/api/repositories/imports/{body['import_id']}")

    assert progress_response.status_code == 200
    assert progress_response.json()["events"][-1]["stage"] == "completed"


def test_import_zip_repository_api(tmp_path: Path) -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("project/README.md", "# Demo\n")

    client = create_client(tmp_path / "imports")
    response = client.post(
        "/api/repositories/import/zip",
        files={"file": ("project.zip", buffer.getvalue(), "application/zip")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["source_type"] == "zip"


def test_missing_import_progress_returns_404(tmp_path: Path) -> None:
    client = create_client(tmp_path / "imports")

    response = client.get("/api/repositories/imports/missing")

    assert response.status_code == 404
