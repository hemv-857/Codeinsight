from hashlib import sha256
from pathlib import Path

from backend.app.repositories.metadata import MetadataRepository
from backend.app.services.metadata import MetadataService
from backend.app.services.repository_scanner import RepositoryScannerService


def test_metadata_service_scans_hashes_and_persists_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    source_file = repository_root / "src" / "main.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("print('hello')\n")
    service = MetadataService(
        scanner=RepositoryScannerService(),
        repository=MetadataRepository(str(tmp_path / "metadata.sqlite3")),
    )

    result = service.persist_repository(repository_root, name="demo")

    assert result.name == "demo"
    assert result.files[0].path == "src/main.py"
    assert result.files[0].sha256 == sha256(source_file.read_bytes()).hexdigest()
    assert result.files[0].language == "Python"

    stored = service.get_repository(result.repository_id)
    assert stored == result
