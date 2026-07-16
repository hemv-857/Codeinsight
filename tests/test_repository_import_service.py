import subprocess
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from backend.app.services.repository_import import RepositoryImportError, RepositoryImportService


def create_git_repository(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "forge@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Forge AI"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    (path / "README.md").write_text("# Demo\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service(storage_root: Path) -> RepositoryImportService:
    return RepositoryImportService(
        storage_root=storage_root,
        clone_timeout_seconds=30,
        max_zip_bytes=1024 * 1024,
    )


def create_zip(entries: dict[str, str]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_import_local_git_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    service = create_service(tmp_path / "imports")

    result = service.import_local(str(source))

    assert result.status == "completed"
    assert result.repository_path is not None
    assert (Path(result.repository_path) / "README.md").read_text() == "# Demo\n"
    assert [event.stage for event in result.events] == [
        "queued",
        "validating",
        "cloning",
        "completed",
    ]
    assert service.get_progress(result.import_id) == result


def test_import_zip_repository(tmp_path: Path) -> None:
    service = create_service(tmp_path / "imports")
    content = create_zip({"project/README.md": "# Demo\n"})

    result = service.import_zip("project.zip", content)

    assert result.status == "completed"
    assert result.repository_path is not None
    assert (Path(result.repository_path) / "project" / "README.md").read_text() == "# Demo\n"


def test_rejects_zip_path_traversal(tmp_path: Path) -> None:
    service = create_service(tmp_path / "imports")
    content = create_zip({"../escape.txt": "nope"})

    with pytest.raises(RepositoryImportError, match="unsafe file path"):
        service.import_zip("bad.zip", content)


def test_rejects_invalid_github_url(tmp_path: Path) -> None:
    service = create_service(tmp_path / "imports")

    with pytest.raises(RepositoryImportError, match="github.com"):
        service.import_github("https://example.com/acme/project")
