from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class DependencyGraphRequest(BaseModel):
    """Request body for building a repository dependency graph."""

    repository_path: Path


class DependencyNodeResponse(BaseModel):
    """A source file node in the dependency graph."""

    path: str
    language: str

    model_config = ConfigDict(frozen=True)


class DependencyEdgeResponse(BaseModel):
    """A source-level dependency edge."""

    source: str
    target: str | None
    import_name: str
    import_source: str | None
    dependency_type: str

    model_config = ConfigDict(frozen=True)


class DependencyGraphStatsResponse(BaseModel):
    """Summary counts for a dependency graph."""

    file_count: int = Field(ge=0)
    internal_dependency_count: int = Field(ge=0)
    external_dependency_count: int = Field(ge=0)
    unresolved_dependency_count: int = Field(ge=0)
    circular_dependency_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class DependencyGraphResponse(BaseModel):
    """Dependency graph response for one repository."""

    repository_path: str
    nodes: list[DependencyNodeResponse]
    edges: list[DependencyEdgeResponse]
    external_dependencies: list[str]
    unresolved_imports: list[str]
    circular_dependencies: list[list[str]]
    stats: DependencyGraphStatsResponse

    model_config = ConfigDict(frozen=True)
