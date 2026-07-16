import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import OpenAI

from backend.app.services.repository_chunker import (
    RepositoryChunk,
    RepositoryChunkerService,
    SkippedChunkFile,
)

DEFAULT_EMBEDDING_BATCH_SIZE = 64
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when repository embedding generation fails."""


class EmbeddingClient(Protocol):
    """Minimal embedding client surface used by the service."""

    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        """Generate embedding vectors for text inputs."""


class OpenAIEmbeddingClient:
    """OpenAI-backed embedding client."""

    def __init__(self, api_key: str) -> None:
        self.client = OpenAI(api_key=api_key)

    def create_embeddings(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        try:
            response = self.client.embeddings.create(model=model, input=inputs)
        except Exception as error:
            logger.exception("OpenAI embedding request failed.")
            raise EmbeddingError(str(error)) from error
        return [list(item.embedding) for item in response.data]


@dataclass(frozen=True)
class ChunkEmbedding:
    """An embedding vector generated for one repository chunk."""

    chunk_id: str
    path: str
    kind: str
    language: str
    start_line: int
    end_line: int
    embedding: tuple[float, ...]
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None


@dataclass(frozen=True)
class RepositoryEmbeddingStats:
    """Summary counts for an embedding generation run."""

    chunk_count: int
    embedding_count: int
    dimensions: int
    skipped_file_count: int


@dataclass(frozen=True)
class RepositoryEmbeddings:
    """Embedding vectors generated for repository chunks."""

    repository_path: str
    model: str
    embeddings: tuple[ChunkEmbedding, ...]
    skipped_files: tuple[SkippedChunkFile, ...]
    stats: RepositoryEmbeddingStats


class EmbeddingService:
    """Generates embeddings for repository chunks."""

    def __init__(
        self,
        chunker: RepositoryChunkerService,
        client: EmbeddingClient | None,
        model: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        self.chunker = chunker
        self.client = client
        self.model = model
        self.batch_size = batch_size

    def embed_repository(self, repository_path: Path) -> RepositoryEmbeddings:
        if self.client is None:
            raise EmbeddingError("OpenAI API key is not configured.")

        chunks = self.chunker.chunk_repository(repository_path)
        embeddable_chunks = [chunk for chunk in chunks.chunks if chunk.content.strip()]
        embeddings: list[ChunkEmbedding] = []

        for batch in self._batches(embeddable_chunks):
            vectors = self.client.create_embeddings(
                model=self.model,
                inputs=[chunk.content for chunk in batch],
            )
            if len(vectors) != len(batch):
                raise EmbeddingError("Embedding response count did not match chunk count.")
            embeddings.extend(
                self._chunk_embedding(chunk, vector)
                for chunk, vector in zip(batch, vectors, strict=True)
            )

        dimensions = len(embeddings[0].embedding) if embeddings else 0
        return RepositoryEmbeddings(
            repository_path=chunks.repository_path,
            model=self.model,
            embeddings=tuple(embeddings),
            skipped_files=chunks.skipped_files,
            stats=RepositoryEmbeddingStats(
                chunk_count=len(embeddable_chunks),
                embedding_count=len(embeddings),
                dimensions=dimensions,
                skipped_file_count=len(chunks.skipped_files),
            ),
        )

    def _batches(self, chunks: list[RepositoryChunk]) -> list[list[RepositoryChunk]]:
        return [
            chunks[index : index + self.batch_size]
            for index in range(0, len(chunks), self.batch_size)
        ]

    def _chunk_embedding(self, chunk: RepositoryChunk, vector: list[float]) -> ChunkEmbedding:
        return ChunkEmbedding(
            chunk_id=chunk.id,
            path=chunk.path,
            kind=chunk.kind,
            language=chunk.language,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            symbol_kind=chunk.symbol_kind,
            symbol_name=chunk.symbol_name,
            symbol_parent=chunk.symbol_parent,
            embedding=tuple(vector),
        )
