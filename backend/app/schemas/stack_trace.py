from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TraceLanguageResponse = Literal["python", "javascript", "java", "go", "unknown"]


class StackTraceParseRequest(BaseModel):
    """Request body for stack trace parsing."""

    stack_trace: str = Field(min_length=1)


class StackTraceFrameResponse(BaseModel):
    """One parsed stack trace frame."""

    file_path: str
    line: int = Field(ge=1)
    column: int | None = Field(default=None, ge=1)
    function: str | None = None
    language: TraceLanguageResponse
    raw: str

    model_config = ConfigDict(frozen=True)


class StackTraceStatsResponse(BaseModel):
    """Summary counts for parsed stack trace frames."""

    frame_count: int = Field(ge=0)
    language: TraceLanguageResponse
    file_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class StackTraceParseResponse(BaseModel):
    """Parsed stack trace response."""

    raw: str
    language: TraceLanguageResponse
    error_type: str | None
    message: str | None
    frames: list[StackTraceFrameResponse]
    files: list[str]
    stats: StackTraceStatsResponse

    model_config = ConfigDict(frozen=True)
