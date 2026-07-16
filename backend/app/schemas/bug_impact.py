from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.risk_scoring import RiskLevelResponse, RiskScoreResponse
from backend.app.schemas.stack_trace import StackTraceParseResponse


class BugImpactRequest(BaseModel):
    """Request body for bug impact prediction."""

    repository_path: Path
    stack_trace: str = Field(min_length=1)
    error: str | None = None
    changed_files: list[str] = Field(default_factory=list)


class ImportedBugImpactRequest(BaseModel):
    """Request body for imported repository bug impact prediction."""

    stack_trace: str = Field(min_length=1)
    error: str | None = None
    changed_files: list[str] = Field(default_factory=list)


class RootCauseCandidateResponse(BaseModel):
    """Likely root cause file and location."""

    path: str
    line: int | None = Field(default=None, ge=1)
    function: str | None = None
    score: float = Field(ge=0, le=1)
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class ImpactedFileResponse(BaseModel):
    """One file likely affected by the bug."""

    path: str
    reason: str
    score: float = Field(ge=0, le=1)

    model_config = ConfigDict(frozen=True)


class BugImpactStatsResponse(BaseModel):
    """Summary metrics for bug impact prediction."""

    frame_count: int = Field(ge=0)
    matched_frame_count: int = Field(ge=0)
    impacted_file_count: int = Field(ge=0)
    dependency_edge_count: int = Field(ge=0)
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevelResponse
    confidence: float = Field(ge=0, le=1)

    model_config = ConfigDict(frozen=True)


class BugImpactResponse(BaseModel):
    """Bug impact prediction response."""

    repository_path: str
    error_type: str | None
    message: str | None
    root_cause: RootCauseCandidateResponse | None
    impacted_files: list[ImpactedFileResponse]
    recommendations: list[str]
    parsed_trace: StackTraceParseResponse
    risk: RiskScoreResponse
    stats: BugImpactStatsResponse

    model_config = ConfigDict(frozen=True)
