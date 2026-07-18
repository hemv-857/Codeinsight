import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.database.connection import create_sqlite_engine
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    delete,
    insert,
    select,
)

from graph.knowledge_graph import (
    GraphProperty,
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
    KnowledgeGraphStats,
)

metadata = MetaData()

knowledge_graphs_table = Table(
    "knowledge_graphs",
    metadata,
    Column("repository_path", Text, primary_key=True),
    Column("node_count", Integer, nullable=False),
    Column("edge_count", Integer, nullable=False),
    Column("file_count", Integer, nullable=False),
    Column("symbol_count", Integer, nullable=False),
    Column("dependency_edge_count", Integer, nullable=False),
    Column("call_edge_count", Integer, nullable=False),
    Column("persisted_at", String, nullable=False),
)

knowledge_graph_nodes_table = Table(
    "knowledge_graph_nodes",
    metadata,
    Column(
        "repository_path",
        Text,
        ForeignKey("knowledge_graphs.repository_path", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("node_id", Text, primary_key=True),
    Column("labels", Text, nullable=False),
    Column("properties", Text, nullable=False),
)

knowledge_graph_edges_table = Table(
    "knowledge_graph_edges",
    metadata,
    Column(
        "repository_path",
        Text,
        ForeignKey("knowledge_graphs.repository_path", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("edge_index", Integer, primary_key=True),
    Column("source", Text, nullable=False),
    Column("target", Text, nullable=False),
    Column("relationship", String, nullable=False),
    Column("properties", Text, nullable=False),
)


class SQLiteKnowledgeGraphRepository(KnowledgeGraphRepository):
    """Stores complete knowledge graph snapshots in SQLite."""

    def __init__(self, database_path: str) -> None:
        self.engine = create_sqlite_engine(Path(database_path))
        self.initialize()

    def initialize(self) -> None:
        metadata.create_all(self.engine)

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        persisted_at = datetime.now(UTC).isoformat()
        sqlite_max_variables = 900
        node_columns = 4
        edge_columns = 6
        node_batch_size = sqlite_max_variables // node_columns
        edge_batch_size = sqlite_max_variables // edge_columns
        with self.engine.begin() as connection:
            connection.execute(
                delete(knowledge_graph_edges_table).where(
                    knowledge_graph_edges_table.c.repository_path == graph.repository_path
                )
            )
            connection.execute(
                delete(knowledge_graph_nodes_table).where(
                    knowledge_graph_nodes_table.c.repository_path == graph.repository_path
                )
            )
            connection.execute(
                delete(knowledge_graphs_table).where(
                    knowledge_graphs_table.c.repository_path == graph.repository_path
                )
            )
            connection.execute(
                insert(knowledge_graphs_table),
                {
                    "repository_path": graph.repository_path,
                    "node_count": graph.stats.node_count,
                    "edge_count": graph.stats.edge_count,
                    "file_count": graph.stats.file_count,
                    "symbol_count": graph.stats.symbol_count,
                    "dependency_edge_count": graph.stats.dependency_edge_count,
                    "call_edge_count": graph.stats.call_edge_count,
                    "persisted_at": persisted_at,
                },
            )
            if graph.nodes:
                node_rows = [
                    {
                        "repository_path": graph.repository_path,
                        "node_id": node.id,
                        "labels": json.dumps(node.labels),
                        "properties": json.dumps(node.properties),
                    }
                    for node in graph.nodes
                ]
                for i in range(0, len(node_rows), node_batch_size):
                    connection.execute(
                        insert(knowledge_graph_nodes_table),
                        node_rows[i : i + node_batch_size],
                    )
            if graph.edges:
                edge_rows = [
                    {
                        "repository_path": graph.repository_path,
                        "edge_index": index,
                        "source": edge.source,
                        "target": edge.target,
                        "relationship": edge.relationship,
                        "properties": json.dumps(edge.properties),
                    }
                    for index, edge in enumerate(graph.edges)
                ]
                for i in range(0, len(edge_rows), edge_batch_size):
                    connection.execute(
                        insert(knowledge_graph_edges_table),
                        edge_rows[i : i + edge_batch_size],
                    )
        return KnowledgeGraphPersistenceResult(
            persisted=True,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            backend="sqlite",
        )

    def get(self, repository_path: str) -> KnowledgeGraph:
        with self.engine.connect() as connection:
            graph_row = (
                connection.execute(
                    select(knowledge_graphs_table).where(
                        knowledge_graphs_table.c.repository_path == repository_path
                    )
                )
                .mappings()
                .one_or_none()
            )
            if graph_row is None:
                raise KeyError("Knowledge graph snapshot was not found.")

            node_rows = (
                connection.execute(
                    select(knowledge_graph_nodes_table)
                    .where(knowledge_graph_nodes_table.c.repository_path == repository_path)
                    .order_by(knowledge_graph_nodes_table.c.node_id)
                )
                .mappings()
                .all()
            )
            edge_rows = (
                connection.execute(
                    select(knowledge_graph_edges_table)
                    .where(knowledge_graph_edges_table.c.repository_path == repository_path)
                    .order_by(knowledge_graph_edges_table.c.edge_index)
                )
                .mappings()
                .all()
            )

        return KnowledgeGraph(
            repository_path=repository_path,
            nodes=tuple(
                KnowledgeGraphNode(
                    id=str(row["node_id"]),
                    labels=tuple(str(label) for label in json.loads(str(row["labels"]))),
                    properties=self._decode_properties(str(row["properties"])),
                )
                for row in node_rows
            ),
            edges=tuple(
                KnowledgeGraphEdge(
                    source=str(row["source"]),
                    target=str(row["target"]),
                    relationship=str(row["relationship"]),
                    properties=self._decode_properties(str(row["properties"])),
                )
                for row in edge_rows
            ),
            stats=KnowledgeGraphStats(
                node_count=int(graph_row["node_count"]),
                edge_count=int(graph_row["edge_count"]),
                file_count=int(graph_row["file_count"]),
                symbol_count=int(graph_row["symbol_count"]),
                dependency_edge_count=int(graph_row["dependency_edge_count"]),
                call_edge_count=int(graph_row["call_edge_count"]),
            ),
        )

    def _decode_properties(self, value: str) -> dict[str, GraphProperty]:
        decoded = json.loads(value)
        if not isinstance(decoded, dict):
            raise ValueError("Knowledge graph properties must be a JSON object.")
        return {
            str(key): self._decode_property(property_value)
            for key, property_value in decoded.items()
        }

    def _decode_property(self, value: Any) -> GraphProperty:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value == int(value) else value
        if isinstance(value, str):
            return value
        raise ValueError("Knowledge graph properties must be strings, integers, or booleans.")
