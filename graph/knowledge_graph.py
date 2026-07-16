import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from backend.app.services.repository_scanner import RepositoryScannerService
from parser.tree_sitter_parser import (
    ParseTreeSummary,
    TreeSitterParseError,
    TreeSitterParserService,
)

from graph.call_graph import CallGraphEdge, CallGraphError, CallGraphService
from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService

GraphProperty = str | int | bool
logger = logging.getLogger(__name__)


class KnowledgeGraphError(Exception):
    """Raised when knowledge graph construction or persistence fails."""


@dataclass(frozen=True)
class KnowledgeGraphNode:
    """A node in the repository knowledge graph."""

    id: str
    labels: tuple[str, ...]
    properties: dict[str, GraphProperty]


@dataclass(frozen=True)
class KnowledgeGraphEdge:
    """A typed relationship in the repository knowledge graph."""

    source: str
    target: str
    relationship: str
    properties: dict[str, GraphProperty]


@dataclass(frozen=True)
class KnowledgeGraphStats:
    """Summary counts for a repository knowledge graph."""

    node_count: int
    edge_count: int
    file_count: int
    symbol_count: int
    dependency_edge_count: int
    call_edge_count: int


@dataclass(frozen=True)
class KnowledgeGraph:
    """Repository-level architecture knowledge graph."""

    repository_path: str
    nodes: tuple[KnowledgeGraphNode, ...]
    edges: tuple[KnowledgeGraphEdge, ...]
    stats: KnowledgeGraphStats


@dataclass(frozen=True)
class KnowledgeGraphPersistenceResult:
    """Result of writing a knowledge graph to a graph backend."""

    persisted: bool
    node_count: int
    edge_count: int
    backend: str = "unknown"
    durable_backend: str | None = None


class KnowledgeGraphRepository:
    """Persists knowledge graphs."""

    def replace(self, graph: KnowledgeGraph) -> KnowledgeGraphPersistenceResult:
        """Replace an existing repository graph with a new graph."""
        raise NotImplementedError


