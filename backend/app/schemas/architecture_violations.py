from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ViolationSeverityResponse = Literal["low", "medium", "high", "critical"]


class ArchitectureViolationRequest(BaseModel):
    """Request body for architecture violation detection."""

    repository_path: Path


class ArchitectureViolationResponseItem(BaseModel):
    """One architecture boundary violation."""

    rule_id: str
    severity: ViolationSeverityResponse
    source: str
    target: str
    import_name: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class ArchitectureViolationStatsResponse(BaseModel):
    """Summary counts for architecture violation detection."""

    dependency_count: int = Field(ge=0)
    violation_count: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class ArchitectureViolationResponse(BaseModel):
    """Architecture violation detection response."""

    repository_path: str
    violations: list[ArchitectureViolationResponseItem]
    stats: ArchitectureViolationStatsResponse

    model_config = ConfigDict(frozen=True)
