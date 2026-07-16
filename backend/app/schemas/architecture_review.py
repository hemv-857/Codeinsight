from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ArchitectureReviewSeverityResponse = Literal["low", "medium", "high", "critical"]


class ArchitectureReviewRequest(BaseModel):
    """Request body for reviewing proposed architecture changes."""

    repository_path: Path
    changed_files: list[str] = Field(min_length=1)
    focus: str | None = None


class ImportedArchitectureReviewRequest(BaseModel):
    """Request body for reviewing architecture changes in an imported repository."""

    changed_files: list[str] = Field(min_length=1)
    focus: str | None = None


class ArchitectureReviewFindingResponse(BaseModel):
    """One architecture review finding."""

    category: str
    severity: ArchitectureReviewSeverityResponse
    path: str | None
    title: str
    description: str
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class ArchitectureReviewImpactFileResponse(BaseModel):
    """One architecture-impact file."""

    path: str
    layer: str
    reason: str
    score: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class ArchitectureReviewStatsResponse(BaseModel):
    """Summary metrics for architecture review."""

    changed_file_count: int = Field(ge=0)
    impacted_file_count: int = Field(ge=0)
    violation_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    risk_score: int = Field(ge=0, le=100)
    risk_level: ArchitectureReviewSeverityResponse
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class ArchitectureReviewResponse(BaseModel):
    """Architecture review response."""

    repository_path: str
    focus: str | None
    changed_files: list[str]
    impacted_files: list[ArchitectureReviewImpactFileResponse]
    findings: list[ArchitectureReviewFindingResponse]
    recommendations: list[str]
    summary: str
    stats: ArchitectureReviewStatsResponse

    model_config = ConfigDict(frozen=True)
