from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DeadCodeKindResponse = Literal["unused_file", "unused_callable"]


class DeadCodeRequest(BaseModel):
    """Request body for dead code detection."""

    repository_path: Path


class DeadCodeFindingResponse(BaseModel):
    """One candidate dead code finding."""

    kind: DeadCodeKindResponse
    path: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    line: int | None = Field(default=None, ge=1)
    symbol_name: str | None = None
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class DeadCodeStatsResponse(BaseModel):
    """Summary counts for dead code detection."""

    file_count: int = Field(ge=0)
    callable_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)
    unused_file_count: int = Field(ge=0)
    unused_callable_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class DeadCodeResponse(BaseModel):
    """Dead code detection response."""

    repository_path: str
    findings: list[DeadCodeFindingResponse]
    stats: DeadCodeStatsResponse

    model_config = ConfigDict(frozen=True)
