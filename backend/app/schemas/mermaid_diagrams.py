from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class MermaidDiagramRequest(BaseModel):
    """Request body for generating Mermaid diagrams."""

    repository_path: Path
    focus: str | None = None


class ImportedMermaidDiagramRequest(BaseModel):
    """Request body for imported repository Mermaid diagrams."""

    focus: str | None = None


class MermaidDiagramResponse(BaseModel):
    """One generated Mermaid diagram."""

    kind: str
    title: str
    description: str
    code: str

    model_config = ConfigDict(frozen=True)


class MermaidDiagramStatsResponse(BaseModel):
    """Generated Mermaid diagram statistics."""

    diagram_count: int = Field(ge=0)
    dependency_edge_count: int = Field(ge=0)
    call_edge_count: int = Field(ge=0)
    component_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class MermaidDiagramSetResponse(BaseModel):
    """Generated Mermaid diagram response."""

    repository_path: str
    focus: str | None
    diagrams: list[MermaidDiagramResponse]
    stats: MermaidDiagramStatsResponse

    model_config = ConfigDict(frozen=True)
