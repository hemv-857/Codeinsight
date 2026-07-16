import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from graph.call_graph import CallGraph, CallGraphError, CallGraphService, CallGraphStats
from graph.dependency_graph import (
    DependencyGraph,
    DependencyGraphError,
    DependencyGraphService,
    DependencyGraphStats,
)
from parser.tree_sitter_parser import (
    ParseTreeSummary,
    TreeSitterParseError,
    TreeSitterParserService,
)

from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.schemas.repository_scan import RepositoryFileEntry, RepositoryScanResult
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService

DEFAULT_KEY_ITEM_LIMIT = 8

logger = logging.getLogger(__name__)


class RepositorySummaryError(Exception):
    """Raised when repository summarization cannot continue."""


@dataclass(frozen=True)
class SummaryLanguage:
    """Language usage in a repository."""

    language: str
    file_count: int
    size_bytes: int


@dataclass(frozen=True)
class SummaryFile:
    """A key repository file surfaced by summarization."""

    path: str
    language: str | None
    size_bytes: int
    symbol_count: int
    dependency_count: int
    dependent_count: int


@dataclass(frozen=True)
class SummarySymbol:
    """A key source symbol surfaced by summarization."""

    name: str
    kind: str
    path: str
    line: int
    parent: str | None = None


@dataclass(frozen=True)
class RepositorySummaryStats:
    """Summary metrics for a repository."""

    file_count: int
    directory_count: int
    language_count: int
    parsed_file_count: int
    skipped_parse_file_count: int
    symbol_count: int
    dependency_count: int
    callable_count: int
    call_count: int
    indexed_embedding_count: int


@dataclass(frozen=True)
class RepositorySummary:
    """Repository-level summary assembled from indexed code intelligence."""

    repository_path: str
    overview: str
    languages: tuple[SummaryLanguage, ...]
    key_files: tuple[SummaryFile, ...]
    key_symbols: tuple[SummarySymbol, ...]
    dependency_highlights: tuple[str, ...]
    call_highlights: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    embedding_indexed: bool
    stats: RepositorySummaryStats


