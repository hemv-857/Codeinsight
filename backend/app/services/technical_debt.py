import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from graph.dependency_graph import DependencyGraphError, DependencyGraphService
from parser.tree_sitter_parser import SourceSymbol, TreeSitterParseError, TreeSitterParserService

from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService

DebtSeverity = Literal["low", "medium", "high", "critical"]

LARGE_FILE_LINES = 500
LONG_SYMBOL_LINES = 80
BROAD_TYPE_METHODS = 15
HIGH_FAN_OUT = 8
HIGH_COMPLEXITY = 10
CRITICAL_COMPLEXITY = 20
COMPLEXITY_TOKENS = (
    " if ",
    " elif ",
    " else if ",
    " for ",
    " while ",
    " case ",
    " catch ",
    " except ",
    "&&",
    "||",
    "?",
)

logger = logging.getLogger(__name__)


class TechnicalDebtError(Exception):
    """Raised when technical debt analysis cannot continue."""


@dataclass(frozen=True)
class TechnicalDebtFinding:
    """One technical debt finding discovered in a repository."""

    category: str
    severity: DebtSeverity
    path: str
    title: str
    description: str
    line: int | None = None
    end_line: int | None = None
    symbol_name: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class TechnicalDebtStats:
    """Summary counts for a technical debt analysis run."""

    file_count: int
    parsed_file_count: int
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    score: int
    average_complexity: float
    max_complexity: int
    complex_symbol_count: int


@dataclass(frozen=True)
class TechnicalDebtReport:
    """Technical debt report for one repository."""

    repository_path: str
    findings: tuple[TechnicalDebtFinding, ...]
    stats: TechnicalDebtStats


