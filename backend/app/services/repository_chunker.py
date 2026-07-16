import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from parser.tree_sitter_parser import SourceSymbol, TreeSitterParseError, TreeSitterParserService

from backend.app.services.repository_scanner import RepositoryScannerService

DEFAULT_CHUNK_MAX_CHARS = 12_000
CHUNKED_SYMBOL_KINDS = frozenset({"class", "function", "interface", "method"})

logger = logging.getLogger(__name__)


class RepositoryChunkError(Exception):
    """Raised when repository chunking cannot continue."""


@dataclass(frozen=True)
class SkippedChunkFile:
    """A source file skipped during chunk generation."""

    path: str
    reason: str


@dataclass(frozen=True)
class RepositoryChunk:
    """A text chunk ready for later embedding generation."""

    id: str
    kind: Literal["file", "symbol"]
    path: str
    language: str
    content: str
    start_line: int
    end_line: int
    char_count: int
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None


@dataclass(frozen=True)
class RepositoryChunkStats:
    """Summary counts for a repository chunking run."""

    source_file_count: int
    chunk_count: int
    file_chunk_count: int
    symbol_chunk_count: int
    skipped_file_count: int


@dataclass(frozen=True)
class RepositoryChunks:
    """Chunks generated for one repository."""

    repository_path: str
    chunks: tuple[RepositoryChunk, ...]
    skipped_files: tuple[SkippedChunkFile, ...]
    stats: RepositoryChunkStats


class RepositoryChunkerService:
    """Builds deterministic repository text chunks for embedding generation."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
        max_chunk_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    ) -> None:
        if max_chunk_chars <= 0:
            raise ValueError("max_chunk_chars must be positive.")
        self.scanner = scanner
        self.parser = parser
        self.max_chunk_chars = max_chunk_chars

    def chunk_repository(self, repository_path: Path) -> RepositoryChunks:
        root = repository_path.expanduser().resolve()
        scan = self.scanner.scan(root)
        chunks: list[RepositoryChunk] = []
        skipped_files: list[SkippedChunkFile] = []
        source_file_count = 0

        for file in scan.files:
            if file.language is None:
                continue
            source_file_count += 1
            path = root / file.path
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                logger.warning("Skipping non-UTF-8 source file during chunking: %s", file.path)
                skipped_files.append(SkippedChunkFile(path=file.path, reason="non_utf8"))
                continue
            except OSError as error:
                raise RepositoryChunkError(str(error)) from error

            chunks.extend(self._file_chunks(file.path, file.language, content))
            if self.parser.supports_path(Path(file.path)):
                chunks.extend(self._symbol_chunks(root, file.path, file.language, content))

        file_chunk_count = sum(1 for chunk in chunks if chunk.kind == "file")
        symbol_chunk_count = len(chunks) - file_chunk_count
        return RepositoryChunks(
            repository_path=str(root),
            chunks=tuple(chunks),
            skipped_files=tuple(skipped_files),
            stats=RepositoryChunkStats(
                source_file_count=source_file_count,
                chunk_count=len(chunks),
                file_chunk_count=file_chunk_count,
                symbol_chunk_count=symbol_chunk_count,
                skipped_file_count=len(skipped_files),
            ),
        )

    def _file_chunks(self, path: str, language: str, content: str) -> list[RepositoryChunk]:
        lines = content.splitlines(keepends=True)
        if not lines:
            return []

        chunks: list[RepositoryChunk] = []
        current: list[str] = []
        start_line = 1
        current_chars = 0

        for line_number, line in enumerate(lines, start=1):
            if current and current_chars + len(line) > self.max_chunk_chars:
                chunks.append(
                    self._chunk(
                        kind="file",
                        path=path,
                        language=language,
                        content="".join(current),
                        start_line=start_line,
                        end_line=line_number - 1,
                    )
                )
                current = []
                current_chars = 0
                start_line = line_number
            current.append(line)
            current_chars += len(line)

        if current:
            chunks.append(
                self._chunk(
                    kind="file",
                    path=path,
                    language=language,
                    content="".join(current),
                    start_line=start_line,
                    end_line=start_line + len(current) - 1,
                )
            )
        return chunks

    def _symbol_chunks(
        self,
        root: Path,
        path: str,
        language: str,
        content: str,
    ) -> list[RepositoryChunk]:
        try:
            parsed = self.parser.parse_file(root / path)
        except TreeSitterParseError as error:
            raise RepositoryChunkError(str(error)) from error

        lines = content.splitlines(keepends=True)
        chunks: list[RepositoryChunk] = []
        for symbol in parsed.symbols:
            if symbol.kind not in CHUNKED_SYMBOL_KINDS:
                continue
            source = self._symbol_source(lines, symbol)
            if not source.strip():
                continue
            chunks.append(
                self._chunk(
                    kind="symbol",
                    path=path,
                    language=language,
                    content=source,
                    start_line=symbol.line,
                    end_line=symbol.end_line,
                    symbol=symbol,
                )
            )
        return chunks

    def _symbol_source(self, lines: list[str], symbol: SourceSymbol) -> str:
        start = max(symbol.line - 1, 0)
        end = min(symbol.end_line, len(lines))
        return "".join(lines[start:end])

    def _chunk(
        self,
        *,
        kind: Literal["file", "symbol"],
        path: str,
        language: str,
        content: str,
        start_line: int,
        end_line: int,
        symbol: SourceSymbol | None = None,
    ) -> RepositoryChunk:
        symbol_name = symbol.name if symbol else None
        symbol_kind = symbol.kind if symbol else None
        symbol_parent = symbol.parent if symbol else None
        return RepositoryChunk(
            id=self._chunk_id(kind, path, start_line, end_line, symbol_kind, symbol_name),
            kind=kind,
            path=path,
            language=language,
            content=content,
            start_line=start_line,
            end_line=end_line,
            char_count=len(content),
            symbol_kind=symbol_kind,
            symbol_name=symbol_name,
            symbol_parent=symbol_parent,
        )

    def _chunk_id(
        self,
        kind: str,
        path: str,
        start_line: int,
        end_line: int,
        symbol_kind: str | None,
        symbol_name: str | None,
    ) -> str:
        source = ":".join(
            (kind, path, str(start_line), str(end_line), symbol_kind or "", symbol_name or "")
        )
        digest = hashlib.sha256(source.encode()).hexdigest()[:16]
        return f"{kind}:{path}:{start_line}:{end_line}:{digest}"
