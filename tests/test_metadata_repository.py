from datetime import UTC, datetime
from pathlib import Path

from backend.app.repositories.metadata import MetadataRepository
from backend.app.schemas.repository_scan import RepositoryFileEntry, RepositoryScanResult


def create_scan(root: Path, size_bytes: int = 5) -> RepositoryScanResult:
    return RepositoryScanResult(
        repository_path=str(root),
        files=[
            RepositoryFileEntry(
                path="src/main.py",
                extension=".py",
                language="Python",
                size_bytes=size_bytes,
            )
        ],
        directories=["src"],
        extensions=[".py"],
        languages=["Python"],
    )


def test_metadata_repository_persists_scan(tmp_path: Path) -> None:
    repository = MetadataRepository(str(tmp_path / "metadata.sqlite3"))
    modified_at = datetime(2026, 1, 1, tzinfo=UTC)

    result = repository.save_scan(
        name="demo",
        scan=create_scan(tmp_path / "repo"),
        file_metadata={"src/main.py": ("abc123", modified_at)},
    )

    assert result.repository_id > 0
    assert result.name == "demo"
    assert result.path == str(tmp_path / "repo")
    assert result.languages == ["Python"]
    assert result.extensions == [".py"]
    assert result.directories[0].path == "src"
    assert result.files[0].sha256 == "abc123"
    assert result.files[0].modified_at == modified_at


def test_metadata_repository_replaces_existing_scan(tmp_path: Path) -> None:
    repository = MetadataRepository(str(tmp_path / "metadata.sqlite3"))
    root = tmp_path / "repo"
    first = repository.save_scan(
        name="demo",
        scan=create_scan(root, size_bytes=5),
        file_metadata={"src/main.py": ("first", datetime(2026, 1, 1, tzinfo=UTC))},
    )

    second = repository.save_scan(
        name="demo-renamed",
        scan=create_scan(root, size_bytes=8),
        file_metadata={"src/main.py": ("second", datetime(2026, 1, 2, tzinfo=UTC))},
    )

    assert second.repository_id == first.repository_id
    assert second.name == "demo-renamed"
    assert second.files[0].size_bytes == 8
    assert second.files[0].sha256 == "second"
