from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class CircularDependencyRequest(BaseModel):
    """Request body for circular dependency detection."""

    repository_path: Path


class CircularDependencyEdgeResponse(BaseModel):
    """One dependency edge participating in a cycle."""

    source: str
    target: str
    import_name: str

    model_config = ConfigDict(frozen=True)


class CircularDependencyCycleResponse(BaseModel):
    """One circular dependency cycle."""

    files: list[str]
    length: int = Field(ge=2)
    edges: list[CircularDependencyEdgeResponse]

    model_config = ConfigDict(frozen=True)


class CircularDependencyStatsResponse(BaseModel):
    """Summary counts for circular dependency detection."""

    cycle_count: int = Field(ge=0)
    affected_file_count: int = Field(ge=0)
    max_cycle_length: int = Field(ge=0)
    internal_dependency_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class CircularDependencyResponse(BaseModel):
    """Circular dependency detection response."""

    repository_path: str
    cycles: list[CircularDependencyCycleResponse]
    stats: CircularDependencyStatsResponse

    model_config = ConfigDict(frozen=True)
