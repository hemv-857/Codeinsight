from dataclasses import dataclass
from pathlib import Path

from backend.app.services.repository_scanner import RepositoryScannerService
from parser.tree_sitter_parser import (
    ParseTreeSummary,
    SourceCall,
    SourceSymbol,
    TreeSitterParseError,
    TreeSitterParserService,
)


class CallGraphError(Exception):
    """Raised when call graph construction cannot continue."""


@dataclass(frozen=True)
class CallGraphNode:
    """A callable source symbol in a repository call graph."""

    id: str
    name: str
    kind: str
    path: str
    line: int
    parent: str | None = None


@dataclass(frozen=True)
class CallGraphEdge:
    """A call from one callable scope to another callable target."""

    source: str | None
    target: str | None
    caller: str | None
    callee: str
    path: str
    line: int
    recursive: bool


@dataclass(frozen=True)
class CallGraphStats:
    """Summary counts for a repository call graph."""

    callable_count: int
    call_count: int
    resolved_call_count: int
    unresolved_call_count: int
    recursive_call_count: int


@dataclass(frozen=True)
class CallGraph:
    """Function and method call graph for a repository."""

    repository_path: str
    nodes: tuple[CallGraphNode, ...]
    edges: tuple[CallGraphEdge, ...]
    unresolved_calls: tuple[str, ...]
    stats: CallGraphStats


class CallGraphService:
    """Builds a function-level call graph from parsed repository call sites."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
    ) -> None:
        self.scanner = scanner
        self.parser = parser

    def build(self, repository_path: Path) -> CallGraph:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            parsed_files = [
                (file.path, self.parser.parse_file(root / file.path))
                for file in scan.files
                if file.language is not None and self.parser.supports_path(Path(file.path))
            ]
        except TreeSitterParseError as error:
            raise CallGraphError(str(error)) from error

        nodes = tuple(self._nodes_for_files(parsed_files))
        node_by_path_and_name = {(node.path, node.name): node.id for node in nodes}
        node_by_name = self._nodes_by_name(nodes)
        edges = tuple(self._edges_for_files(parsed_files, node_by_path_and_name, node_by_name))
        unresolved = tuple(sorted({edge.callee for edge in edges if edge.target is None}))
        return CallGraph(
            repository_path=str(root),
            nodes=nodes,
            edges=edges,
            unresolved_calls=unresolved,
            stats=CallGraphStats(
                callable_count=len(nodes),
                call_count=len(edges),
                resolved_call_count=sum(1 for edge in edges if edge.target is not None),
                unresolved_call_count=sum(1 for edge in edges if edge.target is None),
                recursive_call_count=sum(1 for edge in edges if edge.recursive),
            ),
        )

    def _nodes_for_files(
        self,
        parsed_files: list[tuple[str, ParseTreeSummary]],
    ) -> list[CallGraphNode]:
        nodes: list[CallGraphNode] = []
        for path, parsed in parsed_files:
            for symbol in parsed.symbols:
                if symbol.kind in {"function", "method"}:
                    nodes.append(self._node(path, symbol))
        return nodes

    def _edges_for_files(
        self,
        parsed_files: list[tuple[str, ParseTreeSummary]],
        node_by_path_and_name: dict[tuple[str, str], str],
        node_by_name: dict[str, list[str]],
    ) -> list[CallGraphEdge]:
        edges: list[CallGraphEdge] = []
        for path, parsed in parsed_files:
            for call in parsed.calls:
                source = (
                    node_by_path_and_name.get((path, call.caller))
                    if call.caller is not None
                    else None
                )
                target = self._resolve_call(path, call, node_by_path_and_name, node_by_name)
                edges.append(
                    CallGraphEdge(
                        source=source,
                        target=target,
                        caller=call.caller,
                        callee=call.callee,
                        path=path,
                        line=call.line,
                        recursive=call.recursive,
                    )
                )
        return edges

    def _resolve_call(
        self,
        path: str,
        call: SourceCall,
        node_by_path_and_name: dict[tuple[str, str], str],
        node_by_name: dict[str, list[str]],
    ) -> str | None:
        local = node_by_path_and_name.get((path, call.callee))
        if local is not None:
            return local
        matches = node_by_name.get(call.callee, [])
        return matches[0] if len(matches) == 1 else None

    def _node(self, path: str, symbol: SourceSymbol) -> CallGraphNode:
        name = f"{symbol.parent}.{symbol.name}" if symbol.parent else symbol.name
        return CallGraphNode(
            id=f"{path}:{name}",
            name=symbol.name,
            kind=symbol.kind,
            path=path,
            line=symbol.line,
            parent=symbol.parent,
        )

    def _nodes_by_name(self, nodes: tuple[CallGraphNode, ...]) -> dict[str, list[str]]:
        by_name: dict[str, list[str]] = {}
        for node in nodes:
            by_name.setdefault(node.name, []).append(node.id)
        return by_name
