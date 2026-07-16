from typing import Any

import networkx as nx

from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
)


class NetworkXKnowledgeGraphRepository(KnowledgeGraphRepository):
    """Keeps the latest repository knowledge graph in memory with NetworkX."""

    def __init__(self) -> None:
        self.graph: nx.MultiDiGraph[Any] = nx.MultiDiGraph()

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        memory_graph: nx.MultiDiGraph[Any] = nx.MultiDiGraph(repository_path=graph.repository_path)
        for node in graph.nodes:
            memory_graph.add_node(node.id, labels=node.labels, **node.properties)
        for edge in graph.edges:
            memory_graph.add_edge(
                edge.source,
                edge.target,
                key=edge.relationship,
                relationship=edge.relationship,
                **edge.properties,
            )
        self.graph = memory_graph
        return KnowledgeGraphPersistenceResult(
            persisted=True,
            node_count=memory_graph.number_of_nodes(),
            edge_count=memory_graph.number_of_edges(),
            backend="networkx",
        )
