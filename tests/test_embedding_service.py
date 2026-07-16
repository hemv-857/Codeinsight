import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_embedding_service
from backend.app.main import create_app
from backend.app.services.embedding import EmbeddingClient, EmbeddingError, EmbeddingService
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from parser.tree_sitter_parser import TreeSitterParserService


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, list[str]]] = []

    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        self.requests.append((model, inputs))
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


def create_service(client: EmbeddingClient | None = None, batch_size: int = 64) -> EmbeddingService:
    return EmbeddingService(
        chunker=RepositoryChunkerService(
            scanner=RepositoryScannerService(),
            parser=TreeSitterParserService(),
        ),
        client=client,
        model="text-embedding-3-small",
        batch_size=batch_size,
    )


def test_embedding_service_generates_embeddings_for_repository_chunks(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    client = FakeEmbeddingClient()
    service = create_service(client=client, batch_size=2)

    result = service.embed_repository(tmp_path)

    assert result.model == "text-embedding-3-small"
    assert result.stats.chunk_count == 4
    assert result.stats.embedding_count == 4
    assert result.stats.dimensions == 2
    assert len(client.requests) == 2
    assert all(embedding.embedding for embedding in result.embeddings)
    assert {
        embedding.symbol_name for embedding in result.embeddings if embedding.kind == "symbol"
    } == {
        "UserService",
        "load",
        "make_user",
    }


def test_embedding_service_requires_api_key_client(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(client=None)

    try:
        service.embed_repository(tmp_path)
    except EmbeddingError as error:
        assert "OpenAI API key" in str(error)
    else:
        raise AssertionError("Expected embedding generation to require a client.")


def test_embedding_service_detects_response_count_mismatch(tmp_path: Path) -> None:
    class ShortEmbeddingClient:
        def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
            return [[1.0]]

    create_repository_fixture(tmp_path)
    service = create_service(client=ShortEmbeddingClient())

    try:
        service.embed_repository(tmp_path)
    except EmbeddingError as error:
        assert "response count" in str(error)
    else:
        raise AssertionError("Expected embedding generation to reject mismatched responses.")


def test_embedding_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(Settings(environment="test"))
    app.dependency_overrides[get_embedding_service] = lambda: create_service(
        client=FakeEmbeddingClient()
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/embeddings",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "text-embedding-3-small"
    assert body["stats"]["embedding_count"] == 4
    assert body["stats"]["dimensions"] == 2
    assert len(body["embeddings"][0]["embedding"]) == 2


def test_embedding_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    app = create_app(Settings(environment="test", repository_storage_path=tmp_path / "imports"))
    app.dependency_overrides[get_embedding_service] = lambda: create_service(
        client=FakeEmbeddingClient()
    )
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    embedding_response = client.get(f"/api/repositories/imports/{import_id}/embeddings")

    assert embedding_response.status_code == 200
    assert embedding_response.json()["stats"]["embedding_count"] == 4


def test_embedding_api_reports_missing_api_key(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(Settings(environment="test", openai_api_key=None))
    client = TestClient(app)

    response = client.post(
        "/api/repositories/embeddings",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 400
    assert "OpenAI API key" in response.json()["detail"]
