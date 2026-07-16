from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class CallGraphRequest(BaseModel):
    """Request body for building a repository call graph."""

    repository_path: Path


class CallGraphNodeResponse(BaseModel):
    """Callable symbol node in a call graph."""

    id: str
    name: str
    kind: str
    path: str
    line: int = Field(ge=1)
    parent: str | None = None

    model_config = ConfigDict(frozen=True)


class CallGraphEdgeResponse(BaseModel):
    """Call edge between callable symbols."""

    source: str | None
    target: str | None
    caller: str | None
    callee: str
    path: str
    line: int = Field(ge=1)
    recursive: bool

    model_config = ConfigDict(frozen=True)


class CallGraphStatsResponse(BaseModel):
    """Summary counts for a call graph."""

    callable_count: int = Field(ge=0)
    call_count: int = Field(ge=0)
    resolved_call_count: int = Field(ge=0)
    unresolved_call_count: int = Field(ge=0)
    recursive_call_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class CallGraphResponse(BaseModel):
    """Call graph response for one repository."""

    repository_path: str
    nodes: list[CallGraphNodeResponse]
    edges: list[CallGraphEdgeResponse]
    unresolved_calls: list[str]
    stats: CallGraphStatsResponse

    model_config = ConfigDict(frozen=True)
