import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_knowledge_graph_service
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from graph.fallback_repository import FallbackKnowledgeGraphRepository
from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphError,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
    KnowledgeGraphService,
)
from graph.neo4j_repository import Neo4jKnowledgeGraphRepository
from graph.networkx_repository import NetworkXKnowledgeGraphRepository
from graph.persistent_repository import PersistentKnowledgeGraphRepository
from graph.sqlite_repository import SQLiteKnowledgeGraphRepository
from parser.tree_sitter_parser import TreeSitterParserService


class FailingKnowledgeGraphRepository(KnowledgeGraphRepository):
    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        raise RuntimeError("Neo4j unavailable")


class RecordingKnowledgeGraphRepository(KnowledgeGraphRepository):
    def __init__(self) -> None:
        self.graph: KnowledgeGraph | None = None

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        self.graph = graph
        return KnowledgeGraphPersistenceResult(
            persisted=True,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            backend="test",
        )


class FakeNeo4jSession:
    def __init__(self) -> None:
        self.queries: list[tuple[str, dict[str, object]]] = []

    def __enter__(self) -> "FakeNeo4jSession":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def run(self, query: str, **parameters: object) -> object:
        self.queries.append((query, parameters))
        return object()


class FakeNeo4jDriver:
    def __init__(self) -> None:
        self.session_instance = FakeNeo4jSession()

    def session(self, *, database: str) -> FakeNeo4jSession:
        return self.session_instance


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repository_fixture(path: Path) -> None:
    write_file(
        path / "app" / "main.py",
        "\n".join(
            [
                "from app.service import helper",
                "",
                "def main():",
                "    helper()",
                "",
            ]
        ),
    )
    write_file(
        path / "app" / "service.py",
        "\n".join(
            [
                "class Base:",
                "    pass",
                "",
                "class Service(Base):",
                "    def load(self):",
                "        helper()",
                "",
                "def helper():",
                "    return 1",
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


def create_service(repository: KnowledgeGraphRepository) -> KnowledgeGraphService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return KnowledgeGraphService(
        scanner=scanner,
        parser=parser,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        call_graph=CallGraphService(scanner=scanner, parser=parser),
        repository=repository,
    )


def test_knowledge_graph_builds_repository_nodes_edges_and_stats(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    repository = RecordingKnowledgeGraphRepository()
    service = create_service(repository)

    graph, persistence = service.build_and_persist(tmp_path)

    labels_by_id = {node.id: node.labels for node in graph.nodes}
    relationships = {(edge.source, edge.relationship, edge.target) for edge in graph.edges}
    assert persistence.persisted is True
    assert "repository:" + str(tmp_path.resolve()) in labels_by_id
    assert "file:app/main.py" in labels_by_id
    assert "symbol:app/main.py:function:main" in labels_by_id
    assert ("file:app/main.py", "IMPORTS", "file:app/service.py") in relationships
    assert (
        "symbol:app/main.py:function:main",
        "CALLS",
        "symbol:app/service.py:function:helper",
    ) in relationships
    assert graph.stats.file_count == 2
    assert graph.stats.dependency_edge_count == 1
    assert graph.stats.call_edge_count == 2
    assert repository.graph == graph


def test_neo4j_repository_replaces_graph_with_cypher_writes(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(RecordingKnowledgeGraphRepository())
    graph = service.build(tmp_path)
    driver = FakeNeo4jDriver()
    repository = Neo4jKnowledgeGraphRepository(driver=driver, database="neo4j")

    result = repository.replace(graph)

    queries = [query for query, _parameters in driver.session_instance.queries]
    assert result.persisted is True
    assert result.backend == "neo4j"
    assert queries[0].startswith("MATCH (n:ForgeNode")
    assert any("MERGE (n:ForgeNode:Repository" in query for query in queries)
    assert any("MERGE (source)-[edge:CALLS]" in query for query in queries)


def test_networkx_repository_replaces_in_memory_graph(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(RecordingKnowledgeGraphRepository())
    graph = service.build(tmp_path)
    repository = NetworkXKnowledgeGraphRepository()

    result = repository.replace(graph)

    assert result.backend == "networkx"
    assert repository.graph.number_of_nodes() == len(graph.nodes)
    assert repository.graph.number_of_edges() == len(graph.edges)
    assert repository.graph.has_node("file:app/main.py")
    assert repository.graph.has_edge("file:app/main.py", "file:app/service.py", key="IMPORTS")


def test_sqlite_repository_replaces_and_reads_graph_snapshot(tmp_path: Path) -> None:
    repository_path = tmp_path / "repo"
    repository_path.mkdir()
    create_repository_fixture(repository_path)
    service = create_service(RecordingKnowledgeGraphRepository())
    graph = service.build(repository_path)
    repository = SQLiteKnowledgeGraphRepository(str(tmp_path / "graphs.sqlite3"))

    result = repository.replace(graph)
    stored = repository.get(graph.repository_path)

    assert result.backend == "sqlite"
    assert result.durable_backend is None
    assert stored.repository_path == graph.repository_path
    assert stored.stats == graph.stats
    assert {node.id: node.labels for node in stored.nodes} == {
        node.id: node.labels for node in graph.nodes
    }
    assert {(edge.source, edge.relationship, edge.target) for edge in stored.edges} == {
        (edge.source, edge.relationship, edge.target) for edge in graph.edges
    }


def test_persistent_repository_writes_live_backend_and_durable_snapshot(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(RecordingKnowledgeGraphRepository())
    graph = service.build(tmp_path)
    live_repository = RecordingKnowledgeGraphRepository()
    durable_repository = SQLiteKnowledgeGraphRepository(str(tmp_path / "graphs.sqlite3"))
    repository = PersistentKnowledgeGraphRepository(
        live_repository=live_repository,
        durable_repository=durable_repository,
    )

    result = repository.replace(graph)

    assert result.persisted is True
    assert result.backend == "test"
    assert result.durable_backend == "sqlite"
    assert live_repository.graph == graph
    assert durable_repository.get(graph.repository_path).stats == graph.stats


def test_knowledge_graph_service_reports_persistence_errors(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(FailingKnowledgeGraphRepository())

    try:
        service.build_and_persist(tmp_path)
    except KnowledgeGraphError as error:
        assert "Neo4j unavailable" in str(error)
    else:
        raise AssertionError("Expected knowledge graph persistence to fail.")


def test_fallback_repository_uses_networkx_when_primary_fails(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    service = create_service(RecordingKnowledgeGraphRepository())
    graph = service.build(tmp_path)
    fallback = NetworkXKnowledgeGraphRepository()
    repository = FallbackKnowledgeGraphRepository(
        primary=FailingKnowledgeGraphRepository(),
        fallback=fallback,
    )

    result = repository.replace(graph)

    assert result.persisted is True
    assert result.backend == "networkx"
    assert fallback.graph.number_of_nodes() == len(graph.nodes)


def test_knowledge_graph_api_for_repository_path(tmp_path: Path) -> None:
    create_repository_fixture(tmp_path)
    repository = RecordingKnowledgeGraphRepository()
    app = create_app(Settings(environment="test"))
    app.dependency_overrides[get_knowledge_graph_service] = lambda: create_service(repository)
    client = TestClient(app)

    response = client.post(
        "/api/repositories/knowledge-graph",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence"]["persisted"] is True
    assert body["persistence"]["backend"] == "test"
    assert body["persistence"]["durable_backend"] is None
    assert body["stats"]["file_count"] == 2
    assert body["stats"]["call_edge_count"] == 2


def test_knowledge_graph_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    repository = RecordingKnowledgeGraphRepository()
    app = create_app(Settings(environment="test", repository_storage_path=tmp_path / "imports"))
    app.dependency_overrides[get_knowledge_graph_service] = lambda: create_service(repository)
    client = TestClient(app)

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    graph_response = client.get(f"/api/repositories/imports/{import_id}/knowledge-graph")

    assert graph_response.status_code == 200
    assert graph_response.json()["stats"]["dependency_edge_count"] == 1
