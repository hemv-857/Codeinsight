from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ImportSourceType = Literal["github", "local", "zip"]
ImportStatus = Literal["pending", "running", "completed", "failed"]


class RepositoryImportRequest(BaseModel):
    """Request body for URL or local-path repository imports."""

    source_type: Literal["github", "local"]
    source: str = Field(min_length=1)


class ImportProgressEvent(BaseModel):
    """A single repository import progress event."""

    stage: str
    message: str
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class RepositoryImportResponse(BaseModel):
    """Repository import status returned by the API."""

    import_id: str
    source_type: ImportSourceType
    source: str
    status: ImportStatus
    repository_path: str | None
    events: list[ImportProgressEvent]

    model_config = ConfigDict(frozen=True)
