from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService

from backend.app.services.architecture_violations import (
    ArchitectureViolation,
    ArchitectureViolationError,
    ArchitectureViolationService,
)
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService
from backend.app.services.repository_summary import (
    RepositorySummaryError,
    RepositorySummaryService,
    SummaryFile,
)

ArchitectureReviewSeverity = Literal["low", "medium", "high", "critical"]

MAX_REVIEW_ITEMS = 12
HIGH_FAN_IN = 3
HIGH_FAN_OUT = 3


class ArchitectureReviewError(Exception):
    """Raised when architecture review cannot continue."""


@dataclass(frozen=True)
class ArchitectureReviewFinding:
    """One architecture review finding for a proposed change."""

    category: str
    severity: ArchitectureReviewSeverity
    path: str | None
    title: str
    description: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureReviewImpactFile:
    """One architecture component likely affected by changed files."""

    path: str
    layer: str
    reason: str
    score: float


@dataclass(frozen=True)
class ArchitectureReviewStats:
    """Summary metrics for architecture review."""

    changed_file_count: int
    impacted_file_count: int
    violation_count: int
    finding_count: int
    risk_score: int
    risk_level: ArchitectureReviewSeverity
    confidence: float


@dataclass(frozen=True)
class ArchitectureReview:
    """Grounded architecture review result."""

    repository_path: str
    focus: str | None
    changed_files: tuple[str, ...]
    impacted_files: tuple[ArchitectureReviewImpactFile, ...]
    findings: tuple[ArchitectureReviewFinding, ...]
    recommendations: tuple[str, ...]
    summary: str
    stats: ArchitectureReviewStats


