from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from graph.dependency_graph import DependencyEdge, DependencyGraphError, DependencyGraphService

from backend.app.services.repository_import import RepositoryImportError
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService
from backend.app.services.stack_trace import (
    StackTrace,
    StackTraceParseError,
    StackTraceParserService,
)


class BugImpactError(Exception):
    """Raised when bug impact prediction cannot continue."""


@dataclass(frozen=True)
class ImpactedFile:
    """One file likely involved in or affected by a bug."""

    path: str
    reason: str
    score: float


@dataclass(frozen=True)
class RootCauseCandidate:
    """Likely bug source inferred from stack trace and repository graph evidence."""

    path: str
    line: int | None
    function: str | None
    score: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class BugImpactStats:
    """Summary metrics for a bug impact prediction."""

    frame_count: int
    matched_frame_count: int
    impacted_file_count: int
    dependency_edge_count: int
    risk_score: int
    confidence: float


@dataclass(frozen=True)
class BugImpactPrediction:
    """Grounded bug impact prediction for one repository and stack trace."""

    repository_path: str
    error_type: str | None
    message: str | None
    root_cause: RootCauseCandidate | None
    impacted_files: tuple[ImpactedFile, ...]
    recommendations: tuple[str, ...]
    parsed_trace: StackTrace
    stats: BugImpactStats


class BugImpactService:
    """Predicts likely bug impact from stack traces and repository dependency graph."""

    def __init__(
        self,
        scanner: RepositoryScannerService,
        dependency_graph: DependencyGraphService,
        stack_trace_parser: StackTraceParserService,
    ) -> None:
        self.scanner = scanner
        self.dependency_graph = dependency_graph
        self.stack_trace_parser = stack_trace_parser

    def predict(
        self,
        repository_path: Path,
        stack_trace: str,
        changed_files: tuple[str, ...] = (),
        error: str | None = None,
    ) -> BugImpactPrediction:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
            graph = self.dependency_graph.build(root)
            parsed_trace = self.stack_trace_parser.parse(stack_trace)
        except (RepositoryScanError, DependencyGraphError, StackTraceParseError) as exc:
            raise BugImpactError(str(exc)) from exc
        except RepositoryImportError as exc:
            raise BugImpactError(str(exc)) from exc

        repository_files = tuple(file.path for file in scan.files)
        frame_matches = {
            index: self._match_file(frame.file_path, repository_files)
            for index, frame in enumerate(parsed_trace.frames)
        }
        matched_paths = tuple(path for path in frame_matches.values() if path is not None)
        normalized_changed = tuple(
            path
            for path in (self._match_file(item, repository_files) for item in changed_files)
            if path
        )
        root_cause = self._root_cause(parsed_trace, frame_matches, normalized_changed)
        impacted_files = self._impacted_files(
            matched_paths=matched_paths,
            changed_files=normalized_changed,
            edges=graph.edges,
        )
        risk_score = min(100, 20 + len(impacted_files) * 8 + len(matched_paths) * 6)
        confidence = self._confidence(parsed_trace, matched_paths, root_cause)
        recommendations = self._recommendations(
            root_cause, impacted_files, error or parsed_trace.message
        )
        return BugImpactPrediction(
            repository_path=str(root),
            error_type=parsed_trace.error_type,
            message=error or parsed_trace.message,
            root_cause=root_cause,
            impacted_files=impacted_files,
            recommendations=recommendations,
            parsed_trace=parsed_trace,
            stats=BugImpactStats(
                frame_count=parsed_trace.stats.frame_count,
                matched_frame_count=len(matched_paths),
                impacted_file_count=len(impacted_files),
                dependency_edge_count=graph.stats.internal_dependency_count,
                risk_score=risk_score,
                confidence=confidence,
            ),
        )

    def _match_file(self, trace_path: str, repository_files: tuple[str, ...]) -> str | None:
        normalized = PurePosixPath(trace_path).as_posix().lstrip("./")
        for path in repository_files:
            if normalized == path or normalized.endswith(f"/{path}"):
                return path
        basename_matches = [
            path
            for path in repository_files
            if PurePosixPath(path).name == PurePosixPath(normalized).name
        ]
        return basename_matches[0] if len(basename_matches) == 1 else None

    def _root_cause(
        self,
        parsed_trace: StackTrace,
        frame_matches: dict[int, str | None],
        changed_files: tuple[str, ...],
    ) -> RootCauseCandidate | None:
        frame_indexes = tuple(range(len(parsed_trace.frames)))
        if parsed_trace.language in {"python", "java", "go"}:
            frame_indexes = tuple(reversed(frame_indexes))
        for index in frame_indexes:
            frame = parsed_trace.frames[index]
            path = frame_matches[index]
            if path is None:
                continue
            evidence = ["matched stack frame"]
            if path in changed_files:
                evidence.append("file was recently changed")
            score = 0.9 if path in changed_files else max(0.55, 0.85 - index * 0.08)
            return RootCauseCandidate(
                path=path,
                line=frame.line,
                function=frame.function,
                score=score,
                evidence=tuple(evidence),
            )
        if changed_files:
            return RootCauseCandidate(
                path=changed_files[0],
                line=None,
                function=None,
                score=0.5,
                evidence=("file was recently changed",),
            )
        return None

    def _impacted_files(
        self,
        matched_paths: tuple[str, ...],
        changed_files: tuple[str, ...],
        edges: tuple[DependencyEdge, ...],
    ) -> tuple[ImpactedFile, ...]:
        seed_paths = tuple(dict.fromkeys((*matched_paths, *changed_files)))
        impacted: dict[str, ImpactedFile] = {}
        for path in seed_paths:
            impacted[path] = ImpactedFile(
                path=path, reason="stack trace or changed file", score=0.95
            )
        for edge in edges:
            if edge.target in seed_paths:
                impacted.setdefault(
                    edge.source,
                    ImpactedFile(
                        path=edge.source,
                        reason=f"imports impacted file {edge.target}",
                        score=0.72,
                    ),
                )
            if edge.source in seed_paths and edge.target is not None:
                impacted.setdefault(
                    edge.target,
                    ImpactedFile(
                        path=edge.target,
                        reason=f"imported by impacted file {edge.source}",
                        score=0.62,
                    ),
                )
        return tuple(sorted(impacted.values(), key=lambda item: (-item.score, item.path)))

    def _confidence(
        self,
        parsed_trace: StackTrace,
        matched_paths: tuple[str, ...],
        root_cause: RootCauseCandidate | None,
    ) -> float:
        if root_cause is None:
            return 0.2
        if parsed_trace.stats.frame_count == 0:
            return 0.35
        return min(0.95, 0.45 + len(matched_paths) / parsed_trace.stats.frame_count * 0.4)

    def _recommendations(
        self,
        root_cause: RootCauseCandidate | None,
        impacted_files: tuple[ImpactedFile, ...],
        error: str | None,
    ) -> tuple[str, ...]:
        recommendations: list[str] = []
        if root_cause is not None:
            location = (
                f"{root_cause.path}:{root_cause.line}" if root_cause.line else root_cause.path
            )
            recommendations.append(f"Inspect {location} first; it is the top matched frame.")
        if error:
            recommendations.append(f"Reproduce the failure around error: {error}")
        if impacted_files:
            recommendations.append(
                "Review direct import neighbors before changing the suspected file."
            )
        return tuple(recommendations)
