from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from backend.app.schemas.repository_import import (
    ImportProgressEvent,
    ImportSourceType,
    ImportStatus,
    RepositoryImportResponse,
)

logger = logging.getLogger(__name__)

REPOSITORY_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


class RepositoryImportError(Exception):
    """Raised when repository import validation or execution fails."""


@dataclass
class RepositoryImportRecord:
    """Mutable import progress tracked for the current backend process."""

    import_id: str
    source_type: ImportSourceType
    source: str
    status: ImportStatus = "pending"
    repository_path: Path | None = None
    events: list[ImportProgressEvent] = field(default_factory=list)

    def as_response(self) -> RepositoryImportResponse:
        return RepositoryImportResponse(
            import_id=self.import_id,
            source_type=self.source_type,
            source=self.source,
            status=self.status,
            repository_path=str(self.repository_path) if self.repository_path else None,
            events=self.events,
        )


class RepositoryImportService:
    """Imports GitHub, local, and ZIP repositories into a managed workspace."""

    def __init__(self, storage_root: Path, clone_timeout_seconds: int, max_zip_bytes: int) -> None:
        self.storage_root = storage_root
        self.clone_timeout_seconds = clone_timeout_seconds
        self.max_zip_bytes = max_zip_bytes
        self._records: dict[str, RepositoryImportRecord] = {}
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def import_github(self, source: str) -> RepositoryImportResponse:
        clone_url = self._validate_github_url(source)
        return self._clone_repository(
            source_type="github",
            source=clone_url,
            clone_source=clone_url,
            name_hint=Path(urlparse(clone_url).path).stem,
        )

    def import_local(self, source: str) -> RepositoryImportResponse:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_dir():
            raise RepositoryImportError(
                "Local repository path does not exist or is not a directory."
            )

        self._run_git(["git", "-C", str(source_path), "rev-parse", "--is-inside-work-tree"])
        return self._clone_repository(
            source_type="local",
            source=str(source_path),
            clone_source=str(source_path),
            name_hint=source_path.name,
        )

    def import_zip(self, filename: str, content: bytes) -> RepositoryImportResponse:
        if not filename.lower().endswith(".zip"):
            raise RepositoryImportError("Uploaded repository must be a .zip archive.")
        if len(content) > self.max_zip_bytes:
            raise RepositoryImportError("Uploaded ZIP archive exceeds the configured size limit.")

        record = self._create_record(
            source_type="zip", source=filename, name_hint=Path(filename).stem
        )
        destination = self._destination_for(record)
        self._add_event(record, "validating", "Validating ZIP archive.")

        try:
            self._add_event(record, "extracting", "Extracting ZIP archive.")
            self._extract_zip(content, destination)
            record.repository_path = destination
            record.status = "completed"
            self._add_event(record, "completed", "Repository ZIP import completed.")
            return record.as_response()
        except Exception as error:
            self._fail_import(record, destination, error)
            raise

    def get_progress(self, import_id: str) -> RepositoryImportResponse:
        record = self._records.get(import_id)
        if record is None:
            raise RepositoryImportError("Repository import was not found.")
        return record.as_response()

    def _clone_repository(
        self,
        source_type: ImportSourceType,
        source: str,
        clone_source: str,
        name_hint: str,
    ) -> RepositoryImportResponse:
        record = self._create_record(source_type=source_type, source=source, name_hint=name_hint)
        destination = self._destination_for(record)
        self._add_event(record, "validating", "Repository source validated.")

        try:
            self._add_event(record, "cloning", "Cloning repository.")
            self._run_git(["git", "clone", "--", clone_source, str(destination)])
            record.repository_path = destination
            record.status = "completed"
            self._add_event(record, "completed", "Repository clone completed.")
            return record.as_response()
        except Exception as error:
            self._fail_import(record, destination, error)
            raise

    def _create_record(
        self,
        source_type: ImportSourceType,
        source: str,
        name_hint: str,
    ) -> RepositoryImportRecord:
        import_id = uuid4().hex
        record = RepositoryImportRecord(
            import_id=import_id,
            source_type=source_type,
            source=source,
        )
        self._records[import_id] = record
        self._add_event(record, "queued", "Repository import queued.")
        record.repository_path = self._destination_for(record, name_hint)
        record.status = "running"
        return record

    def _destination_for(
        self,
        record: RepositoryImportRecord,
        name_hint: str | None = None,
    ) -> Path:
        if record.repository_path is not None:
            return record.repository_path

        clean_name = self._clean_repository_name(name_hint or record.source)
        return self.storage_root / f"{clean_name}-{record.import_id[:12]}"

    def _add_event(self, record: RepositoryImportRecord, stage: str, message: str) -> None:
        record.events.append(
            ImportProgressEvent(stage=stage, message=message, created_at=datetime.now(UTC))
        )

    def _fail_import(
        self,
        record: RepositoryImportRecord,
        destination: Path,
        error: Exception,
    ) -> None:
        record.status = "failed"
        self._add_event(record, "failed", str(error))
        if destination.exists():
            shutil.rmtree(destination)
        logger.warning("Repository import failed", exc_info=error)

    def _run_git(self, command: list[str]) -> None:
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.clone_timeout_seconds,
            )
        except FileNotFoundError as error:
            raise RepositoryImportError("Git is not installed or is unavailable.") from error
        except subprocess.TimeoutExpired as error:
            raise RepositoryImportError("Git operation timed out.") from error
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or error.stdout.strip() or "Git operation failed."
            raise RepositoryImportError(message) from error

    def _extract_zip(self, content: bytes, destination: Path) -> None:
        with TemporaryDirectory() as temporary_directory:
            zip_path = Path(temporary_directory) / "repository.zip"
            zip_path.write_bytes(content)

            try:
                with ZipFile(zip_path) as archive:
                    self._validate_zip_members(archive)
                    destination.mkdir(parents=True, exist_ok=False)
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        target = destination / member.filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(member) as source_file, target.open("wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
            except BadZipFile as error:
                raise RepositoryImportError("Uploaded file is not a valid ZIP archive.") from error

    def _validate_zip_members(self, archive: ZipFile) -> None:
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RepositoryImportError("ZIP archive contains an unsafe file path.")

    def _validate_github_url(self, source: str) -> str:
        parsed = urlparse(source)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise RepositoryImportError("GitHub repository URL must use https://github.com.")

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 2:
            raise RepositoryImportError("GitHub repository URL must include owner and repository.")

        owner, repo = parts
        if not owner or not repo:
            raise RepositoryImportError("GitHub repository URL must include owner and repository.")

        repository_name = repo.removesuffix(".git")
        if not repository_name:
            raise RepositoryImportError("GitHub repository name is invalid.")

        return f"https://github.com/{owner}/{repository_name}.git"

    def _clean_repository_name(self, value: str) -> str:
        name = REPOSITORY_NAME_PATTERN.sub("-", Path(value).stem).strip(".-")
        return name or "repository"
