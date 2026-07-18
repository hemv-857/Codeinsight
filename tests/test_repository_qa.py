import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.architecture_explanation import ArchitectureExplanationService
from backend.app.services.embedding import EmbeddingClient, EmbeddingService
from backend.app.services.repository_chunker import RepositoryChunkerService
from backend.app.services.repository_qa import RepositoryQAService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.repository_summary import RepositorySummaryService
from backend.app.services.retrieval import HybridRetrievalService
from backend.app.services.vector_store import VectorStoreService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
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
        handler_score = float(normalized.count("handler") + normalized.count("request"))
        return [auth_score or 0.1, handler_score or 0.1]


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
        model="qa-embedding",
        batch_size=2,
    )


def create_qa_service(
    database_path: Path,
    client: EmbeddingClient | None = None,
) -> RepositoryQAService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    vector_repository = VectorStoreRepository(str(database_path))
    dependency_graph = DependencyGraphService(scanner=scanner, parser=parser)
    summary_service = RepositorySummaryService(
        scanner=scanner,
        parser=parser,
        dependency_graph=dependency_graph,
        call_graph=CallGraphService(scanner=scanner, parser=parser),
        vector_repository=vector_repository,
    )
    return RepositoryQAService(
        summary_service=summary_service,
        architecture_service=ArchitectureExplanationService(summary_service=summary_service),
        retrieval_service=HybridRetrievalService(
            repository=vector_repository,
            embedding_client=client,
            dependency_graph=dependency_graph,
            model="qa-embedding",
        ),
    )


def index_repository(repository_path: Path, database_path: Path) -> None:
    VectorStoreService(
        embedding_service=create_embedding_service(TopicEmbeddingClient()),
        repository=VectorStoreRepository(str(database_path)),
    ).index_repository(repository_path)


def test_repository_qa_answers_from_summary_without_vectors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_qa_service(tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3")

    answer = service.answer(tmp_path, "What is this repository?")

    assert answer.mode == "summary"
    assert "semantic index evidence" in answer.answer
    assert "app/auth.py" in answer.supporting_files
    assert answer.supporting_symbols


def test_repository_qa_answers_architecture_questions(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_qa_service(tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3")

    answer = service.answer(tmp_path, "How does auth flow through the architecture?")

    assert answer.mode == "architecture"
    assert "internal dependencies" in answer.answer
    assert "app/auth.py" in answer.supporting_files


def test_repository_qa_uses_retrieval_when_vectors_are_indexed(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    database_path = tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3"
    index_repository(tmp_path, database_path)
    service = create_qa_service(database_path, TopicEmbeddingClient())

    answer = service.answer(tmp_path, "Where is auth token validation?")

    assert answer.mode == "retrieval"
    assert answer.snippets
    assert answer.snippets[0].path == "app/auth.py"
    assert "app/auth.py" in answer.answer


def test_repository_qa_streams_answer_chunks(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_qa_service(tmp_path.parent / f"{tmp_path.name}-vectors.sqlite3")
    answer = service.answer(tmp_path, "What is this repository?")

    chunks = tuple(service.stream_answer(answer))

    assert chunks
    assert "".join(chunks) == f"{answer.answer} "


def test_repository_qa_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(
            environment="test",
            conversation_database_path=tmp_path / "memory.sqlite3",
            vector_database_path=tmp_path / "vectors.sqlite3",
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/question",
        json={"repository_path": str(tmp_path), "question": "What is this repository?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "summary"
    assert body["session_id"]
    assert body["supporting_files"]
    assert body["confidence"] > 0

    followup_response = client.post(
        "/api/repositories/question",
        json={
            "repository_path": str(tmp_path),
            "question": "How does auth work?",
            "session_id": body["session_id"],
        },
    )
    history_response = client.get(f"/api/repositories/conversations/{body['session_id']}")

    assert followup_response.status_code == 200
    assert followup_response.json()["session_id"] == body["session_id"]
    assert history_response.status_code == 200
    assert len(history_response.json()["messages"]) == 4


def test_repository_qa_stream_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    app = create_app(
        Settings(
            environment="test",
            conversation_database_path=tmp_path / "memory.sqlite3",
            vector_database_path=tmp_path / "vectors.sqlite3",
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/repositories/question/stream",
        json={"repository_path": str(tmp_path), "question": "What is this repository?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: answer.start" in response.text
    assert "event: answer.delta" in response.text
    assert "event: answer.metadata" in response.text
    assert "event: answer.done" in response.text


def test_repository_qa_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    app = create_app(
        Settings(
            environment="test",
            conversation_database_path=tmp_path / "memory.sqlite3",
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
    qa_response = client.post(
        f"/api/repositories/imports/{import_id}/question",
        json={"question": "How does auth work?"},
    )

    assert import_response.status_code == 201
    assert qa_response.status_code == 200
    assert qa_response.json()["supporting_files"]
    assert qa_response.json()["session_id"]


def test_repository_qa_stream_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    app = create_app(
        Settings(
            environment="test",
            conversation_database_path=tmp_path / "memory.sqlite3",
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
    stream_response = client.post(
        f"/api/repositories/imports/{import_id}/question/stream",
        json={"question": "How does auth work?"},
    )

    assert import_response.status_code == 201
    assert stream_response.status_code == 200
    assert "session_id" in stream_response.text
    assert "event: answer.done" in stream_response.text


def test_repository_qa_api_rejects_missing_repository(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test"))
    client = TestClient(app)

    response = client.post(
        "/api/repositories/question",
        json={"repository_path": str(tmp_path / "missing"), "question": "What is this?"},
    )

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]
