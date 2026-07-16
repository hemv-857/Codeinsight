from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService

ViolationSeverity = Literal["low", "medium", "high", "critical"]

TEST_PARTS = {"__tests__", "spec", "test", "tests"}
UI_PARTS = {"components", "frontend", "pages", "ui", "views"}
API_PARTS = {"api", "controllers", "handlers", "routes", "views"}
SERVICE_PARTS = {"services", "usecases", "use_cases"}
PERSISTENCE_PARTS = {"database", "db", "models", "repositories"}
INFRASTRUCTURE_PARTS = {"config", "docker", "infrastructure", "scripts", "settings"}


class ArchitectureViolationError(Exception):
    """Raised when architecture violation detection cannot continue."""


@dataclass(frozen=True)
class ArchitectureViolation:
    """One dependency edge that violates a common architecture boundary."""

    rule_id: str
    severity: ViolationSeverity
    source: str
    target: str
    import_name: str
    title: str
    description: str
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureViolationStats:
    """Summary counts for architecture violation detection."""

    dependency_count: int
    violation_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


@dataclass(frozen=True)
class ArchitectureViolationReport:
    """Architecture violation report for one repository."""

    repository_path: str
    violations: tuple[ArchitectureViolation, ...]
    stats: ArchitectureViolationStats


class ArchitectureViolationService:
    """Detects practical architecture boundary violations from import edges."""

    def __init__(self, dependency_graph: DependencyGraphService) -> None:
        self.dependency_graph = dependency_graph

    def detect(self, repository_path: Path) -> ArchitectureViolationReport:
        try:
            graph = self.dependency_graph.build(repository_path)
        except DependencyGraphError as error:
            raise ArchitectureViolationError(str(error)) from error

        findings: list[ArchitectureViolation] = []
        for edge in graph.edges:
            violation = self._violation_for_edge(edge)
            if violation is not None:
                findings.append(violation)
        violations = tuple(
            sorted(
                findings, key=lambda item: (severity_rank(item.severity), item.source, item.target)
            )
        )
        return ArchitectureViolationReport(
            repository_path=graph.repository_path,
            violations=violations,
            stats=ArchitectureViolationStats(
                dependency_count=graph.stats.internal_dependency_count,
                violation_count=len(violations),
                critical_count=sum(1 for item in violations if item.severity == "critical"),
                high_count=sum(1 for item in violations if item.severity == "high"),
                medium_count=sum(1 for item in violations if item.severity == "medium"),
                low_count=sum(1 for item in violations if item.severity == "low"),
            ),
        )

    def _violation_for_edge(self, edge: DependencyEdge) -> ArchitectureViolation | None:
        if edge.target is None:
            return None
        source_parts = path_parts(edge.source)
        target_parts = path_parts(edge.target)
        if is_test(source_parts) is False and is_test(target_parts):
            return self._violation(
                edge=edge,
                rule_id="production-imports-test",
                severity="high",
                title="Production code imports test code",
                description="Production source depends on a test-only module.",
                confidence=0.92,
                evidence=("source is not under a test path", "target is under a test path"),
            )
        if has_any(source_parts, UI_PARTS) and has_any(
            target_parts, PERSISTENCE_PARTS | INFRASTRUCTURE_PARTS
        ):
            return self._violation(
                edge=edge,
                rule_id="ui-depends-on-infrastructure",
                severity="high",
                title="UI depends on infrastructure",
                description=(
                    "UI code should depend on API or application services, not persistence "
                    "or infrastructure modules."
                ),
                confidence=0.82,
                evidence=("source matches UI layer", "target matches infrastructure layer"),
            )
        if has_any(source_parts, API_PARTS) and has_any(target_parts, PERSISTENCE_PARTS):
            return self._violation(
                edge=edge,
                rule_id="api-skips-service-layer",
                severity="medium",
                title="API skips service layer",
                description="API route or controller imports persistence code directly.",
                confidence=0.78,
                evidence=("source matches API layer", "target matches persistence layer"),
            )
        if has_any(source_parts, PERSISTENCE_PARTS) and has_any(target_parts, API_PARTS | UI_PARTS):
            return self._violation(
                edge=edge,
                rule_id="persistence-depends-on-interface",
                severity="critical",
                title="Persistence depends on interface layer",
                description=(
                    "Persistence modules should not import UI, route, or controller modules."
                ),
                confidence=0.88,
                evidence=("source matches persistence layer", "target matches interface layer"),
            )
        if has_any(source_parts, SERVICE_PARTS) and has_any(target_parts, UI_PARTS):
            return self._violation(
                edge=edge,
                rule_id="service-depends-on-ui",
                severity="critical",
                title="Service depends on UI",
                description="Application services should not depend on presentation components.",
                confidence=0.9,
                evidence=("source matches service layer", "target matches UI layer"),
            )
        return None

    def _violation(
        self,
        *,
        edge: DependencyEdge,
        rule_id: str,
        severity: ViolationSeverity,
        title: str,
        description: str,
        confidence: float,
        evidence: tuple[str, ...],
    ) -> ArchitectureViolation:
        target = edge.target
        if target is None:
            raise ArchitectureViolationError("Internal violation edge is missing a target.")
        return ArchitectureViolation(
            rule_id=rule_id,
            severity=severity,
            source=edge.source,
            target=target,
            import_name=edge.import_name,
            title=title,
            description=description,
            confidence=confidence,
            evidence=evidence,
        )


def path_parts(path: str) -> set[str]:
    pure_path = PurePosixPath(path)
    return {part.lower().removesuffix(".py") for part in pure_path.parts}


def has_any(parts: set[str], names: set[str]) -> bool:
    return bool(parts & names)


def is_test(parts: set[str]) -> bool:
    return bool(parts & TEST_PARTS) or any(part.startswith("test_") for part in parts)


def severity_rank(severity: ViolationSeverity) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}[severity]
