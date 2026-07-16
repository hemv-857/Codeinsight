from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RepositoryQARequest(BaseModel):
    """Request body for repository Q&A."""

    repository_path: Path
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class ImportedRepositoryQARequest(BaseModel):
    """Request body for imported repository Q&A."""

    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class RepositoryQASnippetResponse(BaseModel):
    """Retrieved source snippet supporting an answer."""

    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    content: str
    score: float

    model_config = ConfigDict(frozen=True)


class RepositoryQAResponse(BaseModel):
    """Grounded repository Q&A response."""

    repository_path: str
    question: str
    answer: str
    mode: str
    confidence: float = Field(ge=0, le=1)
    supporting_files: list[str]
    supporting_symbols: list[str]
    snippets: list[RepositoryQASnippetResponse]

    model_config = ConfigDict(frozen=True)
