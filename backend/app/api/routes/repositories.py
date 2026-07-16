from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.app.core.dependencies import (
    get_repository_import_service,
    get_repository_scanner_service,
)
from backend.app.schemas.repository_import import RepositoryImportRequest, RepositoryImportResponse
from backend.app.schemas.repository_scan import RepositoryScanRequest, RepositoryScanResult
from backend.app.services.repository_import import RepositoryImportError, RepositoryImportService
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.post(
    "/import", response_model=RepositoryImportResponse, status_code=status.HTTP_201_CREATED
)
def import_repository(
    request: RepositoryImportRequest,
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Import a GitHub or local Git repository."""
    try:
        if request.source_type == "github":
            return service.import_github(request.source)
        return service.import_local(request.source)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/import/zip",
    response_model=RepositoryImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_repository_zip(
    file: Annotated[UploadFile, File()],
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Import a repository from an uploaded ZIP archive."""
    try:
        content = await file.read(service.max_zip_bytes + 1)
        return service.import_zip(file.filename or "repository.zip", content)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}", response_model=RepositoryImportResponse)
def get_repository_import(
    import_id: str,
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Return progress for a repository import."""
    try:
        return service.get_progress(import_id)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/scan", response_model=RepositoryScanResult)
def scan_repository(
    request: RepositoryScanRequest,
    service: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
) -> RepositoryScanResult:
    """Recursively scan a repository path."""
    try:
        return service.scan(request.repository_path)
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/scan", response_model=RepositoryScanResult)
def scan_imported_repository(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    scanner_service: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
) -> RepositoryScanResult:
    """Recursively scan a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositoryScanError("Repository import has no local path to scan.")
        return scanner_service.scan(Path(imported_repository.repository_path))
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
