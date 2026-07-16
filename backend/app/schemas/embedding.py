from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.repository_chunk import SkippedChunkFileResponse


class RepositoryEmbeddingRequest(BaseModel):
    """Request body for generating repository embeddings."""

    repository_path: Path


class RepositoryEmbeddingStatsResponse(BaseModel):
    """Summary counts for generated embeddings."""

    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    dimensions: int = Field(ge=0)
    skipped_file_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class ChunkEmbeddingResponse(BaseModel):
    """Embedding vector for one repository chunk."""

    chunk_id: str
    path: str
    kind: str
    language: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    embedding: list[float]
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None

    model_config = ConfigDict(frozen=True)


class RepositoryEmbeddingsResponse(BaseModel):
    """Generated embeddings for repository chunks."""

    repository_path: str
    model: str
    embeddings: list[ChunkEmbeddingResponse]
    skipped_files: list[SkippedChunkFileResponse]
    stats: RepositoryEmbeddingStatsResponse

    model_config = ConfigDict(frozen=True)
