from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeGraphRequest(BaseModel):
    """Request body for building and persisting a repository knowledge graph."""

    repository_path: Path


class KnowledgeGraphStatsResponse(BaseModel):
    """Summary counts for a knowledge graph."""

    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    file_count: int = Field(ge=0)
    symbol_count: int = Field(ge=0)
    dependency_edge_count: int = Field(ge=0)
    call_edge_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class KnowledgeGraphPersistenceResponse(BaseModel):
    """Neo4j persistence result."""

    persisted: bool
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph build and persistence response."""

    repository_path: str
    stats: KnowledgeGraphStatsResponse
    persistence: KnowledgeGraphPersistenceResponse

    model_config = ConfigDict(frozen=True)
