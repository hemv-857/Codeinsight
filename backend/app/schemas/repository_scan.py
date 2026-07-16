from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RepositoryScanRequest(BaseModel):
    """Request body for scanning an existing repository path."""

    repository_path: Path


class RepositoryFileEntry(BaseModel):
    """Metadata for a discovered repository file."""

    path: str
    extension: str
    language: str | None
    size_bytes: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class RepositoryScanResult(BaseModel):
    """Recursive repository scan result."""

    repository_path: str
    files: list[RepositoryFileEntry]
    directories: list[str]
    extensions: list[str]
    languages: list[str]

    model_config = ConfigDict(frozen=True)
