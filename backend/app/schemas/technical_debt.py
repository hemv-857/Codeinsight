from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DebtSeverityResponse = Literal["low", "medium", "high", "critical"]


class TechnicalDebtRequest(BaseModel):
    """Request body for technical debt analysis against a repository path."""

    repository_path: Path


class TechnicalDebtFindingResponse(BaseModel):
    """One technical debt finding in a repository."""

    category: str
    severity: DebtSeverityResponse
    path: str
    title: str
    description: str
    line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    symbol_name: str | None = None
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class TechnicalDebtStatsResponse(BaseModel):
    """Summary counts for a technical debt report."""

    file_count: int = Field(ge=0)
    parsed_file_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    score: int = Field(ge=0, le=100)

    model_config = ConfigDict(frozen=True)


class TechnicalDebtResponse(BaseModel):
    """Technical debt analysis response."""

    repository_path: str
    findings: list[TechnicalDebtFindingResponse]
    stats: TechnicalDebtStatsResponse

    model_config = ConfigDict(frozen=True)
