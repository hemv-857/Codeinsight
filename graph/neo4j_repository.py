from contextlib import AbstractContextManager
from typing import Protocol

from neo4j import GraphDatabase

from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
)


class Neo4jSession(Protocol):
    """Minimal Neo4j session surface used by the repository."""

    def run(self, query: str, **parameters: object) -> object:
        """Run one Cypher statement."""


class Neo4jDriver(Protocol):
    """Minimal Neo4j driver surface used by the repository."""

    def session(self, *, database: str) -> AbstractContextManager[Neo4jSession]:
        """Open a Neo4j session for a database."""


class Neo4jKnowledgeGraphRepository(KnowledgeGraphRepository):
    """Persists repository knowledge graphs into Neo4j."""

    def __init__(self, driver: Neo4jDriver, database: str) -> None:
        self.driver = driver
        self.database = database

    @classmethod
    def connect(
        cls,
        uri: str,
        username: str,
        password: str,
        database: str,
    ) -> "Neo4jKnowledgeGraphRepository":
        """Create a Neo4j-backed repository from connection settings."""
        driver = GraphDatabase.driver(uri, auth=(username, password))
        return cls(driver=driver, database=database)

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (n:ForgeNode {repository_path: $repository_path}) DETACH DELETE n",
                repository_path=graph.repository_path,
            )
            for node in graph.nodes:
                labels = ":".join(self._safe_identifier(label) for label in node.labels)
                session.run(
                    f"MERGE (n:{labels} {{id: $id}}) SET n += $properties",
                    id=node.id,
                    properties=node.properties,
                )
            for edge in graph.edges:
                relationship = self._safe_identifier(edge.relationship)
                session.run(
                    (
                        "MATCH (source:ForgeNode {id: $source_id}) "
                        "MATCH (target:ForgeNode {id: $target_id}) "
                        f"MERGE (source)-[edge:{relationship}]->(target) "
                        "SET edge += $properties"
                    ),
                    source_id=edge.source,
                    target_id=edge.target,
                    properties=edge.properties,
                )
        return KnowledgeGraphPersistenceResult(
            persisted=True,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            backend="neo4j",
            durable_backend="neo4j",
        )

    def _safe_identifier(self, value: str) -> str:
        if not value.replace("_", "").isalnum():
            raise ValueError("Neo4j labels and relationship types must be alphanumeric.")
        return value
