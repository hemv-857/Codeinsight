from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetadataPersistRequest(BaseModel):
    """Request body for persisting repository scan metadata."""

    repository_path: str = Field(min_length=1)
    name: str | None = None


class StoredDirectory(BaseModel):
    """Stored directory metadata."""

    path: str

    model_config = ConfigDict(frozen=True)


class StoredFile(BaseModel):
    """Stored file metadata."""

    path: str
    extension: str
    language: str | None
    size_bytes: int = Field(ge=0)
    sha256: str
    modified_at: datetime

    model_config = ConfigDict(frozen=True)


class StoredRepositoryMetadata(BaseModel):
    """Stored repository metadata and discovered children."""

    repository_id: int
    name: str
    path: str
    languages: list[str]
    extensions: list[str]
    indexed_at: datetime
    directories: list[StoredDirectory]
    files: list[StoredFile]

    model_config = ConfigDict(frozen=True)
