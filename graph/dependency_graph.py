from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from posixpath import normpath

from backend.app.services.repository_scanner import RepositoryScannerService
from parser.tree_sitter_parser import (
    ParseTreeSummary,
    SourceSymbol,
    TreeSitterParseError,
    TreeSitterParserService,
)

SOURCE_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".cxx",
    ".hh",
    ".hpp",
    ".hxx",
    ".java",
    ".go",
    ".rs",
)

INDEX_FILES = ("__init__", "index", "mod")


class DependencyGraphError(Exception):
    """Raised when dependency graph construction cannot continue."""


@dataclass(frozen=True)
class DependencyNode:
    """A source file in a repository dependency graph."""

    path: str
    language: str


@dataclass(frozen=True)
class DependencyEdge:
    """A dependency relationship from one source file to another import target."""

    source: str
    target: str | None
    import_name: str
    import_source: str | None
    dependency_type: str


@dataclass(frozen=True)
class DependencyGraphStats:
    """Summary counts for a repository dependency graph."""

    file_count: int
    internal_dependency_count: int
    external_dependency_count: int
    unresolved_dependency_count: int
    circular_dependency_count: int


@dataclass(frozen=True)
class DependencyGraph:
    """File-level dependency graph for a repository."""

    repository_path: str
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]
    external_dependencies: tuple[str, ...]
    unresolved_imports: tuple[str, ...]
    circular_dependencies: tuple[tuple[str, ...], ...]
    stats: DependencyGraphStats


class DependencyGraphService:
    """Builds a file-level dependency graph from parsed repository imports."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
    ) -> None:
        self.scanner = scanner
        self.parser = parser

    def build(self, repository_path: Path) -> DependencyGraph:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            parsed_files = [
                (file.path, self.parser.parse_file(root / file.path))
                for file in scan.files
                if file.language is not None and self.parser.supports_path(Path(file.path))
            ]
        except TreeSitterParseError as error:
            raise DependencyGraphError(str(error)) from error

        language_by_path = {path: parsed.language for path, parsed in parsed_files}
        file_paths = tuple(language_by_path)
        nodes = tuple(
            DependencyNode(path=path, language=language_by_path[path]) for path in file_paths
        )
        edges = tuple(self._edges_for_files(file_paths, parsed_files))
        cycles = self._cycles(file_paths, edges)
        external_dependencies = tuple(
            sorted({edge.import_name for edge in edges if edge.dependency_type == "external"})
        )
        unresolved_imports = tuple(
            sorted({edge.import_name for edge in edges if edge.target is None})
        )
        return DependencyGraph(
            repository_path=str(root),
            nodes=nodes,
            edges=edges,
            external_dependencies=external_dependencies,
            unresolved_imports=unresolved_imports,
            circular_dependencies=cycles,
            stats=DependencyGraphStats(
                file_count=len(nodes),
                internal_dependency_count=sum(1 for edge in edges if edge.target is not None),
                external_dependency_count=sum(
                    1 for edge in edges if edge.dependency_type == "external"
                ),
                unresolved_dependency_count=sum(1 for edge in edges if edge.target is None),
                circular_dependency_count=len(cycles),
            ),
        )

    def _edges_for_files(
        self,
        file_paths: tuple[str, ...],
        parsed_files: list[tuple[str, ParseTreeSummary]],
    ) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        file_set = set(file_paths)
        for source_path, parsed in parsed_files:
            imports = [symbol for symbol in parsed.symbols if symbol.kind == "import"]
            for symbol in imports:
                target = self._resolve_import(source_path, symbol, file_set)
                edges.append(
                    DependencyEdge(
                        source=source_path,
                        target=target,
                        import_name=symbol.name,
                        import_source=symbol.source,
                        dependency_type="internal" if target is not None else "external",
                    )
                )
        return edges

    def _resolve_import(
        self,
        source_path: str,
        symbol: SourceSymbol,
        file_set: set[str],
    ) -> str | None:
        raw_import = symbol.source or symbol.name
        normalized_import = self._normalize_import(raw_import)
        if normalized_import is None:
            return None

        source_dir = PurePosixPath(source_path).parent
        for candidate in self._candidate_paths(normalized_import, source_dir):
            if candidate in file_set:
                return candidate
        return None

    def _candidate_paths(self, import_name: str, source_dir: PurePosixPath) -> list[str]:
        candidates: list[str] = []
        import_path = import_name.replace("::", "/").replace(".", "/")
        if import_name.startswith("."):
            import_path = (source_dir / import_name).as_posix()
        elif "/" not in import_path:
            candidates.append((source_dir / import_path).as_posix())

        candidates.append(import_path)
        if PurePosixPath(import_path).suffix:
            return self._dedupe(candidates)

        for extension in SOURCE_EXTENSIONS:
            candidates.append(f"{import_path}{extension}")
        for index_file in INDEX_FILES:
            for extension in SOURCE_EXTENSIONS:
                candidates.append(f"{import_path}/{index_file}{extension}")
        return self._dedupe(candidates)

    def _normalize_import(self, raw_import: str | None) -> str | None:
        if raw_import is None:
            return None
        cleaned = raw_import.strip().strip("\"'<>")
        return cleaned or None

    def _cycles(
        self,
        file_paths: tuple[str, ...],
        edges: tuple[DependencyEdge, ...],
    ) -> tuple[tuple[str, ...], ...]:
        adjacency: dict[str, list[str]] = {path: [] for path in file_paths}
        for edge in edges:
            if edge.target is not None:
                adjacency[edge.source].append(edge.target)

        seen: set[tuple[str, ...]] = set()
        for start in file_paths:
            self._find_cycles(start, start, adjacency, [start], seen)
        return tuple(sorted(seen))

    def _find_cycles(
        self,
        start: str,
        current: str,
        adjacency: dict[str, list[str]],
        path: list[str],
        seen: set[tuple[str, ...]],
    ) -> None:
        for next_path in adjacency[current]:
            if next_path == start and len(path) > 1:
                seen.add(self._canonical_cycle(path))
                continue
            if next_path not in path:
                self._find_cycles(start, next_path, adjacency, [*path, next_path], seen)

    def _canonical_cycle(self, cycle: list[str]) -> tuple[str, ...]:
        rotations = [tuple(cycle[index:] + cycle[:index]) for index in range(len(cycle))]
        return min(rotations)

    def _dedupe(self, values: list[str]) -> list[str]:
        return list(dict.fromkeys(normpath(value).removeprefix("./") for value in values))