class ArchitectureReviewService:
    """Reviews proposed changes for architecture impact and boundary risks."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        dependency_graph: DependencyGraphService,
        summary: RepositorySummaryService,
        architecture_violations: ArchitectureViolationService,
    ) -> None:
        self.scanner = scanner
        self.dependency_graph = dependency_graph
        self.summary = summary
        self.architecture_violations = architecture_violations

    def review(
        self,
        repository_path: Path,
        changed_files: tuple[str, ...],
        focus: str | None = None,
    ) -> ArchitectureReview:
        """Review changed files against repository architecture signals."""
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            graph = self.dependency_graph.build(root)
            summary = self.summary.summarize(root)
            violations = self.architecture_violations.detect(root)
        except (
            RepositoryScanError,
            DependencyGraphError,
            RepositorySummaryError,
            ArchitectureViolationError,
        ) as error:
            raise ArchitectureReviewError(str(error)) from error

        repository_files = tuple(file.path for file in scan.files)
        normalized_changed = self._changed_files(changed_files, repository_files)
        impacted_files = self._impacted_files(normalized_changed, graph.edges, summary.key_files)
        scoped_violations = self._scoped_violations(violations.violations, impacted_files)
        findings = self._findings(
            changed_files=normalized_changed,
            impacted_files=impacted_files,
            key_files=summary.key_files,
            edges=graph.edges,
            violations=scoped_violations,
        )
        risk_score = self._risk_score(normalized_changed, impacted_files, findings)
        return ArchitectureReview(
            repository_path=str(root),
            focus=focus,
            changed_files=normalized_changed,
            impacted_files=impacted_files,
            findings=findings,
            recommendations=self._recommendations(impacted_files, findings, scoped_violations),
            summary=self._summary(normalized_changed, impacted_files, findings, risk_score),
            stats=ArchitectureReviewStats(
                changed_file_count=len(normalized_changed),
                impacted_file_count=len(impacted_files),
                violation_count=len(scoped_violations),
                finding_count=len(findings),
                risk_score=risk_score,
                risk_level=self._level(risk_score),
                confidence=self._confidence(normalized_changed, findings, scoped_violations),
            ),
        )

    def _changed_files(
        self,
        changed_files: tuple[str, ...],
        repository_files: tuple[str, ...],
    ) -> tuple[str, ...]:
        matched = [
            self._match_file(path, repository_files) or path.strip().lstrip("./")
            for path in changed_files
            if path.strip()
        ]
        return tuple(dict.fromkeys(matched))

    def _match_file(self, path: str, repository_files: tuple[str, ...]) -> str | None:
        normalized = PurePosixPath(path).as_posix().lstrip("./")
        for repository_file in repository_files:
            if normalized == repository_file or normalized.endswith(f"/{repository_file}"):
                return repository_file
        basename_matches = [
            item
            for item in repository_files
            if PurePosixPath(item).name == PurePosixPath(normalized).name
        ]
        return basename_matches[0] if len(basename_matches) == 1 else None

    def _impacted_files(
        self,
        changed_files: tuple[str, ...],
        edges: tuple[DependencyEdge, ...],
        key_files: tuple[SummaryFile, ...],
    ) -> tuple[ArchitectureReviewImpactFile, ...]:
        impacted: dict[str, ArchitectureReviewImpactFile] = {
            path: ArchitectureReviewImpactFile(
                path=path,
                layer=self._layer(path),
                reason="changed in architecture review",
                score=0.96,
            )
            for path in changed_files
        }
        changed = set(changed_files)
        for edge in edges:
            if edge.target in changed:
                impacted.setdefault(
                    edge.source,
                    ArchitectureReviewImpactFile(
                        path=edge.source,
                        layer=self._layer(edge.source),
                        reason=f"depends on changed file {edge.target}",
                        score=0.74,
                    ),
                )
            if edge.source in changed and edge.target is not None:
                impacted.setdefault(
                    edge.target,
                    ArchitectureReviewImpactFile(
                        path=edge.target,
                        layer=self._layer(edge.target),
                        reason=f"direct dependency of changed file {edge.source}",
                        score=0.66,
                    ),
                )
        key_file_paths = {file.path for file in key_files}
        for path in changed & key_file_paths:
            impacted[path] = ArchitectureReviewImpactFile(
                path=path,
                layer=self._layer(path),
                reason="changed key architecture file",
                score=0.99,
            )
        return tuple(sorted(impacted.values(), key=lambda item: (-item.score, item.path)))[
            :MAX_REVIEW_ITEMS
        ]

    def _scoped_violations(
        self,
        violations: tuple[ArchitectureViolation, ...],
        impacted_files: tuple[ArchitectureReviewImpactFile, ...],
    ) -> tuple[ArchitectureViolation, ...]:
        impacted = {file.path for file in impacted_files}
        return tuple(
            violation
            for violation in violations
            if violation.source in impacted or violation.target in impacted
        )[:MAX_REVIEW_ITEMS]

    def _findings(
        self,
        *,
        changed_files: tuple[str, ...],
        impacted_files: tuple[ArchitectureReviewImpactFile, ...],
        key_files: tuple[SummaryFile, ...],
        edges: tuple[DependencyEdge, ...],
        violations: tuple[ArchitectureViolation, ...],
    ) -> tuple[ArchitectureReviewFinding, ...]:
        findings: list[ArchitectureReviewFinding] = []
        changed = set(changed_files)
        impacted_layers = {file.layer for file in impacted_files}
        if len(impacted_layers) >= 3:
            findings.append(
                ArchitectureReviewFinding(
                    category="layer_spread",
                    severity="high",
                    path=None,
                    title="Change crosses multiple architecture layers",
                    description=f"The change reaches {len(impacted_layers)} inferred layers.",
                    evidence=tuple(sorted(impacted_layers)),
                )
            )
        for key_file in key_files:
            if key_file.path in changed:
                findings.append(
                    ArchitectureReviewFinding(
                        category="key_component_changed",
                        severity="high",
                        path=key_file.path,
                        title="Key architecture file changed",
                        description="This file is central in the repository summary.",
                        evidence=(
                            f"{key_file.dependency_count} outgoing dependencies",
                            f"{key_file.dependent_count} incoming dependents",
                        ),
                    )
                )
        findings.extend(self._fan_findings(changed_files, edges))
        for violation in violations:
            findings.append(
                ArchitectureReviewFinding(
                    category=f"boundary:{violation.rule_id}",
                    severity=violation.severity,
                    path=violation.source,
                    title=violation.title,
                    description=violation.description,
                    evidence=(
                        f"{violation.source} imports {violation.target}",
                        *violation.evidence,
                    ),
                )
            )
        return tuple(findings[:MAX_REVIEW_ITEMS])

    def _fan_findings(
        self,
        changed_files: tuple[str, ...],
        edges: tuple[DependencyEdge, ...],
    ) -> tuple[ArchitectureReviewFinding, ...]:
        findings: list[ArchitectureReviewFinding] = []
        for path in changed_files:
            fan_out = sum(1 for edge in edges if edge.source == path and edge.target is not None)
            fan_in = sum(1 for edge in edges if edge.target == path)
            if fan_out >= HIGH_FAN_OUT:
                findings.append(
                    ArchitectureReviewFinding(
                        category="high_fan_out",
                        severity="medium",
                        path=path,
                        title="Changed file has broad outgoing dependencies",
                        description="This file imports several internal files.",
                        evidence=(f"{fan_out} outgoing internal dependencies",),
                    )
                )
            if fan_in >= HIGH_FAN_IN:
                findings.append(
                    ArchitectureReviewFinding(
                        category="high_fan_in",
                        severity="high",
                        path=path,
                        title="Changed file has many dependents",
                        description="Several files depend on this changed file.",
                        evidence=(f"{fan_in} incoming internal dependents",),
                    )
                )
        return tuple(findings)

    def _recommendations(
        self,
        impacted_files: tuple[ArchitectureReviewImpactFile, ...],
        findings: tuple[ArchitectureReviewFinding, ...],
        violations: tuple[ArchitectureViolation, ...],
    ) -> tuple[str, ...]:
        recommendations = ["Review direct architecture neighbors before merging."]
        if any(file.layer in {"api", "ui", "persistence"} for file in impacted_files):
            recommendations.append("Verify layer boundaries through the service layer.")
        if violations:
            recommendations.append("Resolve or document architecture boundary violations.")
        if any(finding.category == "key_component_changed" for finding in findings):
            recommendations.append("Regenerate architecture docs and diagrams after this change.")
        return tuple(dict.fromkeys(recommendations))

    def _risk_score(
        self,
        changed_files: tuple[str, ...],
        impacted_files: tuple[ArchitectureReviewImpactFile, ...],
        findings: tuple[ArchitectureReviewFinding, ...],
    ) -> int:
        severity_points = {"low": 4, "medium": 10, "high": 20, "critical": 35}
        score = min(len(changed_files) * 6, 24)
        score += min(max(len(impacted_files) - len(changed_files), 0) * 8, 28)
        score += min(sum(severity_points[finding.severity] for finding in findings), 52)
        return max(0, min(score, 100))

    def _summary(
        self,
        changed_files: tuple[str, ...],
        impacted_files: tuple[ArchitectureReviewImpactFile, ...],
        findings: tuple[ArchitectureReviewFinding, ...],
        risk_score: int,
    ) -> str:
        return (
            f"Reviewed {len(changed_files)} changed files across "
            f"{len(impacted_files)} architecture-impact files with {len(findings)} findings. "
            f"Architecture risk score: {risk_score}."
        )

    def _confidence(
        self,
        changed_files: tuple[str, ...],
        findings: tuple[ArchitectureReviewFinding, ...],
        violations: tuple[ArchitectureViolation, ...],
    ) -> float:
        return min(
            0.94,
            0.5
            + min(len(changed_files), 5) * 0.05
            + min(len(findings), 4) * 0.04
            + min(len(violations), 3) * 0.03,
        )

    def _level(self, score: int) -> ArchitectureReviewSeverity:
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    def _layer(self, path: str) -> str:
        parts = {part.lower().removesuffix(".py") for part in PurePosixPath(path).parts}
        if parts & {"components", "frontend", "pages", "ui", "views"}:
            return "ui"
        if parts & {"api", "controllers", "handlers", "routes"}:
            return "api"
        if parts & {"services", "usecases", "use_cases"}:
            return "service"
        if parts & {"database", "db", "models", "repositories"}:
            return "persistence"
        if parts & {"config", "docker", "infrastructure", "scripts", "settings"}:
            return "infrastructure"
        if parts & {"test", "tests", "__tests__", "spec"} or PurePosixPath(path).name.startswith(
            "test_"
        ):
            return "test"
        return "source"
