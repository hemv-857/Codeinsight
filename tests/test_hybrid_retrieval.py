import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_embedding_service
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.embedding import EmbeddingClient, EmbeddingService
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.retrieval import HybridRetrievalService, RetrievalError
from backend.app.services.vector_store import VectorStoreService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


class TopicEmbeddingClient:
    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in inputs]

    def _vector(self, text: str) -> list[float]:
        normalized = text.lower()
        auth_score = float(
            normalized.count("auth") + normalized.count("token") + normalized.count("user")
        )
        server_score = float(
            normalized.count("main") + normalized.count("handler") + normalized.count("server")
        )
        return [auth_score or 0.1, server_score or 0.1]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "auth.py",
        "\n".join(
            [
                "def authenticate_user(token):",
                "    return token == 'valid'",
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


def create_embedding_service(client: EmbeddingClient) -> EmbeddingService:
    return EmbeddingService(
        chunker=RepositoryChunkerService(
            scanner=RepositoryScannerService(),
            parser=TreeSitterParserService(),
        ),
        client=client,
        model="topic-embedding",
        batch_size=2,
    )


def create_retrieval_service(
    database_path: Path,
    client: EmbeddingClient | None = None,
) -> HybridRetrievalService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return HybridRetrievalService(
        repository=VectorStoreRepository(str(database_path)),
        embedding_client=client if client is not None else TopicEmbeddingClient(),
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        model="topic-embedding",
    )


def index_repository(repository_path: Path, database_path: Path) -> VectorStoreRepository:
    repository = VectorStoreRepository(str(database_path))
    service = VectorStoreService(
        embedding_service=create_embedding_service(TopicEmbeddingClient()),
        repository=repository,
    )
    service.index_repository(repository_path)
    return repository


def test_vector_store_persists_chunk_content_for_keyword_retrieval(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    repository = index_repository(tmp_path, tmp_path / "vectors.sqlite3")

    stored = repository.list_repository(str(tmp_path.resolve()))

    assert any("authenticate_user" in item.content for item in stored)


def test_hybrid_retrieval_ranks_vector_keyword_and_graph_signals(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    index_repository(tmp_path, tmp_path / "vectors.sqlite3")
    service = create_retrieval_service(tmp_path / "vectors.sqlite3")

    result = service.retrieve(tmp_path, "auth token", limit=3)

    assert result.stats.searched_embedding_count == 4
    assert result.results[0].path == "app/auth.py"
    assert result.results[0].keyword_score > 0
    assert result.results[0].vector_score > 0
    assert any("app/main.py" in item.related_paths for item in result.results)


def test_hybrid_retrieval_requires_stored_vectors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_retrieval_service(tmp_path / "vectors.sqlite3")

    try:
        service.retrieve(tmp_path, "auth token")
    except RetrievalError as error:
        assert "No vectors" in str(error)
    else:
        raise AssertionError("Expected RetrievalError.")


def test_hybrid_retrieval_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(environment="test", vector_database_path=tmp_path / "vectors.sqlite3")
    )
    app.dependency_overrides[get_embedding_service] = lambda: create_embedding_service(
        TopicEmbeddingClient()
    )
    client = TestClient(app)

    index_response = client.post(
        "/api/repositories/vector-store",
        json={"repository_path": str(tmp_path)},
    )
    retrieve_response = client.post(
        "/api/repositories/retrieve",
        json={
            "repository_path": str(tmp_path),
            "query": "auth token",
            "limit": 2,
        },
    )

    assert index_response.status_code == 200
    assert retrieve_response.status_code == 200
    body = retrieve_response.json()
    assert body["stats"]["result_count"] == 2
    assert body["results"][0]["path"] == "app/auth.py"
    assert body["results"][0]["content"]


def test_hybrid_retrieval_api_for_imported_repository(tmp_path: Path) -> None:
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
        TopicEmbeddingClient()
    )
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )
    import_id = import_response.json()["import_id"]
    index_response = client.get(f"/api/repositories/imports/{import_id}/vector-store")
    retrieve_response = client.post(
        f"/api/repositories/imports/{import_id}/retrieve",
        json={"query": "auth token", "limit": 1},
    )

    assert import_response.status_code == 201
    assert index_response.status_code == 200
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["results"][0]["path"] == "app/auth.py"
