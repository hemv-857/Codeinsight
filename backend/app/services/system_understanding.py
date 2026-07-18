from dataclasses import dataclass
from pathlib import Path

from backend.app.services.architecture_explanation import (
    ArchitectureExplanationError,
    ArchitectureExplanationService,
)
from backend.app.services.mermaid_diagrams import (
    MermaidDiagram,
    MermaidDiagramError,
    MermaidDiagramService,
)
from backend.app.services.repository_summary import (
    RepositorySummary,
    RepositorySummaryError,
    RepositorySummaryService,
    SummarySymbol,
)

MAX_REPORT_ITEMS = 8
SERVICE_TOKENS = ("service", "router", "controller", "client", "repository", "manager")
DATABASE_TOKENS = ("db", "database", "sql", "model", "migration", "repository", "schema")


class SystemUnderstandingError(Exception):
    """Raised when system understanding generation cannot continue."""


@dataclass(frozen=True)
class UnderstandingComponent:
    """A main component in the generated system understanding report."""

    name: str
    path: str
    role: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class UnderstandingFile:
    """An important file surfaced by the system understanding report."""

    path: str
    language: str | None
    reason: str
    score: int


@dataclass(frozen=True)
class UnderstandingSymbol:
    """A related symbol surfaced by the system understanding report."""

    name: str
    kind: str
    path: str
    line: int
    reason: str


@dataclass(frozen=True)
class SystemUnderstandingStats:
    """Measurable report generation statistics."""

    file_count: int
    parsed_file_count: int
    symbol_count: int
    dependency_count: int
    call_count: int
    diagram_count: int
    confidence: float


@dataclass(frozen=True)
class SystemUnderstandingReport:
    """Interactive repository understanding report grounded in code intelligence."""

    repository_path: str
    title: str
    application_overview: str
    architecture_summary: str
    main_components: tuple[UnderstandingComponent, ...]
    critical_execution_flows: tuple[str, ...]
    important_services: tuple[UnderstandingSymbol, ...]
    database_interactions: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    high_risk_modules: tuple[UnderstandingFile, ...]
    suggested_learning_path: tuple[str, ...]
    architecture_diagram: str
    dependency_visualization: str
    important_files: tuple[UnderstandingFile, ...]
    related_symbols: tuple[UnderstandingSymbol, ...]
    evidence_paths: tuple[str, ...]
    markdown: str
    stats: SystemUnderstandingStats


