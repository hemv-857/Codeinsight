from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from backend.app.repositories.metadata import MetadataRepository
from backend.app.schemas.metadata import StoredRepositoryMetadata
from backend.app.services.repository_scanner import RepositoryScannerService


class MetadataService:
    """Coordinates repository scanning and metadata persistence."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        repository: MetadataRepository,
    ) -> None:
        self.scanner = scanner
        self.repository = repository

    def persist_repository(
        self,
        repository_path: Path,
        name: str | None = None,
    ) -> StoredRepositoryMetadata:
        scan = self.scanner.scan(repository_path)
        root = Path(scan.repository_path)
        file_metadata = {
            file.path: (self._hash_file(root / file.path), self._modified_at(root / file.path))
            for file in scan.files
        }
        repository_name = name or root.name
        return self.repository.save_scan(repository_name, scan, file_metadata)

    def get_repository(self, repository_id: int) -> StoredRepositoryMetadata:
        return self.repository.get_repository(repository_id)

    def _hash_file(self, path: Path) -> str:
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _modified_at(self, path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC)
