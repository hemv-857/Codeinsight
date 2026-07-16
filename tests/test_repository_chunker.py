import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_repository_chunker_service
from backend.app.main import create_app
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "service.py",
        "\n".join(
            [
                "class UserService:",
                "    def load(self, user_id):",
                "        value = user_id",
                "        return value",
                "",
                "def make_user(name):",
                "    return UserService()",
                "",
            ]
        ),
    )
    write_file(path / "README.md", "# ignored by source chunker\n")


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


def create_service(max_chunk_chars: int = 12_000) -> RepositoryChunkerService:
    return RepositoryChunkerService(
        scanner=RepositoryScannerService(),
        parser=TreeSitterParserService(),
        max_chunk_chars=max_chunk_chars,
    )


def test_repository_chunker_builds_file_and_symbol_chunks(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service()

    result = service.chunk_repository(tmp_path)

    chunks_by_kind = {
        kind: [chunk for chunk in result.chunks if chunk.kind == kind]
        for kind in {"file", "symbol"}
    }
    symbol_names = {chunk.symbol_name for chunk in chunks_by_kind["symbol"]}
    assert result.stats.source_file_count == 1
    assert result.stats.file_chunk_count == 1
    assert result.stats.symbol_chunk_count == 3
    assert result.stats.skipped_file_count == 0
    assert chunks_by_kind["file"][0].path == "app/service.py"
    assert "class UserService" in chunks_by_kind["file"][0].content
    assert {"UserService", "load", "make_user"} == symbol_names
    assert all(chunk.id.startswith(f"{chunk.kind}:{chunk.path}:") for chunk in result.chunks)


def test_repository_chunker_splits_file_chunks_by_size(tmp_path: Path) -> None:
    write_file(tmp_path / "main.py", "a = 1\nb = 2\nc = 3\n")
    service = create_service(max_chunk_chars=8)

    result = service.chunk_repository(tmp_path)

    file_chunks = [chunk for chunk in result.chunks if chunk.kind == "file"]
    assert [chunk.content for chunk in file_chunks] == ["a = 1\n", "b = 2\n", "c = 3\n"]
    assert [(chunk.start_line, chunk.end_line) for chunk in file_chunks] == [(1, 1), (2, 2), (3, 3)]


def test_repository_chunk_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(Settings(environment="test", repository_chunk_max_chars=12_000))
    client = TestClient(app)

    response = client.post(
        "/api/repositories/chunks",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["source_file_count"] == 1
    assert body["stats"]["symbol_chunk_count"] == 3
    assert {chunk["symbol_name"] for chunk in body["chunks"] if chunk["kind"] == "symbol"} == {
        "UserService",
        "load",
        "make_user",
    }


def test_repository_chunk_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    app = create_app(Settings(environment="test", repository_storage_path=tmp_path / "imports"))
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    chunk_response = client.get(f"/api/repositories/imports/{import_id}/chunks")

    assert chunk_response.status_code == 200
    assert chunk_response.json()["stats"]["file_chunk_count"] == 1


def test_repository_chunk_api_reports_service_errors(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test"))
    app.dependency_overrides[get_repository_chunker_service] = lambda: create_service()
    client = TestClient(app)

    response = client.post(
        "/api/repositories/chunks",
        json={"repository_path": str(tmp_path / "missing")},
    )

    assert response.status_code == 400
