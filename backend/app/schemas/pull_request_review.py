from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReviewSeverityResponse = Literal["low", "medium", "high", "critical"]


class PullRequestReviewRequest(BaseModel):
    """Request body for reviewing a pull request."""

    repository_path: Path
    changed_files: list[str] = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    diff_text: str | None = None


class ImportedPullRequestReviewRequest(BaseModel):
    """Request body for reviewing an imported repository pull request."""

    changed_files: list[str] = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    diff_text: str | None = None


class PullRequestFindingResponse(BaseModel):
    """One pull request review finding."""

    category: str
    severity: ReviewSeverityResponse
    path: str | None
    title: str
    description: str
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class PullRequestImpactFileResponse(BaseModel):
    """One file likely impacted by the pull request."""

    path: str
    reason: str
    score: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class PullRequestReviewStatsResponse(BaseModel):
    """Summary metrics for pull request review."""

    changed_file_count: int = Field(ge=0)
    impacted_file_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    risk_score: int = Field(ge=0, le=100)
    risk_level: ReviewSeverityResponse
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class PullRequestReviewResponse(BaseModel):
    """Pull request review response."""

    repository_path: str
    title: str | None
    description: str | None
    changed_files: list[str]
    impacted_files: list[PullRequestImpactFileResponse]
    findings: list[PullRequestFindingResponse]
    recommendations: list[str]
    summary: str
    stats: PullRequestReviewStatsResponse

    model_config = ConfigDict(frozen=True)
