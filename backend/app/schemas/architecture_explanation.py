from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ArchitectureExplanationRequest(BaseModel):
    """Request body for explaining repository architecture."""

    repository_path: Path
    focus: str | None = Field(default=None, min_length=1)


class ImportedArchitectureExplanationRequest(BaseModel):
    """Request body for explaining imported repository architecture."""

    focus: str | None = Field(default=None, min_length=1)


class ArchitectureComponentResponse(BaseModel):
    """A component in an architecture explanation."""

    name: str
    path: str
    role: str
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class ArchitectureExplanationResponse(BaseModel):
    """Grounded architecture explanation response."""

    repository_path: str
    focus: str | None
    overview: str
    components: list[ArchitectureComponentResponse]
    dependency_flow: list[str]
    call_flow: list[str]
    observations: list[str]
    evidence_paths: list[str]
    confidence: float = Field(ge=0, le=1)

    model_config = ConfigDict(frozen=True)
