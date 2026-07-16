from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RepositoryChunkRequest(BaseModel):
    """Request body for chunking a repository."""

    repository_path: Path


class RepositoryChunkStatsResponse(BaseModel):
    """Summary counts for repository chunks."""

    source_file_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    file_chunk_count: int = Field(ge=0)
    symbol_chunk_count: int = Field(ge=0)
    skipped_file_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class SkippedChunkFileResponse(BaseModel):
    """A source file skipped while chunking."""

    path: str
    reason: str

    model_config = ConfigDict(frozen=True)


class RepositoryChunkResponseItem(BaseModel):
    """One repository text chunk."""

    id: str
    kind: str
    path: str
    language: str
    content: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    char_count: int = Field(ge=0)
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None

    model_config = ConfigDict(frozen=True)


class RepositoryChunksResponse(BaseModel):
    """Chunks generated for a repository."""

    repository_path: str
    chunks: list[RepositoryChunkResponseItem]
    skipped_files: list[SkippedChunkFileResponse]
    stats: RepositoryChunkStatsResponse

    model_config = ConfigDict(frozen=True)
