from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ReadmeGenerationRequest(BaseModel):
    """Request body for generating a repository README."""

    repository_path: Path


class ReadmeSectionResponse(BaseModel):
    """One generated README section."""

    heading: str
    content: str

    model_config = ConfigDict(frozen=True)


class ReadmeStatsResponse(BaseModel):
    """Generated README output statistics."""

    section_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    language_count: int = Field(ge=0)
    key_file_count: int = Field(ge=0)
    key_symbol_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class GeneratedReadmeResponse(BaseModel):
    """Generated README response."""

    repository_path: str
    title: str
    markdown: str
    sections: list[ReadmeSectionResponse]
    evidence_paths: list[str]
    stats: ReadmeStatsResponse

    model_config = ConfigDict(frozen=True)
