import logging

from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphRepository,
)

logger = logging.getLogger(__name__)


class FallbackKnowledgeGraphRepository(KnowledgeGraphRepository):
    """Persists to a primary graph backend, falling back when it is unavailable."""

    def __init__(
        self,
        primary: KnowledgeGraphRepository,
        fallback: KnowledgeGraphRepository,
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        try:
            return self.primary.replace(graph)
        except Exception:
            logger.exception("Primary knowledge graph backend failed; using fallback.")
            return self.fallback.replace(graph)
