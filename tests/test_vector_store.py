import subprocess
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_embedding_service
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.embedding import (
    EmbeddingClient,
    EmbeddingService,
    OllamaEmbeddingClient,
)
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.vector_store import VectorStoreService
from fastapi.testclient import TestClient
from parser.tree_sitter_parser import TreeSitterParserService


class FakeEmbeddingClient:
    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        return [[float(index), float(len(text))] for index, text in enumerate(inputs, start=1)]


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
                "        return user_id",
                "",
                "def make_user(name):",
                "    return UserService()",
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


def create_embedding_service(client: EmbeddingClient) -> EmbeddingService:
    return EmbeddingService(
        chunker=RepositoryChunkerService(
            scanner=RepositoryScannerService(),
            parser=TreeSitterParserService(),
        ),
        client=client,
        model="demo-embedding",
        batch_size=2,
    )


def test_vector_store_repository_replaces_vectors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    embeddings = create_embedding_service(FakeEmbeddingClient()).embed_repository(tmp_path)
    repository = VectorStoreRepository(str(tmp_path / "vectors.sqlite3"))

    stored_count = repository.replace(embeddings)
    stored = repository.list_repository(embeddings.repository_path)

    assert stored_count == 4
    assert len(stored) == 4
    assert stored[0].embedding
    assert {item.symbol_name for item in stored if item.kind == "symbol"} == {
        "UserService",
        "load",
        "make_user",
    }


def test_vector_store_service_generates_and_persists_vectors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    repository = VectorStoreRepository(str(tmp_path / "vectors.sqlite3"))
    service = VectorStoreService(
        embedding_service=create_embedding_service(FakeEmbeddingClient()),
        repository=repository,
    )

    result = service.index_repository(tmp_path)

    assert result.backend == "sqlite"
    assert result.model == "demo-embedding"
    assert result.stored_embedding_count == 4
    assert result.dimensions == 2
    assert len(repository.list_repository(result.repository_path)) == 4


def test_vector_store_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    app.dependency_overrides[get_embedding_service] = lambda: create_embedding_service(
        FakeEmbeddingClient()
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/vector-store",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stored_embedding_count"] == 4
    assert body["dimensions"] == 2
    assert "embeddings" not in body


def test_vector_store_api_for_imported_repository(tmp_path: Path) -> None:
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
    app.dependency_overrides[get_embedding_service] = lambda: create_embedding_service(
        FakeEmbeddingClient()
    )
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    vector_response = client.get(f"/api/repositories/imports/{import_id}/vector-store")

    assert vector_response.status_code == 200
    assert vector_response.json()["stored_embedding_count"] == 4


def test_ollama_embedding_client_uses_local_embedding_endpoint(monkeypatch: Any) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"embeddings": [[1.0, 5.0]]}'

    def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
        assert request.full_url == "http://localhost:11434/api/embed"
        assert timeout == 120
        return FakeResponse()

    monkeypatch.setattr("backend.app.services.embedding.urlopen", fake_urlopen)
    client = OllamaEmbeddingClient("http://localhost:11434")

    vectors = client.create_embeddings(model="nomic-embed-text", inputs=["hello"])

    assert vectors == [[1.0, 5.0]]
