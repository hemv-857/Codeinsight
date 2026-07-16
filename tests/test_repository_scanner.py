import subprocess
from pathlib import Path

import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService
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


def test_scanner_collects_repository_metadata(tmp_path: Path) -> None:
    write_file(tmp_path / "app" / "main.py", "print('hello')\n")
    write_file(tmp_path / "web" / "index.tsx", "export default function Page() {}\n")
    write_file(tmp_path / "README.md", "# Demo\n")
    service = RepositoryScannerService()

    result = service.scan(tmp_path)

    assert [file.path for file in result.files] == [
        "README.md",
        "app/main.py",
        "web/index.tsx",
    ]
    assert result.directories == ["app", "web"]
    assert result.extensions == [".md", ".py", ".tsx"]
    assert result.languages == ["Python", "TypeScript"]
    assert result.files[1].language == "Python"


def test_scanner_ignores_generated_and_dependency_directories(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "main.py", "print('kept')\n")
    for ignored in [".git", "node_modules", "venv", "target", "dist"]:
        write_file(tmp_path / ignored / "ignored.py", "print('ignored')\n")
    service = RepositoryScannerService()

    result = service.scan(tmp_path)

    assert [file.path for file in result.files] == ["src/main.py"]
    assert result.directories == ["src"]


def test_scanner_rejects_missing_repository(tmp_path: Path) -> None:
    service = RepositoryScannerService()

    with pytest.raises(RepositoryScanError, match="does not exist"):
        service.scan(tmp_path / "missing")


def test_scan_repository_api(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "main.go", "package main\n")
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post("/api/repositories/scan", json={"repository_path": str(tmp_path)})

    assert response.status_code == 200
    body = response.json()
    assert body["languages"] == ["Go"]
    assert body["files"][0]["path"] == "src/main.go"


def test_scan_imported_repository_api(tmp_path: Path) -> None:
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

    scan_response = client.get(f"/api/repositories/imports/{import_id}/scan")

    assert scan_response.status_code == 200
    assert scan_response.json()["languages"] == ["Python"]
