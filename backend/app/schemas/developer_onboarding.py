from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class DeveloperOnboardingRequest(BaseModel):
    """Request body for generating developer onboarding documentation."""

    repository_path: Path
    focus: str | None = None


class ImportedDeveloperOnboardingRequest(BaseModel):
    """Request body for imported repository developer onboarding documentation."""

    focus: str | None = None


class DeveloperOnboardingSectionResponse(BaseModel):
    """One generated developer onboarding section."""

    heading: str
    content: str

    model_config = ConfigDict(frozen=True)


class DeveloperOnboardingStatsResponse(BaseModel):
    """Generated developer onboarding documentation statistics."""

    section_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    evidence_path_count: int = Field(ge=0)
    diagram_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class GeneratedDeveloperOnboardingResponse(BaseModel):
    """Generated developer onboarding documentation response."""

    repository_path: str
    title: str
    focus: str | None
    markdown: str
    sections: list[DeveloperOnboardingSectionResponse]
    evidence_paths: list[str]
    stats: DeveloperOnboardingStatsResponse

    model_config = ConfigDict(frozen=True)
