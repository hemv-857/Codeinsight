import re
from dataclasses import dataclass
from pathlib import Path

from backend.app.services.repository_summary import (
    RepositorySummary,
    RepositorySummaryError,
    RepositorySummaryService,
    SummaryFile,
    SummarySymbol,
)

DEFAULT_CONFIDENCE = 0.82
FOCUSED_CONFIDENCE = 0.74
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


class ArchitectureExplanationError(Exception):
    """Raised when architecture explanation cannot continue."""


@dataclass(frozen=True)
class ArchitectureComponent:
    """A component surfaced in an architecture explanation."""

    name: str
    path: str
    role: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureExplanation:
    """Grounded architecture explanation for a repository."""

    repository_path: str
    focus: str | None
    overview: str
    components: tuple[ArchitectureComponent, ...]
    dependency_flow: tuple[str, ...]
    call_flow: tuple[str, ...]
    observations: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    confidence: float


class ArchitectureExplanationService:
    """Explains repository architecture using existing summary and graph evidence."""

    def __init__(self, summary_service: RepositorySummaryService) -> None:
        self.summary_service = summary_service

    def explain(
        self,
        repository_path: Path,
        focus: str | None = None,
    ) -> ArchitectureExplanation:
        normalized_focus = focus.strip() if focus is not None and focus.strip() else None
        try:
            summary = self.summary_service.summarize(repository_path)
        except RepositorySummaryError:
            raise
        except Exception as error:
            raise ArchitectureExplanationError(str(error)) from error

        key_files = self._focused_files(summary.key_files, summary.key_symbols, normalized_focus)
        key_symbols = self._focused_symbols(summary.key_symbols, normalized_focus)
        components = self._components(key_files, key_symbols)
        evidence_paths = tuple(
            dict.fromkeys(
                [component.path for component in components] + list(summary.evidence_paths)
            )
        )[:8]
        return ArchitectureExplanation(
            repository_path=summary.repository_path,
            focus=normalized_focus,
            overview=self._overview(summary, normalized_focus),
            components=components,
            dependency_flow=self._dependency_flow(summary),
            call_flow=self._call_flow(summary),
            observations=self._observations(summary),
            evidence_paths=evidence_paths,
            confidence=FOCUSED_CONFIDENCE if normalized_focus else DEFAULT_CONFIDENCE,
        )

    def _focused_files(
        self,
        files: tuple[SummaryFile, ...],
        symbols: tuple[SummarySymbol, ...],
        focus: str | None,
    ) -> tuple[SummaryFile, ...]:
        if focus is None:
            return files[:5]
        focus_tokens = self._tokens(focus)
        matching_paths = {
            symbol.path
            for symbol in symbols
            if focus_tokens.intersection(self._tokens(f"{symbol.name} {symbol.parent or ''}"))
        }
        focused = [
            file
            for file in files
            if file.path in matching_paths or focus_tokens.intersection(self._tokens(file.path))
        ]
        return tuple(focused[:5] if focused else files[:5])

    def _focused_symbols(
        self,
        symbols: tuple[SummarySymbol, ...],
        focus: str | None,
    ) -> tuple[SummarySymbol, ...]:
        if focus is None:
            return symbols
        focus_tokens = self._tokens(focus)
        focused = [
            symbol
            for symbol in symbols
            if focus_tokens.intersection(
                self._tokens(f"{symbol.name} {symbol.parent or ''} {symbol.path}")
            )
        ]
        return tuple(focused if focused else symbols)

    def _components(
        self,
        files: tuple[SummaryFile, ...],
        symbols: tuple[SummarySymbol, ...],
    ) -> tuple[ArchitectureComponent, ...]:
        symbols_by_path: dict[str, list[SummarySymbol]] = {}
        for symbol in symbols:
            symbols_by_path.setdefault(symbol.path, []).append(symbol)

        components: list[ArchitectureComponent] = []
        for file in files:
            file_symbols = symbols_by_path.get(file.path, [])[:3]
            symbol_names = ", ".join(symbol.name for symbol in file_symbols)
            role = self._role(file, symbol_names)
            components.append(
                ArchitectureComponent(
                    name=file.path,
                    path=file.path,
                    role=role,
                    evidence=tuple(
                        f"{symbol.kind} {symbol.name} at line {symbol.line}"
                        for symbol in file_symbols
                    ),
                )
            )
        return tuple(components)

    def _role(self, file: SummaryFile, symbol_names: str) -> str:
        parts = [f"{file.language or 'Source'} module"]
        if file.dependent_count:
            parts.append(f"used by {file.dependent_count} internal files")
        if file.dependency_count:
            parts.append(f"depends on {file.dependency_count} internal files")
        if symbol_names:
            parts.append(f"defines {symbol_names}")
        return "; ".join(parts) + "."

    def _overview(self, summary: RepositorySummary, focus: str | None) -> str:
        prefix = (
            f"For focus '{focus}', this architecture centers on"
            if focus
            else "This architecture centers on"
        )
        primary_language = summary.languages[0].language if summary.languages else "source"
        return (
            f"{prefix} {primary_language} source files with "
            f"{summary.stats.dependency_count} internal dependencies, "
            f"{summary.stats.callable_count} callable symbols, and "
            f"{summary.stats.call_count} observed call sites."
        )

    def _dependency_flow(self, summary: RepositorySummary) -> tuple[str, ...]:
        if summary.dependency_highlights:
            return summary.dependency_highlights
        return ("No internal dependency edges were detected from parsed imports.",)

    def _call_flow(self, summary: RepositorySummary) -> tuple[str, ...]:
        if summary.call_highlights:
            return summary.call_highlights
        return ("No call edges were detected from parsed call sites.",)

    def _observations(self, summary: RepositorySummary) -> tuple[str, ...]:
        observations = [
            f"{len(summary.key_files)} key source files explain the main structure.",
            f"{len(summary.key_symbols)} key symbols anchor the implementation.",
        ]
        if not summary.embedding_indexed:
            observations.append(
                "Embeddings are not indexed yet, so semantic retrieval is unavailable."
            )
        if summary.stats.skipped_parse_file_count:
            observations.append(
                f"{summary.stats.skipped_parse_file_count} source files could not be parsed."
            )
        return tuple(observations)

    def _tokens(self, text: str) -> set[str]:
        return set(TOKEN_PATTERN.findall(text.lower()))
