import subprocess
from hashlib import sha256
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient


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
    write_file(path / "src" / "main.py", "print('hello')\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                metadata_database_path=tmp_path / "metadata.sqlite3",
                repository_storage_path=tmp_path / "imports",
            )
        )
    )


def test_metadata_api_persists_and_reads_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    source_file = repository_root / "src" / "main.py"
    write_file(source_file, "print('hello')\n")
    client = create_client(tmp_path)

    response = client.post(
        "/api/repositories/metadata",
        json={"repository_path": str(repository_root), "name": "demo"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "demo"
    assert body["languages"] == ["Python"]
    assert body["files"][0]["sha256"] == sha256(source_file.read_bytes()).hexdigest()

    read_response = client.get(f"/api/repositories/metadata/{body['repository_id']}")

    assert read_response.status_code == 200
    assert read_response.json() == body


def test_metadata_api_persists_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    client = create_client(tmp_path)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    metadata_response = client.get(f"/api/repositories/imports/{import_id}/metadata")

    assert metadata_response.status_code == 200
    assert metadata_response.json()["files"][0]["path"] == "src/main.py"


def test_metadata_api_returns_404_for_missing_repository(tmp_path: Path) -> None:
    client = create_client(tmp_path)

    response = client.get("/api/repositories/metadata/999")

    assert response.status_code == 404
