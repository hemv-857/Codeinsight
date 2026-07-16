from pathlib import Path

from backend.app.schemas.repository_scan import RepositoryFileEntry, RepositoryScanResult

IGNORED_DIRECTORIES = frozenset({".git", "node_modules", "venv", "target", "dist"})

LANGUAGE_BY_EXTENSION = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".go": "Go",
    ".h": "C",
    ".hpp": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".py": "Python",
    ".rs": "Rust",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}


class RepositoryScanError(Exception):
    """Raised when repository scanning cannot continue."""


class RepositoryScannerService:
    """Recursively scans repository files and directories."""

    def scan(self, repository_path: Path) -> RepositoryScanResult:
        root = repository_path.expanduser().resolve()
        if not root.is_dir():
            raise RepositoryScanError("Repository path does not exist or is not a directory.")

        files: list[RepositoryFileEntry] = []
        directories: set[str] = set()
        extensions: set[str] = set()
        languages: set[str] = set()

        for current_root, directory_names, filenames in root.walk(top_down=True):
            directory_names[:] = sorted(
                name
                for name in directory_names
                if name not in IGNORED_DIRECTORIES and not (current_root / name).is_symlink()
            )

            if current_root != root:
                directories.add(current_root.relative_to(root).as_posix())

            for filename in sorted(filenames):
                file_path = current_root / filename
                if file_path.is_symlink() or not file_path.is_file():
                    continue

                relative_path = file_path.relative_to(root).as_posix()
                extension = file_path.suffix.lower()
                language = LANGUAGE_BY_EXTENSION.get(extension)
                if extension:
                    extensions.add(extension)
                if language is not None:
                    languages.add(language)

                files.append(
                    RepositoryFileEntry(
                        path=relative_path,
                        extension=extension,
                        language=language,
                        size_bytes=file_path.stat().st_size,
                    )
                )

        return RepositoryScanResult(
            repository_path=str(root),
            files=files,
            directories=sorted(directories),
            extensions=sorted(extensions),
            languages=sorted(languages),
        )
