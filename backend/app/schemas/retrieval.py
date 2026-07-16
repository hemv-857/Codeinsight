from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class HybridRetrievalRequest(BaseModel):
    """Request body for hybrid retrieval against a repository path."""

    repository_path: Path
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class ImportedHybridRetrievalRequest(BaseModel):
    """Request body for hybrid retrieval against an imported repository."""

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class HybridRetrievalResultResponse(BaseModel):
    """One ranked hybrid retrieval result."""

    chunk_id: str
    path: str
    kind: str
    language: str
    start_line: int
    end_line: int
    content: str
    score: float
    vector_score: float
    keyword_score: float
    graph_score: float
    related_paths: list[str]
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None

    model_config = ConfigDict(frozen=True)


class HybridRetrievalStatsResponse(BaseModel):
    """Summary counts for a hybrid retrieval query."""

    result_count: int = Field(ge=0)
    searched_embedding_count: int = Field(ge=0)
    dimensions: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class HybridRetrievalResponse(BaseModel):
    """Hybrid retrieval response."""

    repository_path: str
    query: str
    model: str
    results: list[HybridRetrievalResultResponse]
    stats: HybridRetrievalStatsResponse

    model_config = ConfigDict(frozen=True)
