from dataclasses import dataclass
from pathlib import Path

from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.embedding import EmbeddingService


@dataclass(frozen=True)
class VectorStoreResult:
    """Result of storing repository embeddings."""

    repository_path: str
    model: str
    stored_embedding_count: int
    dimensions: int
    backend: str
    skipped_file_count: int


class VectorStoreService:
    """Generates and stores repository embedding vectors."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        repository: VectorStoreRepository,
    ) -> None:
        self.embedding_service = embedding_service
        self.repository = repository

    def index_repository(self, repository_path: Path) -> VectorStoreResult:
        embeddings = self.embedding_service.embed_repository(repository_path)
        stored_count = self.repository.replace(embeddings)
        return VectorStoreResult(
            repository_path=embeddings.repository_path,
            model=embeddings.model,
            stored_embedding_count=stored_count,
            dimensions=embeddings.stats.dimensions,
            backend="sqlite",
            skipped_file_count=embeddings.stats.skipped_file_count,
        )
