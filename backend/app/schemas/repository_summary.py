from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RepositorySummaryRequest(BaseModel):
    """Request body for summarizing a repository path."""

    repository_path: Path


class RepositorySummaryLanguageResponse(BaseModel):
    """Language usage in a repository summary."""

    language: str
    file_count: int = Field(ge=0)
    size_bytes: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class RepositorySummaryFileResponse(BaseModel):
    """Key file in a repository summary."""

    path: str
    language: str | None
    size_bytes: int = Field(ge=0)
    symbol_count: int = Field(ge=0)
    dependency_count: int = Field(ge=0)
    dependent_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class RepositorySummarySymbolResponse(BaseModel):
    """Key symbol in a repository summary."""

    name: str
    kind: str
    path: str
    line: int = Field(ge=1)
    parent: str | None = None

    model_config = ConfigDict(frozen=True)


class RepositorySummaryStatsResponse(BaseModel):
    """Summary metrics for a repository."""

    file_count: int = Field(ge=0)
    directory_count: int = Field(ge=0)
    language_count: int = Field(ge=0)
    parsed_file_count: int = Field(ge=0)
    skipped_parse_file_count: int = Field(ge=0)
    symbol_count: int = Field(ge=0)
    dependency_count: int = Field(ge=0)
    callable_count: int = Field(ge=0)
    call_count: int = Field(ge=0)
    indexed_embedding_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class RepositorySummaryResponse(BaseModel):
    """Grounded repository summary response."""

    repository_path: str
    overview: str
    languages: list[RepositorySummaryLanguageResponse]
    key_files: list[RepositorySummaryFileResponse]
    key_symbols: list[RepositorySummarySymbolResponse]
    dependency_highlights: list[str]
    call_highlights: list[str]
    evidence_paths: list[str]
    embedding_indexed: bool
    stats: RepositorySummaryStatsResponse

    model_config = ConfigDict(frozen=True)
