import re
from dataclasses import dataclass
from pathlib import Path

from graph.call_graph import CallGraphEdge, CallGraphError, CallGraphService
from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParseError

from backend.app.services.architecture_docs import ArchitectureDocsError, ArchitectureDocsService
from backend.app.services.architecture_explanation import ArchitectureExplanationError
from backend.app.services.repository_scanner import RepositoryScanError
from backend.app.services.repository_summary import RepositorySummaryError

MAX_DIAGRAM_EDGES = 12
NODE_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_]")


class MermaidDiagramError(Exception):
    """Raised when Mermaid diagram generation cannot continue."""


@dataclass(frozen=True)
class MermaidDiagram:
    """One generated Mermaid diagram."""

    kind: str
    title: str
    description: str
    code: str


@dataclass(frozen=True)
class MermaidDiagramStats:
    """Generated Mermaid diagram statistics."""

    diagram_count: int
    dependency_edge_count: int
    call_edge_count: int
    component_count: int


@dataclass(frozen=True)
class MermaidDiagramSet:
    """Generated Mermaid diagrams for a repository."""

    repository_path: str
    focus: str | None
    diagrams: tuple[MermaidDiagram, ...]
    stats: MermaidDiagramStats


class MermaidDiagramService:
    """Generates Mermaid diagram source from repository graph evidence."""

    def __init__(
        self,
        architecture_docs: ArchitectureDocsService,
        dependency_graph: DependencyGraphService,
        call_graph: CallGraphService,
    ) -> None:
        self.architecture_docs = architecture_docs
        self.dependency_graph = dependency_graph
        self.call_graph = call_graph

    def generate(self, repository_path: Path, focus: str | None = None) -> MermaidDiagramSet:
        """Generate Mermaid diagrams for a repository path."""
        try:
            architecture = self.architecture_docs.generate(repository_path, focus=focus)
            dependencies = self.dependency_graph.build(repository_path)
            calls = self.call_graph.build(repository_path)
        except (
            RepositoryScanError,
            RepositorySummaryError,
            ArchitectureExplanationError,
            ArchitectureDocsError,
            DependencyGraphError,
            CallGraphError,
            TreeSitterParseError,
        ) as error:
            raise MermaidDiagramError(str(error)) from error

        internal_edges = tuple(edge for edge in dependencies.edges if edge.target is not None)
        resolved_calls = tuple(
            edge for edge in calls.edges if edge.source is not None and edge.target is not None
        )
        diagrams = (
            self._architecture_diagram(architecture.title, architecture.evidence_paths),
            self._dependency_diagram(internal_edges),
            self._call_diagram(resolved_calls),
        )
        return MermaidDiagramSet(
            repository_path=architecture.repository_path,
            focus=architecture.focus,
            diagrams=diagrams,
            stats=MermaidDiagramStats(
                diagram_count=len(diagrams),
                dependency_edge_count=len(internal_edges),
                call_edge_count=len(resolved_calls),
                component_count=architecture.stats.component_count,
            ),
        )

    def _architecture_diagram(
        self,
        title: str,
        evidence_paths: tuple[str, ...],
    ) -> MermaidDiagram:
        lines = ["flowchart TD", f"  repo[{self._quote(title)}]"]
        for path in evidence_paths[:MAX_DIAGRAM_EDGES]:
            node_id = self._node_id(path)
            lines.append(f"  repo --> {node_id}[{self._quote(path)}]")
        if len(lines) == 2:
            lines.append('  repo --> empty["No evidence paths available"]')
        return MermaidDiagram(
            kind="architecture",
            title="Architecture Overview",
            description="Repository architecture evidence paths surfaced by CodeInsight.",
            code="\n".join(lines),
        )

    def _dependency_diagram(self, edges: tuple[DependencyEdge, ...]) -> MermaidDiagram:
        lines = ["flowchart LR"]
        for edge in edges[:MAX_DIAGRAM_EDGES]:
            if edge.target is None:
                continue
            lines.append(
                f"  {self._node_id(edge.source)}[{self._quote(edge.source)}] --> "
                f"{self._node_id(edge.target)}[{self._quote(edge.target)}]"
            )
        if len(lines) == 1:
            lines.append('  no_dependencies["No internal dependencies detected"]')
        return MermaidDiagram(
            kind="dependency",
            title="Dependency Flow",
            description="Internal file imports resolved by the dependency graph.",
            code="\n".join(lines),
        )

    def _call_diagram(self, edges: tuple[CallGraphEdge, ...]) -> MermaidDiagram:
        lines = ["flowchart LR"]
        for edge in edges[:MAX_DIAGRAM_EDGES]:
            if edge.source is None or edge.target is None:
                continue
            lines.append(
                f"  {self._node_id(edge.source)}[{self._quote(edge.source)}] -->|"
                f"{self._quote(edge.callee)}| "
                f"{self._node_id(edge.target)}[{self._quote(edge.target)}]"
            )
        if len(lines) == 1:
            lines.append('  no_calls["No resolved calls detected"]')
        return MermaidDiagram(
            kind="call",
            title="Call Flow",
            description="Resolved function and method calls from parsed source files.",
            code="\n".join(lines),
        )

    def _node_id(self, value: str) -> str:
        cleaned = NODE_ID_PATTERN.sub("_", value).strip("_")
        return f"n_{cleaned[:80] or 'node'}"

    def _quote(self, value: str) -> str:
        escaped = value.replace('"', "'")
        return f'"{escaped}"'
