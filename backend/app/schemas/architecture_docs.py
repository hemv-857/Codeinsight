from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ArchitectureDocsRequest(BaseModel):
    """Request body for generating architecture documentation."""

    repository_path: Path
    focus: str | None = None


class ImportedArchitectureDocsRequest(BaseModel):
    """Request body for imported repository architecture documentation."""

    focus: str | None = None


class ArchitectureDocSectionResponse(BaseModel):
    """One generated architecture documentation section."""

    heading: str
    content: str

    model_config = ConfigDict(frozen=True)


class ArchitectureDocStatsResponse(BaseModel):
    """Generated architecture documentation statistics."""

    section_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    component_count: int = Field(ge=0)
    evidence_path_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class GeneratedArchitectureDocResponse(BaseModel):
    """Generated architecture documentation response."""

    repository_path: str
    title: str
    focus: str | None
    markdown: str
    sections: list[ArchitectureDocSectionResponse]
    evidence_paths: list[str]
    stats: ArchitectureDocStatsResponse

    model_config = ConfigDict(frozen=True)
