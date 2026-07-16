from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SecuritySeverityResponse = Literal["low", "medium", "high", "critical"]


class SecurityReviewRequest(BaseModel):
    """Request body for reviewing changed files for security risks."""

    repository_path: Path
    changed_files: list[str] = Field(min_length=1)
    focus: str | None = None


class ImportedSecurityReviewRequest(BaseModel):
    """Request body for reviewing security risks in an imported repository."""

    changed_files: list[str] = Field(min_length=1)
    focus: str | None = None


class SecurityFindingResponse(BaseModel):
    """One security review finding."""

    category: str
    severity: SecuritySeverityResponse
    path: str
    line: int = Field(ge=1)
    title: str
    description: str
    evidence: list[str]
    remediation: str

    model_config = ConfigDict(frozen=True)


class SecurityReviewStatsResponse(BaseModel):
    """Summary metrics for security review."""

    changed_file_count: int = Field(ge=0)
    reviewed_file_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    risk_score: int = Field(ge=0, le=100)
    risk_level: SecuritySeverityResponse
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class SecurityReviewResponse(BaseModel):
    """Security review response."""

    repository_path: str
    focus: str | None
    changed_files: list[str]
    findings: list[SecurityFindingResponse]
    recommendations: list[str]
    summary: str
    stats: SecurityReviewStatsResponse

    model_config = ConfigDict(frozen=True)
