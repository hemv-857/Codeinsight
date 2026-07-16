from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
)


class PersistentKnowledgeGraphRepository(KnowledgeGraphRepository):
    """Writes graphs to a live backend and a durable snapshot store."""

    def __init__(
        self,
        live_repository: KnowledgeGraphRepository,
        durable_repository: KnowledgeGraphRepository,
    ) -> None:
        self.live_repository = live_repository
        self.durable_repository = durable_repository

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        live_result = self.live_repository.replace(graph)
        durable_result = self.durable_repository.replace(graph)
        return KnowledgeGraphPersistenceResult(
            persisted=live_result.persisted and durable_result.persisted,
            node_count=durable_result.node_count,
            edge_count=durable_result.edge_count,
            backend=live_result.backend,
            durable_backend=durable_result.backend,
        )