class RepositorySummaryService:
    """Builds a grounded repository summary from scanner, parser, graph, and vector data."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
        dependency_graph: DependencyGraphService,
        call_graph: CallGraphService,
        vector_repository: VectorStoreRepository,
    ) -> None:
        self.scanner = scanner
        self.parser = parser
        self.dependency_graph = dependency_graph
        self.call_graph = call_graph
        self.vector_repository = vector_repository

    def summarize(self, repository_path: Path) -> RepositorySummary:
        root = repository_path.expanduser().resolve()
        scan = self.scanner.scan(root)
        parsed_files = self._parse_supported_files(root, scan)
        dependency_graph = self._dependency_graph(root)
        call_graph = self._call_graph(root)
        indexed_embeddings = self.vector_repository.list_repository(str(root))

        symbol_count_by_path = Counter(
            path
            for path, parsed in parsed_files
            for symbol in parsed.symbols
            if symbol.kind != "import"
        )
        dependencies_by_path = Counter(
            edge.source for edge in dependency_graph.edges if edge.target is not None
        )
        dependents_by_path = Counter(
            edge.target for edge in dependency_graph.edges if edge.target is not None
        )
        key_files = self._key_files(
            files=scan.files,
            symbol_count_by_path=symbol_count_by_path,
            dependencies_by_path=dependencies_by_path,
            dependents_by_path=dependents_by_path,
        )
        key_symbols = self._key_symbols(parsed_files)
        languages = self._languages(scan.files)
        evidence_paths = tuple(
            dict.fromkeys(
                [file.path for file in key_files]
                + [symbol.path for symbol in key_symbols]
                + [edge.source for edge in dependency_graph.edges[:DEFAULT_KEY_ITEM_LIMIT]]
            )
        )[:DEFAULT_KEY_ITEM_LIMIT]
        stats = RepositorySummaryStats(
            file_count=len(scan.files),
            directory_count=len(scan.directories),
            language_count=len(scan.languages),
            parsed_file_count=len(parsed_files),
            skipped_parse_file_count=len(
                [
                    file
                    for file in scan.files
                    if file.language is not None and self.parser.supports_path(Path(file.path))
                ]
            )
            - len(parsed_files),
            symbol_count=sum(len(parsed.symbols) for _, parsed in parsed_files),
            dependency_count=dependency_graph.stats.internal_dependency_count,
            callable_count=call_graph.stats.callable_count,
            call_count=call_graph.stats.call_count,
            indexed_embedding_count=len(indexed_embeddings),
        )
        return RepositorySummary(
            repository_path=str(root),
            overview=self._overview(scan, languages, stats),
            languages=languages,
            key_files=key_files,
            key_symbols=key_symbols,
            dependency_highlights=self._dependency_highlights(dependency_graph),
            call_highlights=self._call_highlights(call_graph),
            evidence_paths=evidence_paths,
            embedding_indexed=bool(indexed_embeddings),
            stats=stats,
        )

    def _parse_supported_files(
        self,
        root: Path,
        scan: RepositoryScanResult,
    ) -> tuple[tuple[str, ParseTreeSummary], ...]:
        parsed_files: list[tuple[str, ParseTreeSummary]] = []
        for file in scan.files:
            relative_path = Path(file.path)
            if file.language is None or not self.parser.supports_path(relative_path):
                continue
            try:
                parsed_files.append((file.path, self.parser.parse_file(root / relative_path)))
            except TreeSitterParseError as error:
                logger.warning("Skipping unparsable source file %s: %s", file.path, error)
        return tuple(parsed_files)

    def _dependency_graph(self, root: Path) -> DependencyGraph:
        try:
            return self.dependency_graph.build(root)
        except (RepositoryScanError, DependencyGraphError, TreeSitterParseError) as error:
            logger.warning("Dependency graph unavailable for summary: %s", error)
            return DependencyGraph(
                repository_path=str(root),
                nodes=(),
                edges=(),
                external_dependencies=(),
                unresolved_imports=(),
                circular_dependencies=(),
                stats=DependencyGraphStats(
                    file_count=0,
                    internal_dependency_count=0,
                    external_dependency_count=0,
                    unresolved_dependency_count=0,
                    circular_dependency_count=0,
                ),
            )

    def _call_graph(self, root: Path) -> CallGraph:
        try:
            return self.call_graph.build(root)
        except (RepositoryScanError, CallGraphError, TreeSitterParseError) as error:
            logger.warning("Call graph unavailable for summary: %s", error)
            return CallGraph(
                repository_path=str(root),
                nodes=(),
                edges=(),
                unresolved_calls=(),
                stats=CallGraphStats(
                    callable_count=0,
                    call_count=0,
                    resolved_call_count=0,
                    unresolved_call_count=0,
                    recursive_call_count=0,
                ),
            )

    def _languages(self, files: list[RepositoryFileEntry]) -> tuple[SummaryLanguage, ...]:
        file_count_by_language: Counter[str] = Counter()
        size_by_language: Counter[str] = Counter()
        for file in files:
            if file.language is None:
                continue
            file_count_by_language[file.language] += 1
            size_by_language[file.language] += file.size_bytes
        return tuple(
            SummaryLanguage(
                language=language,
                file_count=file_count,
                size_bytes=size_by_language[language],
            )
            for language, file_count in file_count_by_language.most_common()
        )

    def _key_files(
        self,
        files: list[RepositoryFileEntry],
        symbol_count_by_path: Counter[str],
        dependencies_by_path: Counter[str],
        dependents_by_path: Counter[str],
    ) -> tuple[SummaryFile, ...]:
        source_files = [file for file in files if file.language is not None]
        ranked = sorted(
            source_files,
            key=lambda file: (
                -(
                    symbol_count_by_path[file.path]
                    + dependencies_by_path[file.path]
                    + dependents_by_path[file.path]
                ),
                file.path,
            ),
        )
        return tuple(
            SummaryFile(
                path=file.path,
                language=file.language,
                size_bytes=file.size_bytes,
                symbol_count=symbol_count_by_path[file.path],
                dependency_count=dependencies_by_path[file.path],
                dependent_count=dependents_by_path[file.path],
            )
            for file in ranked[:DEFAULT_KEY_ITEM_LIMIT]
        )

    def _key_symbols(
        self,
        parsed_files: tuple[tuple[str, ParseTreeSummary], ...],
    ) -> tuple[SummarySymbol, ...]:
        symbols = [
            SummarySymbol(
                name=symbol.name,
                kind=symbol.kind,
                path=path,
                line=symbol.line,
                parent=symbol.parent,
            )
            for path, parsed in parsed_files
            for symbol in parsed.symbols
            if symbol.kind != "import"
        ]
        return tuple(
            sorted(
                symbols,
                key=lambda symbol: (
                    symbol.kind not in {"class", "interface"},
                    symbol.path,
                    symbol.line,
                    symbol.name,
                ),
            )[:DEFAULT_KEY_ITEM_LIMIT]
        )

    def _dependency_highlights(self, graph: DependencyGraph) -> tuple[str, ...]:
        highlights: list[str] = []
        if graph.stats.internal_dependency_count:
            highlights.append(
                f"{graph.stats.internal_dependency_count} internal file dependencies found."
            )
        if graph.stats.external_dependency_count:
            highlights.append(
                f"{graph.stats.external_dependency_count} external dependencies referenced."
            )
        if graph.stats.circular_dependency_count:
            highlights.append(
                f"{graph.stats.circular_dependency_count} circular dependency cycles detected."
            )
        return tuple(highlights[:DEFAULT_KEY_ITEM_LIMIT])

    def _call_highlights(self, graph: CallGraph) -> tuple[str, ...]:
        highlights: list[str] = []
        if graph.stats.callable_count:
            highlights.append(f"{graph.stats.callable_count} callable symbols found.")
        if graph.stats.call_count:
            highlights.append(f"{graph.stats.call_count} call sites found.")
        if graph.stats.recursive_call_count:
            highlights.append(f"{graph.stats.recursive_call_count} recursive calls detected.")
        return tuple(highlights[:DEFAULT_KEY_ITEM_LIMIT])

    def _overview(
        self,
        scan: RepositoryScanResult,
        languages: tuple[SummaryLanguage, ...],
        stats: RepositorySummaryStats,
    ) -> str:
        primary_language = languages[0].language if languages else "unknown language"
        return (
            f"This repository contains {stats.file_count} files across "
            f"{stats.directory_count} directories. The primary language is "
            f"{primary_language}, with {stats.symbol_count} parsed symbols, "
            f"{stats.dependency_count} internal dependencies, and "
            f"{stats.call_count} call sites."
        )
