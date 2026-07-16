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
from backend.app.services.technical_debt import (
    TechnicalDebtError,
    TechnicalDebtFinding,
    TechnicalDebtService,
)

ReviewSeverity = Literal["low", "medium", "high", "critical"]

HIGH_CHANGED_FILE_COUNT = 8
LARGE_DIFF_LINES = 300
MAX_ITEMS = 12


class PullRequestReviewError(Exception):
    """Raised when pull request review cannot continue."""


@dataclass(frozen=True)
class PullRequestFinding:
    """One finding from a pull request review."""

    category: str
    severity: ReviewSeverity
    path: str | None
    title: str
    description: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class PullRequestImpactFile:
    """One file likely affected by a pull request."""

    path: str
    reason: str
    score: float


@dataclass(frozen=True)
class PullRequestReviewStats:
    """Summary metrics for a pull request review."""

    changed_file_count: int
    impacted_file_count: int
    finding_count: int
    risk_score: int
    risk_level: ReviewSeverity
    confidence: float


@dataclass(frozen=True)
class PullRequestReview:
    """Grounded pull request review result."""

    repository_path: str
    title: str | None
    description: str | None
    changed_files: tuple[str, ...]
    impacted_files: tuple[PullRequestImpactFile, ...]
    findings: tuple[PullRequestFinding, ...]
    recommendations: tuple[str, ...]
    summary: str
    stats: PullRequestReviewStats


