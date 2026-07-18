from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ContributionSeverity = Literal["low", "medium", "high", "critical"]
ContributionCategory = Literal[
    "bug",
    "security",
    "code_smell",
    "missing_test",
    "missing_docs",
    "performance",
    "accessibility",
    "api_design",
]


class OpenSourceContributionRequest(BaseModel):
    """Request body for analyzing a repository for open source contribution opportunities."""

    repository_path: Path | None = None
    github_url: str | None = None
    focus: str | None = None


class ImportedOpenSourceContributionRequest(BaseModel):
    """Request body for analyzing an imported repository for contribution opportunities."""

    focus: str | None = None


class ContributionFindingResponse(BaseModel):
    """One contribution finding with suggested fix."""

    category: ContributionCategory
    severity: ContributionSeverity
    path: str
    line: int = Field(ge=1)
    title: str
    description: str
    evidence: list[str]
    suggested_fix: str
    impact: str
    effort: str

    model_config = ConfigDict(frozen=True)


class ContributionStatsResponse(BaseModel):
    """Summary metrics for open source contribution analysis."""

    file_count: int = Field(ge=0)
    scanned_file_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    bug_count: int = Field(ge=0)
    security_count: int = Field(ge=0)
    code_smell_count: int = Field(ge=0)
    missing_test_count: int = Field(ge=0)
    missing_docs_count: int = Field(ge=0)
    performance_count: int = Field(ge=0)
    contribution_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class OpenSourceContributionResponse(BaseModel):
    """Open source contribution analysis response."""

    repository_path: str
    focus: str | None
    findings: list[ContributionFindingResponse]
    recommendations: list[str]
    summary: str
    stats: ContributionStatsResponse

    model_config = ConfigDict(frozen=True)
