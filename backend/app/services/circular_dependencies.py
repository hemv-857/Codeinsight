from dataclasses import dataclass
from pathlib import Path

from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService


class CircularDependencyError(Exception):
    """Raised when circular dependency detection cannot continue."""


@dataclass(frozen=True)
class CircularDependencyEdge:
    """One internal dependency edge participating in a cycle."""

    source: str
    target: str
    import_name: str


@dataclass(frozen=True)
class CircularDependencyCycle:
    """One detected circular dependency cycle."""

    files: tuple[str, ...]
    length: int
    edges: tuple[CircularDependencyEdge, ...]


@dataclass(frozen=True)
class CircularDependencyStats:
    """Summary counts for circular dependency detection."""

    cycle_count: int
    affected_file_count: int
    max_cycle_length: int
    internal_dependency_count: int


@dataclass(frozen=True)
class CircularDependencyReport:
    """Circular dependency report for a repository."""

    repository_path: str
    cycles: tuple[CircularDependencyCycle, ...]
    stats: CircularDependencyStats


class CircularDependencyService:
    """Detects file-level circular dependencies from the dependency graph."""

    def __init__(self, dependency_graph: DependencyGraphService) -> None:
        self.dependency_graph = dependency_graph

    def detect(self, repository_path: Path) -> CircularDependencyReport:
        try:
            graph = self.dependency_graph.build(repository_path)
        except DependencyGraphError as error:
            raise CircularDependencyError(str(error)) from error

        internal_edges = [edge for edge in graph.edges if edge.target is not None]
        cycles = tuple(
            CircularDependencyCycle(
                files=cycle,
                length=len(cycle),
                edges=tuple(self._cycle_edges(cycle, internal_edges)),
            )
            for cycle in graph.circular_dependencies
        )
        affected_files = {path for cycle in cycles for path in cycle.files}
        return CircularDependencyReport(
            repository_path=graph.repository_path,
            cycles=cycles,
            stats=CircularDependencyStats(
                cycle_count=len(cycles),
                affected_file_count=len(affected_files),
                max_cycle_length=max((cycle.length for cycle in cycles), default=0),
                internal_dependency_count=graph.stats.internal_dependency_count,
            ),
        )

    def _cycle_edges(
        self, cycle: tuple[str, ...], edges: list[DependencyEdge]
    ) -> list[CircularDependencyEdge]:
        cycle_edges: list[CircularDependencyEdge] = []
        for edge in edges:
            if edge.target is None:
                continue
            if edge.source not in cycle or edge.target not in cycle:
                continue
            cycle_edges.append(
                CircularDependencyEdge(
                    source=edge.source,
                    target=edge.target,
                    import_name=edge.import_name,
                )
            )
        return cycle_edges
