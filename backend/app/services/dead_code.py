from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from graph.call_graph import CallGraphEdge, CallGraphError, CallGraphNode, CallGraphService
from graph.dependency_graph import DependencyGraphError, DependencyGraphService

DeadCodeKind = Literal["unused_file", "unused_callable"]

ENTRYPOINT_NAMES = {
    "__init__",
    "app",
    "index",
    "main",
    "manage",
    "mod",
    "server",
}
ENTRYPOINT_SYMBOLS = {"main", "handler", "render"}
TEST_PARTS = {"__tests__", "spec", "test", "tests"}


class DeadCodeError(Exception):
    """Raised when dead code detection cannot continue."""


@dataclass(frozen=True)
class DeadCodeFinding:
    """One candidate dead code finding."""

    kind: DeadCodeKind
    path: str
    title: str
    description: str
    confidence: float
    line: int | None = None
    symbol_name: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeadCodeStats:
    """Summary counts for a dead code detection run."""

    file_count: int
    callable_count: int
    finding_count: int
    unused_file_count: int
    unused_callable_count: int


@dataclass(frozen=True)
class DeadCodeReport:
    """Dead code candidate report for a repository."""

    repository_path: str
    findings: tuple[DeadCodeFinding, ...]
    stats: DeadCodeStats


class DeadCodeService:
    """Detects conservative dead code candidates from dependency and call graphs."""

    def __init__(
        self,
        dependency_graph: DependencyGraphService,
        call_graph: CallGraphService,
    ) -> None:
        self.dependency_graph = dependency_graph
        self.call_graph = call_graph

    def detect(self, repository_path: Path) -> DeadCodeReport:
        root = repository_path.expanduser().resolve()
        try:
            dependency_graph = self.dependency_graph.build(root)
            call_graph = self.call_graph.build(root)
        except (DependencyGraphError, CallGraphError) as error:
            raise DeadCodeError(str(error)) from error

        findings = [
            *self._unused_files(
                tuple(node.path for node in dependency_graph.nodes),
                tuple(edge.target for edge in dependency_graph.edges if edge.target is not None),
            ),
            *self._unused_callables(call_graph.nodes, call_graph.edges),
        ]
        ordered_findings = tuple(
            sorted(findings, key=lambda item: (item.path, item.line or 0, item.symbol_name or ""))
        )
        unused_file_count = sum(1 for finding in ordered_findings if finding.kind == "unused_file")
        unused_callable_count = sum(
            1 for finding in ordered_findings if finding.kind == "unused_callable"
        )
        return DeadCodeReport(
            repository_path=str(root),
            findings=ordered_findings,
            stats=DeadCodeStats(
                file_count=len(dependency_graph.nodes),
                callable_count=len(call_graph.nodes),
                finding_count=len(ordered_findings),
                unused_file_count=unused_file_count,
                unused_callable_count=unused_callable_count,
            ),
        )

    def _unused_files(
        self, paths: tuple[str, ...], imported_paths: tuple[str, ...]
    ) -> list[DeadCodeFinding]:
        incoming = Counter(imported_paths)
        return [
            DeadCodeFinding(
                kind="unused_file",
                path=path,
                title="Unreferenced source file",
                description=f"{path} is not imported by another parsed source file.",
                confidence=0.68,
                evidence=("no incoming internal imports",),
            )
            for path in paths
            if incoming[path] == 0 and not self._is_exempt_path(path)
        ]

    def _unused_callables(
        self, nodes: tuple[CallGraphNode, ...], edges: tuple[CallGraphEdge, ...]
    ) -> list[DeadCodeFinding]:
        incoming = Counter(edge.target for edge in edges if edge.target is not None)
        findings: list[DeadCodeFinding] = []
        for node in nodes:
            if incoming[node.id] > 0 or self._is_exempt_callable(node.path, node.name):
                continue
            findings.append(
                DeadCodeFinding(
                    kind="unused_callable",
                    path=node.path,
                    line=node.line,
                    symbol_name=node.name,
                    title="Uncalled function or method",
                    description=f"{node.name} has no resolved internal call sites.",
                    confidence=0.62 if node.kind == "method" else 0.72,
                    evidence=("no resolved incoming calls", node.kind),
                )
            )
        return findings

    def _is_exempt_callable(self, path: str, name: str) -> bool:
        if self._is_exempt_path(path):
            return True
        if name.startswith("_") or name in ENTRYPOINT_SYMBOLS:
            return True
        return False

    def _is_exempt_path(self, path: str) -> bool:
        pure_path = PurePosixPath(path)
        name = pure_path.stem
        if name in ENTRYPOINT_NAMES:
            return True
        if any(part.lower() in TEST_PARTS for part in pure_path.parts):
            return True
        return name.startswith("test_") or name.endswith((".test", ".spec"))