class KnowledgeGraphService:
    """Builds and persists repository architecture knowledge graphs."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
        dependency_graph: DependencyGraphService,
        call_graph: CallGraphService,
        repository: KnowledgeGraphRepository,
    ) -> None:
        self.scanner = scanner
        self.parser = parser
        self.dependency_graph = dependency_graph
        self.call_graph = call_graph
        self.repository = repository

    def build(self, repository_path: Path) -> KnowledgeGraph:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            parsed_files = [
                (file.path, self.parser.parse_file(root / file.path))
                for file in scan.files
                if file.language is not None and self.parser.supports_path(Path(file.path))
            ]
            dependency_graph = self.dependency_graph.build(root)
            call_graph = self.call_graph.build(root)
        except (CallGraphError, DependencyGraphError, TreeSitterParseError) as error:
            raise KnowledgeGraphError(str(error)) from error

        nodes: dict[str, KnowledgeGraphNode] = {}
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge] = {}
        repository_id = self._node_id("repository", str(root))
        self._add_node(
            nodes,
            repository_id,
            ("Repository",),
            {"path": str(root), "name": root.name, "repository_path": str(root)},
        )
        self._add_directories(scan.directories, repository_id, str(root), nodes, edges)
        symbol_ids = self._add_files_and_symbols(
            parsed_files,
            repository_id,
            str(root),
            nodes,
            edges,
        )
        self._add_dependency_edges(dependency_graph.edges, str(root), nodes, edges)
        self._add_call_edges(call_graph.edges, str(root), symbol_ids, nodes, edges)

        graph_edges = tuple(edges.values())
        graph_nodes = tuple(nodes.values())
        return KnowledgeGraph(
            repository_path=str(root),
            nodes=graph_nodes,
            edges=graph_edges,
            stats=KnowledgeGraphStats(
                node_count=len(graph_nodes),
                edge_count=len(graph_edges),
                file_count=sum(1 for node in graph_nodes if "File" in node.labels),
                symbol_count=sum(1 for node in graph_nodes if "Symbol" in node.labels),
                dependency_edge_count=sum(
                    1 for edge in graph_edges if edge.relationship == "IMPORTS"
                ),
                call_edge_count=sum(1 for edge in graph_edges if edge.relationship == "CALLS"),
            ),
        )

    def build_and_persist(
        self, repository_path: Path
    ) -> tuple[KnowledgeGraph, KnowledgeGraphPersistenceResult]:
        graph = self.build(repository_path)
        try:
            persistence = self.repository.replace(graph)
        except Exception as error:
            logger.exception("Knowledge graph persistence failed.")
            raise KnowledgeGraphError(str(error)) from error
        return graph, persistence

    def _add_directories(
        self,
        directories: list[str],
        repository_id: str,
        repository_path: str,
        nodes: dict[str, KnowledgeGraphNode],
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge],
    ) -> None:
        for directory in directories:
            directory_id = self._directory_id(directory)
            self._add_node(
                nodes,
                directory_id,
                ("Directory",),
                {
                    "path": directory,
                    "name": PurePosixPath(directory).name,
                    "repository_path": repository_path,
                },
            )
            parent = PurePosixPath(directory).parent.as_posix()
            parent_id = repository_id if parent == "." else self._directory_id(parent)
            self._add_edge(
                edges,
                parent_id,
                directory_id,
                "CONTAINS",
                {"repository_path": repository_path},
            )

    def _add_files_and_symbols(
        self,
        parsed_files: list[tuple[str, ParseTreeSummary]],
        repository_id: str,
        repository_path: str,
        nodes: dict[str, KnowledgeGraphNode],
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge],
    ) -> dict[str, str]:
        symbol_ids: dict[str, str] = {}
        for path, parsed in parsed_files:
            file_id = self._file_id(path)
            self._add_node(
                nodes,
                file_id,
                ("File",),
                {
                    "path": path,
                    "name": PurePosixPath(path).name,
                    "language": parsed.language,
                    "repository_path": repository_path,
                },
            )
            parent = PurePosixPath(path).parent.as_posix()
            parent_id = repository_id if parent == "." else self._directory_id(parent)
            self._add_edge(
                edges,
                parent_id,
                file_id,
                "CONTAINS",
                {"repository_path": repository_path},
            )
            for symbol in parsed.symbols:
                if symbol.kind not in {"class", "function", "interface", "method"}:
                    continue
                qualified = f"{symbol.parent}.{symbol.name}" if symbol.parent else symbol.name
                symbol_id = self._node_id("symbol", f"{path}:{symbol.kind}:{qualified}")
                labels = ("Symbol", self._symbol_label(symbol.kind))
                self._add_node(
                    nodes,
                    symbol_id,
                    labels,
                    {
                        "path": path,
                        "name": symbol.name,
                        "kind": symbol.kind,
                        "line": symbol.line,
                        "repository_path": repository_path,
                    },
                )
                symbol_ids[f"{path}:{qualified}"] = symbol_id
                self._add_edge(
                    edges,
                    file_id,
                    symbol_id,
                    "DEFINES",
                    {"repository_path": repository_path},
                )
                for inherited in symbol.inherits:
                    target_id = self._external_id("symbol", inherited)
                    self._add_external_node(
                        nodes,
                        target_id,
                        "ExternalSymbol",
                        inherited,
                        repository_path,
                    )
                    self._add_edge(
                        edges,
                        symbol_id,
                        target_id,
                        "INHERITS",
                        {"repository_path": repository_path},
                    )
        return symbol_ids

    def _add_dependency_edges(
        self,
        dependency_edges: tuple[DependencyEdge, ...],
        repository_path: str,
        nodes: dict[str, KnowledgeGraphNode],
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge],
    ) -> None:
        for edge in dependency_edges:
            source_id = self._file_id(edge.source)
            target_id = (
                self._file_id(edge.target)
                if edge.target
                else self._external_id("dependency", edge.import_name)
            )
            if edge.target is None:
                self._add_external_node(
                    nodes,
                    target_id,
                    "ExternalDependency",
                    edge.import_name,
                    repository_path,
                )
            self._add_edge(
                edges,
                source_id,
                target_id,
                "IMPORTS",
                {"repository_path": repository_path, "name": edge.import_name},
            )

    def _add_call_edges(
        self,
        call_edges: tuple[CallGraphEdge, ...],
        repository_path: str,
        symbol_ids: dict[str, str],
        nodes: dict[str, KnowledgeGraphNode],
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge],
    ) -> None:
        for edge in call_edges:
            source_id = symbol_ids.get(edge.source or "")
            if source_id is None:
                continue
            target_id = symbol_ids.get(edge.target or "") or self._external_id("call", edge.callee)
            if edge.target is None:
                self._add_external_node(
                    nodes,
                    target_id,
                    "ExternalCall",
                    edge.callee,
                    repository_path,
                )
            self._add_edge(
                edges,
                source_id,
                target_id,
                "CALLS",
                {
                    "repository_path": repository_path,
                    "name": edge.callee,
                    "recursive": edge.recursive,
                },
            )

    def _add_node(
        self,
        nodes: dict[str, KnowledgeGraphNode],
        node_id: str,
        labels: tuple[str, ...],
        properties: dict[str, GraphProperty],
    ) -> None:
        nodes[node_id] = KnowledgeGraphNode(
            id=node_id,
            labels=("ForgeNode", *labels),
            properties={"id": node_id, **properties},
        )

    def _add_external_node(
        self,
        nodes: dict[str, KnowledgeGraphNode],
        node_id: str,
        label: str,
        name: str,
        repository_path: str,
    ) -> None:
        self._add_node(
            nodes,
            node_id,
            (label,),
            {"name": name, "repository_path": repository_path},
        )

    def _add_edge(
        self,
        edges: dict[tuple[str, str, str], KnowledgeGraphEdge],
        source: str,
        target: str,
        relationship: str,
        properties: dict[str, GraphProperty],
    ) -> None:
        edges[(source, relationship, target)] = KnowledgeGraphEdge(
            source=source,
            target=target,
            relationship=relationship,
            properties=properties,
        )

    def _directory_id(self, path: str) -> str:
        return self._node_id("directory", path)

    def _file_id(self, path: str | None) -> str:
        return self._node_id("file", path or "")

    def _external_id(self, kind: str, name: str) -> str:
        return self._node_id(f"external:{kind}", name)

    def _node_id(self, kind: str, value: str) -> str:
        return f"{kind}:{value}"

    def _symbol_label(self, kind: str) -> str:
        return {
            "class": "Class",
            "function": "Function",
            "interface": "Interface",
            "method": "Method",
        }[kind]
