from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ParseFileRequest(BaseModel):
    """Request body for parsing one source file."""

    path: Path


class SourcePoint(BaseModel):
    """Zero-indexed source position."""

    row: int = Field(ge=0)
    column: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class ParseTreeResponse(BaseModel):
    """Compact Tree-sitter parse result."""

    path: str
    language: str
    root_node_type: str
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    start_point: SourcePoint
    end_point: SourcePoint
    has_error: bool
    named_child_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class ParseRepositoryResponse(BaseModel):
    """Parse results for supported files in a repository."""

    repository_path: str
    parsed_files: list[ParseTreeResponse]

    model_config = ConfigDict(frozen=True)