class PullRequestReviewService:
    """Reviews pull request changes using repository graph and quality signals."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        dependency_graph: DependencyGraphService,
        technical_debt: TechnicalDebtService,
        architecture_violations: ArchitectureViolationService,
    ) -> None:
        self.scanner = scanner
        self.dependency_graph = dependency_graph
        self.technical_debt = technical_debt
        self.architecture_violations = architecture_violations

    def review(
        self,
        repository_path: Path,
        changed_files: tuple[str, ...],
        title: str | None = None,
        description: str | None = None,
        diff_text: str | None = None,
    ) -> PullRequestReview:
        """Review a pull request from changed files and optional diff text."""
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            graph = self.dependency_graph.build(root)
            debt = self.technical_debt.analyze(root)
            violations = self.architecture_violations.detect(root)
        except (
            RepositoryScanError,
            DependencyGraphError,
            TechnicalDebtError,
            ArchitectureViolationError,
        ) as error:
            raise PullRequestReviewError(str(error)) from error

        repository_files = tuple(file.path for file in scan.files)
        normalized_changed = self._changed_files(changed_files, repository_files)
        impacted_files = self._impacted_files(normalized_changed, graph.edges)
        findings = self._findings(
            changed_files=normalized_changed,
            impacted_files=impacted_files,
            debt_findings=debt.findings,
            architecture_violations=violations.violations,
            diff_text=diff_text or "",
        )
        risk_score = self._risk_score(normalized_changed, impacted_files, findings, diff_text or "")
        recommendations = self._recommendations(normalized_changed, impacted_files, findings)
        return PullRequestReview(
            repository_path=str(root),
            title=title,
            description=description,
            changed_files=normalized_changed,
            impacted_files=impacted_files,
            findings=findings,
            recommendations=recommendations,
            summary=self._summary(normalized_changed, impacted_files, findings, risk_score),
            stats=PullRequestReviewStats(
                changed_file_count=len(normalized_changed),
                impacted_file_count=len(impacted_files),
                finding_count=len(findings),
                risk_score=risk_score,
                risk_level=self._level(risk_score),
                confidence=self._confidence(normalized_changed, findings),
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
    ) -> tuple[PullRequestImpactFile, ...]:
        impacted: dict[str, PullRequestImpactFile] = {
            path: PullRequestImpactFile(path=path, reason="changed in pull request", score=0.95)
            for path in changed_files
        }
        changed = set(changed_files)
        for edge in edges:
            if edge.target in changed:
                impacted.setdefault(
                    edge.source,
                    PullRequestImpactFile(
                        path=edge.source,
                        reason=f"imports changed file {edge.target}",
                        score=0.72,
                    ),
                )
            if edge.source in changed and edge.target is not None:
                impacted.setdefault(
                    edge.target,
                    PullRequestImpactFile(
                        path=edge.target,
                        reason=f"imported by changed file {edge.source}",
                        score=0.62,
                    ),
                )
        return tuple(sorted(impacted.values(), key=lambda item: (-item.score, item.path)))[
            :MAX_ITEMS
        ]

    def _findings(
        self,
        *,
        changed_files: tuple[str, ...],
        impacted_files: tuple[PullRequestImpactFile, ...],
        debt_findings: tuple[TechnicalDebtFinding, ...],
        architecture_violations: tuple[ArchitectureViolation, ...],
        diff_text: str,
    ) -> tuple[PullRequestFinding, ...]:
        changed = set(changed_files)
        impacted = {file.path for file in impacted_files}
        findings: list[PullRequestFinding] = []
        if len(changed_files) >= HIGH_CHANGED_FILE_COUNT:
            findings.append(
                PullRequestFinding(
                    category="change_size",
                    severity="medium",
                    path=None,
                    title="Large pull request surface",
                    description=f"{len(changed_files)} files are changed.",
                    evidence=(f"{len(changed_files)} changed files",),
                )
            )
        added_or_removed = self._diff_change_count(diff_text)
        if added_or_removed >= LARGE_DIFF_LINES:
            findings.append(
                PullRequestFinding(
                    category="diff_size",
                    severity="high",
                    path=None,
                    title="Large diff",
                    description=f"The provided diff changes {added_or_removed} lines.",
                    evidence=(f"{added_or_removed} added or removed lines",),
                )
            )
        if changed_files and not any(self._is_test_path(path) for path in changed_files):
            findings.append(
                PullRequestFinding(
                    category="testing",
                    severity="medium",
                    path=None,
                    title="No test files changed",
                    description="Changed files do not include an obvious test file.",
                    evidence=("no changed path contains test markers",),
                )
            )
        for finding in debt_findings:
            if finding.path in changed:
                findings.append(
                    PullRequestFinding(
                        category=f"technical_debt:{finding.category}",
                        severity=finding.severity,
                        path=finding.path,
                        title=finding.title,
                        description=finding.description,
                        evidence=tuple(finding.evidence),
                    )
                )
        for violation in architecture_violations:
            if violation.source in impacted or violation.target in impacted:
                findings.append(
                    PullRequestFinding(
                        category=f"architecture:{violation.rule_id}",
                        severity=violation.severity,
                        path=violation.source,
                        title=violation.title,
                        description=violation.description,
                        evidence=tuple(violation.evidence),
                    )
                )
        return tuple(findings[:MAX_ITEMS])

    def _diff_change_count(self, diff_text: str) -> int:
        return sum(
            1
            for line in diff_text.splitlines()
            if (line.startswith("+") and not line.startswith("+++"))
            or (line.startswith("-") and not line.startswith("---"))
        )

    def _is_test_path(self, path: str) -> bool:
        parts = {part.lower() for part in PurePosixPath(path).parts}
        name = PurePosixPath(path).name.lower()
        return bool(parts & {"test", "tests", "__tests__", "spec"}) or name.startswith("test_")

    def _risk_score(
        self,
        changed_files: tuple[str, ...],
        impacted_files: tuple[PullRequestImpactFile, ...],
        findings: tuple[PullRequestFinding, ...],
        diff_text: str,
    ) -> int:
        severity_points = {"low": 4, "medium": 10, "high": 20, "critical": 35}
        score = min(len(changed_files) * 5, 25)
        score += min(max(len(impacted_files) - len(changed_files), 0) * 8, 25)
        score += min(self._diff_change_count(diff_text) // 20, 20)
        score += min(sum(severity_points[item.severity] for item in findings), 45)
        return max(0, min(score, 100))

    def _recommendations(
        self,
        changed_files: tuple[str, ...],
        impacted_files: tuple[PullRequestImpactFile, ...],
        findings: tuple[PullRequestFinding, ...],
    ) -> tuple[str, ...]:
        recommendations = ["Review direct dependency neighbors before merging."]
        if changed_files and not any(self._is_test_path(path) for path in changed_files):
            recommendations.append("Add or update tests that cover the changed behavior.")
        if any(item.severity in {"high", "critical"} for item in findings):
            recommendations.append(
                "Resolve high-severity findings or document why they are acceptable."
            )
        if len(impacted_files) > len(changed_files):
            recommendations.append("Smoke test impacted import neighbors, not only changed files.")
        return tuple(dict.fromkeys(recommendations))

    def _summary(
        self,
        changed_files: tuple[str, ...],
        impacted_files: tuple[PullRequestImpactFile, ...],
        findings: tuple[PullRequestFinding, ...],
        risk_score: int,
    ) -> str:
        return (
            f"Reviewed {len(changed_files)} changed files with {len(impacted_files)} "
            f"impacted files and {len(findings)} findings. Risk score: {risk_score}."
        )

    def _confidence(
        self,
        changed_files: tuple[str, ...],
        findings: tuple[PullRequestFinding, ...],
    ) -> float:
        return min(0.92, 0.45 + min(len(changed_files), 5) * 0.07 + min(len(findings), 3) * 0.04)

    def _level(self, score: int) -> ReviewSeverity:
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"