class TechnicalDebtService:
    """Analyzes repository source facts for practical technical debt signals."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        parser: TreeSitterParserService,
        dependency_graph: DependencyGraphService,
    ) -> None:
        self.scanner = scanner
        self.parser = parser
        self.dependency_graph = dependency_graph

    def analyze(self, repository_path: Path) -> TechnicalDebtReport:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
        except RepositoryScanError as error:
            raise TechnicalDebtError(str(error)) from error

        findings: list[TechnicalDebtFinding] = []
        complexities: list[int] = []
        parsed_file_count = 0
        for file in scan.files:
            path = root / file.path
            if file.language is None or not self.parser.supports_path(path):
                continue
            lines = path.read_text(errors="ignore").splitlines()
            findings.extend(self._file_size_findings(path, file.path))
            try:
                parsed = self.parser.parse_file(path)
            except TreeSitterParseError as error:
                findings.append(self._parse_error(file.path, str(error)))
                continue
            parsed_file_count += 1
            if parsed.has_error:
                findings.append(self._parse_error(file.path, "Tree-sitter reported syntax errors."))
            symbol_findings, symbol_complexities = self._symbol_findings(
                file.path, parsed.symbols, lines
            )
            findings.extend(symbol_findings)
            complexities.extend(symbol_complexities)

        findings.extend(self._dependency_findings(root))
        ordered_findings = tuple(
            sorted(
                findings, key=lambda item: (severity_rank(item.severity), item.path, item.line or 0)
            )
        )
        return TechnicalDebtReport(
            repository_path=str(root),
            findings=ordered_findings,
            stats=self._stats(
                scan_file_count=len(scan.files),
                parsed_file_count=parsed_file_count,
                findings=ordered_findings,
                complexities=complexities,
            ),
        )

    def _file_size_findings(self, path: Path, relative_path: str) -> list[TechnicalDebtFinding]:
        line_count = len(path.read_text(errors="ignore").splitlines())
        if line_count < LARGE_FILE_LINES:
            return []
        return [
            TechnicalDebtFinding(
                category="large_file",
                severity="medium" if line_count < LARGE_FILE_LINES * 2 else "high",
                path=relative_path,
                title="Large source file",
                description=f"{relative_path} has {line_count} lines.",
                evidence=(f"{line_count} lines",),
            )
        ]

    def _symbol_findings(
        self, path: str, symbols: tuple[SourceSymbol, ...], lines: list[str]
    ) -> tuple[list[TechnicalDebtFinding], list[int]]:
        findings: list[TechnicalDebtFinding] = []
        complexities: list[int] = []
        methods_by_parent = Counter(
            symbol.parent for symbol in symbols if symbol.kind == "method" and symbol.parent
        )
        for symbol in symbols:
            line_count = max(symbol.end_line - symbol.line + 1, 1)
            if symbol.kind in {"function", "method"} and line_count >= LONG_SYMBOL_LINES:
                findings.append(
                    TechnicalDebtFinding(
                        category="long_symbol",
                        severity="medium" if line_count < LONG_SYMBOL_LINES * 2 else "high",
                        path=path,
                        line=symbol.line,
                        end_line=symbol.end_line,
                        symbol_name=symbol.name,
                        title="Long function or method",
                        description=f"{symbol.name} spans {line_count} lines.",
                        evidence=(f"{line_count} lines", symbol.kind),
                    )
                )
            if symbol.kind in {"function", "method"}:
                complexity = self._complexity(symbol, lines)
                complexities.append(complexity)
                if complexity >= HIGH_COMPLEXITY:
                    severity: DebtSeverity = (
                        "critical" if complexity >= CRITICAL_COMPLEXITY else "high"
                    )
                    findings.append(
                        TechnicalDebtFinding(
                            category="high_complexity",
                            severity=severity,
                            path=path,
                            line=symbol.line,
                            end_line=symbol.end_line,
                            symbol_name=symbol.name,
                            title="High cyclomatic complexity",
                            description=f"{symbol.name} has estimated complexity {complexity}.",
                            evidence=(f"complexity {complexity}", symbol.kind),
                        )
                    )
            if (
                symbol.kind in {"class", "interface"}
                and methods_by_parent[symbol.name] >= BROAD_TYPE_METHODS
            ):
                findings.append(
                    TechnicalDebtFinding(
                        category="broad_type",
                        severity="medium",
                        path=path,
                        line=symbol.line,
                        end_line=symbol.end_line,
                        symbol_name=symbol.name,
                        title="Broad class or interface",
                        description=(
                            f"{symbol.name} defines {methods_by_parent[symbol.name]} methods."
                        ),
                        evidence=(f"{methods_by_parent[symbol.name]} methods",),
                    )
                )
        return findings, complexities

    def _complexity(self, symbol: SourceSymbol, lines: list[str]) -> int:
        source = "\n".join(lines[max(symbol.line - 1, 0) : symbol.end_line]).lower()
        return 1 + sum(source.count(token) for token in COMPLEXITY_TOKENS)

    def _dependency_findings(self, root: Path) -> list[TechnicalDebtFinding]:
        try:
            graph = self.dependency_graph.build(root)
        except DependencyGraphError as error:
            logger.warning("Dependency graph unavailable for technical debt analysis: %s", error)
            return []

        findings: list[TechnicalDebtFinding] = []
        fan_out = Counter(edge.source for edge in graph.edges if edge.target is not None)
        for path, count in fan_out.items():
            if count >= HIGH_FAN_OUT:
                findings.append(
                    TechnicalDebtFinding(
                        category="high_fan_out",
                        severity="medium",
                        path=path,
                        title="High dependency fan-out",
                        description=f"{path} imports {count} internal files.",
                        evidence=(f"{count} internal dependencies",),
                    )
                )
        for cycle in graph.circular_dependencies:
            findings.append(
                TechnicalDebtFinding(
                    category="dependency_cycle",
                    severity="high",
                    path=cycle[0],
                    title="Circular dependency",
                    description="Circular dependency detected between source files.",
                    evidence=cycle,
                )
            )
        return findings

    def _parse_error(self, path: str, detail: str) -> TechnicalDebtFinding:
        return TechnicalDebtFinding(
            category="parse_error",
            severity="high",
            path=path,
            title="Parser error",
            description=detail,
        )

    def _stats(
        self,
        scan_file_count: int,
        parsed_file_count: int,
        findings: tuple[TechnicalDebtFinding, ...],
        complexities: list[int],
    ) -> TechnicalDebtStats:
        counts = Counter(finding.severity for finding in findings)
        score = max(
            0,
            100
            - (counts["critical"] * 20)
            - (counts["high"] * 12)
            - (counts["medium"] * 6)
            - (counts["low"] * 2),
        )
        return TechnicalDebtStats(
            file_count=scan_file_count,
            parsed_file_count=parsed_file_count,
            finding_count=len(findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            score=score,
            average_complexity=(
                round(sum(complexities) / len(complexities), 2) if complexities else 0.0
            ),
            max_complexity=max(complexities, default=0),
            complex_symbol_count=sum(
                1 for complexity in complexities if complexity >= HIGH_COMPLEXITY
            ),
        )


def severity_rank(severity: DebtSeverity) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}[severity]
