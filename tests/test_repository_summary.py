import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.embedding import EmbeddingClient, EmbeddingService
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.repository_summary import RepositorySummaryService
from backend.app.services.vector_store import VectorStoreService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


class FakeEmbeddingClient:
    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in inputs]


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
    write_file(path / "README.md", "# Demo Repository\n")


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


def create_embedding_service(client: EmbeddingClient) -> EmbeddingService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return EmbeddingService(
        chunker=RepositoryChunkerService(scanner=scanner, parser=parser),
        client=client,
        model="summary-embedding",
        batch_size=2,
    )


def create_summary_service(database_path: Path) -> RepositorySummaryService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        call_graph=CallGraphService(scanner=scanner, parser=parser),
        vector_repository=VectorStoreRepository(str(database_path)),
    )


def index_repository(repository_path: Path, database_path: Path) -> None:
    VectorStoreService(
        embedding_service=create_embedding_service(FakeEmbeddingClient()),
        repository=VectorStoreRepository(str(database_path)),
    ).index_repository(repository_path)


def test_repository_summary_uses_scanner_parser_graphs_and_vectors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    database_path = tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3"
    index_repository(tmp_path, database_path)
    service = create_summary_service(database_path)

    summary = service.summarize(tmp_path)

    assert summary.stats.file_count == 3
    assert summary.stats.parsed_file_count == 2
    assert summary.stats.symbol_count >= 3
    assert summary.stats.dependency_count == 1
    assert summary.stats.indexed_embedding_count > 0
    assert summary.embedding_indexed is True
    assert summary.languages[0].language == "Python"
    assert any(file.path == "app/auth.py" for file in summary.key_files)
    assert any(symbol.name == "AuthService" for symbol in summary.key_symbols)
    assert "primary language is Python" in summary.overview


def test_repository_summary_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/summary",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["parsed_file_count"] == 2
    assert body["embedding_indexed"] is False
    assert body["key_symbols"]
    assert "app/auth.py" in body["evidence_paths"]


def test_repository_summary_api_for_imported_repository(tmp_path: Path) -> None:
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
    summary_response = client.get(f"/api/repositories/imports/{import_id}/summary")

    assert import_response.status_code == 201
    assert summary_response.status_code == 200
    assert summary_response.json()["stats"]["parsed_file_count"] == 2


def test_repository_summary_api_rejects_missing_repository(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test"))
    client = TestClient(app)

    response = client.post(
        "/api/repositories/summary",
        json={"repository_path": str(tmp_path / "missing")},
    )

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]
