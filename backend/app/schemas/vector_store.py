from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class VectorStoreRequest(BaseModel):
    """Request body for indexing repository vectors."""

    repository_path: Path


class VectorStoreResponse(BaseModel):
    """Result of storing repository embedding vectors."""

    repository_path: str
    model: str
    stored_embedding_count: int = Field(ge=0)
    dimensions: int = Field(ge=0)
    backend: str
    skipped_file_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)