class SystemUnderstandingService:
    """Builds a one-click system understanding report from repository graph intelligence."""

    def __init__(
        self,
        summary_service: RepositorySummaryService,
        architecture_service: ArchitectureExplanationService,
        mermaid_service: MermaidDiagramService,
    ) -> None:
        self.summary_service = summary_service
        self.architecture_service = architecture_service
        self.mermaid_service = mermaid_service

    def generate(self, repository_path: Path) -> SystemUnderstandingReport:
        """Generate a grounded system understanding report for a repository path."""
        try:
            summary = self.summary_service.summarize(repository_path)
            architecture = self.architecture_service.explain(repository_path)
            diagrams = self.mermaid_service.generate(repository_path)
        except (
            RepositorySummaryError,
            ArchitectureExplanationError,
            MermaidDiagramError,
        ) as error:
            raise SystemUnderstandingError(str(error)) from error
        except Exception as error:
            raise SystemUnderstandingError(str(error)) from error

        important_files = self._important_files(summary)
        related_symbols = self._related_symbols(summary)
        important_services = self._important_services(related_symbols)
        database_interactions = self._database_interactions(summary)
        high_risk_modules = self._high_risk_modules(important_files)
        learning_path = self._learning_path(summary, important_files, important_services)
        architecture_diagram = self._diagram_code(diagrams.diagrams, "architecture")
        dependency_visualization = self._diagram_code(diagrams.diagrams, "dependency")
        report = SystemUnderstandingReport(
            repository_path=summary.repository_path,
            title=f"{Path(summary.repository_path).name or 'Repository'} System Understanding",
            application_overview=summary.overview,
            architecture_summary=architecture.overview,
            main_components=tuple(
                UnderstandingComponent(
                    name=component.name,
                    path=component.path,
                    role=component.role,
                    evidence=component.evidence,
                )
                for component in architecture.components[:MAX_REPORT_ITEMS]
            ),
            critical_execution_flows=self._fallback_items(
                architecture.call_flow,
                "No critical execution flow was resolved from parsed call sites.",
            ),
            important_services=important_services,
            database_interactions=database_interactions,
            external_dependencies=summary.dependency_highlights[:MAX_REPORT_ITEMS],
            high_risk_modules=high_risk_modules,
            suggested_learning_path=learning_path,
            architecture_diagram=architecture_diagram,
            dependency_visualization=dependency_visualization,
            important_files=important_files,
            related_symbols=related_symbols,
            evidence_paths=tuple(
                dict.fromkeys(
                    list(summary.evidence_paths)
                    + [file.path for file in important_files]
                    + [symbol.path for symbol in related_symbols]
                )
            )[:MAX_REPORT_ITEMS],
            markdown="",
            stats=SystemUnderstandingStats(
                file_count=summary.stats.file_count,
                parsed_file_count=summary.stats.parsed_file_count,
                symbol_count=summary.stats.symbol_count,
                dependency_count=summary.stats.dependency_count,
                call_count=summary.stats.call_count,
                diagram_count=diagrams.stats.diagram_count,
                confidence=architecture.confidence,
            ),
        )
        return self._with_markdown(report)

    def _important_files(self, summary: RepositorySummary) -> tuple[UnderstandingFile, ...]:
        return tuple(
            UnderstandingFile(
                path=file.path,
                language=file.language,
                reason=(
                    f"{file.symbol_count} symbols, {file.dependency_count} dependencies, "
                    f"{file.dependent_count} dependents"
                ),
                score=file.symbol_count + file.dependency_count + file.dependent_count,
            )
            for file in summary.key_files[:MAX_REPORT_ITEMS]
        )

    def _related_symbols(self, summary: RepositorySummary) -> tuple[UnderstandingSymbol, ...]:
        return tuple(
            UnderstandingSymbol(
                name=symbol.name,
                kind=symbol.kind,
                path=symbol.path,
                line=symbol.line,
                reason=f"Key {symbol.kind} surfaced by repository summary.",
            )
            for symbol in summary.key_symbols[:MAX_REPORT_ITEMS]
        )

    def _important_services(
        self,
        symbols: tuple[UnderstandingSymbol, ...],
    ) -> tuple[UnderstandingSymbol, ...]:
        services = [
            symbol
            for symbol in symbols
            if any(token in f"{symbol.name} {symbol.path}".lower() for token in SERVICE_TOKENS)
        ]
        return tuple(services[:MAX_REPORT_ITEMS] or symbols[: min(3, len(symbols))])

    def _database_interactions(self, summary: RepositorySummary) -> tuple[str, ...]:
        paths = [
            file.path
            for file in summary.key_files
            if any(token in file.path.lower() for token in DATABASE_TOKENS)
        ]
        symbols = [
            self._symbol_label(symbol)
            for symbol in summary.key_symbols
            if any(token in f"{symbol.name} {symbol.path}".lower() for token in DATABASE_TOKENS)
        ]
        interactions = tuple(dict.fromkeys(paths + symbols))[:MAX_REPORT_ITEMS]
        if interactions:
            return interactions
        return ("No database-specific files or symbols were detected in key repository evidence.",)

    def _high_risk_modules(
        self,
        files: tuple[UnderstandingFile, ...],
    ) -> tuple[UnderstandingFile, ...]:
        return tuple(sorted(files, key=lambda file: file.score, reverse=True)[:5])

    def _learning_path(
        self,
        summary: RepositorySummary,
        files: tuple[UnderstandingFile, ...],
        services: tuple[UnderstandingSymbol, ...],
    ) -> tuple[str, ...]:
        primary_language = summary.languages[0].language if summary.languages else "source"
        first_file = files[0].path if files else "the repository root"
        first_service = services[0].name if services else "the main exported symbols"
        return (
            f"Start with the {primary_language} layout and repository scan metrics.",
            f"Read `{first_file}` to anchor the application entry points.",
            f"Trace `{first_service}` through dependency and call-flow evidence.",
            "Review high-risk modules before making broad changes.",
            "Use the generated diagrams to follow dependency direction before editing.",
        )

    def _diagram_code(
        self,
        diagrams: tuple[MermaidDiagram, ...],
        kind: str,
    ) -> str:
        for diagram in diagrams:
            if diagram.kind == kind:
                return diagram.code
        return 'flowchart TD\n  missing["Diagram unavailable"]'

    def _fallback_items(self, items: tuple[str, ...], fallback: str) -> tuple[str, ...]:
        return items[:MAX_REPORT_ITEMS] if items else (fallback,)

    def _symbol_label(self, symbol: SummarySymbol) -> str:
        return f"{symbol.kind} `{symbol.name}` in `{symbol.path}` line {symbol.line}"

    def _with_markdown(self, report: SystemUnderstandingReport) -> SystemUnderstandingReport:
        markdown = "\n\n".join(
            [
                f"# {report.title}",
                f"## Application Overview\n\n{report.application_overview}",
                f"## Architecture Summary\n\n{report.architecture_summary}",
                f"## Main Components\n\n{self._component_markdown(report.main_components)}",
                f"## Critical Execution Flows\n\n"
                f"{self._list_markdown(report.critical_execution_flows)}",
                f"## Important Services\n\n{self._symbol_markdown(report.important_services)}",
                f"## Database Interactions\n\n{self._list_markdown(report.database_interactions)}",
                f"## High-Risk Modules\n\n{self._file_markdown(report.high_risk_modules)}",
                f"## Suggested Learning Path\n\n"
                f"{self._list_markdown(report.suggested_learning_path)}",
                "## Evidence\n\n"
                f"{self._list_markdown(tuple(f'`{path}`' for path in report.evidence_paths))}",
            ]
        )
        return SystemUnderstandingReport(**{**report.__dict__, "markdown": f"{markdown}\n"})

    def _component_markdown(self, components: tuple[UnderstandingComponent, ...]) -> str:
        if not components:
            return "No components were identified."
        return "\n".join(f"- `{component.path}`: {component.role}" for component in components)

    def _file_markdown(self, files: tuple[UnderstandingFile, ...]) -> str:
        if not files:
            return "No files were identified."
        return "\n".join(f"- `{file.path}`: {file.reason}" for file in files)

    def _symbol_markdown(self, symbols: tuple[UnderstandingSymbol, ...]) -> str:
        if not symbols:
            return "No symbols were identified."
        return "\n".join(
            f"- `{symbol.name}` ({symbol.kind}) in `{symbol.path}` line {symbol.line}"
            for symbol in symbols
        )

    def _list_markdown(self, items: tuple[str, ...]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "No signals were available."
