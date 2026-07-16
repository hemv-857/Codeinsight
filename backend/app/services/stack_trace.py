import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Literal

TraceLanguage = Literal["python", "javascript", "java", "go", "unknown"]

PYTHON_FRAME = re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<function>.+)$')
JAVASCRIPT_FRAME = re.compile(
    r"^\s*at (?:(?P<function>.+?) \()?(?P<file>(?:file://)?[^():]+):(?P<line>\d+):(?P<column>\d+)\)?$"
)
JAVA_FRAME = re.compile(r"^\s*at (?P<function>[\w.$<>]+)\((?P<file>[^():]+):(?P<line>\d+)\)$")
GO_FRAME = re.compile(r"^\s*(?P<file>[^:\s]+\.go):(?P<line>\d+)(?: \+\S+)?$")
ERROR_LINE = re.compile(r"^(?P<type>[\w.$]*Error|[\w.$]*Exception|panic)(?::\s*(?P<message>.*))?$")


class StackTraceParseError(Exception):
    """Raised when stack trace parsing cannot continue."""


@dataclass(frozen=True)
class StackTraceFrame:
    """One frame parsed from a stack trace."""

    file_path: str
    line: int
    column: int | None
    function: str | None
    language: TraceLanguage
    raw: str


@dataclass(frozen=True)
class StackTraceStats:
    """Summary counts for a parsed stack trace."""

    frame_count: int
    language: TraceLanguage
    file_count: int


@dataclass(frozen=True)
class StackTrace:
    """Parsed stack trace with normalized frames and error metadata."""

    raw: str
    language: TraceLanguage
    error_type: str | None
    message: str | None
    frames: tuple[StackTraceFrame, ...]
    files: tuple[str, ...]
    stats: StackTraceStats


class StackTraceParserService:
    """Parses common runtime stack trace formats into normalized frames."""

    def parse(self, raw_trace: str) -> StackTrace:
        trace = raw_trace.strip()
        if not trace:
            raise StackTraceParseError("Stack trace cannot be empty.")

        frames: list[StackTraceFrame] = []
        error_type: str | None = None
        message: str | None = None
        for line in trace.splitlines():
            parsed = self._frame(line)
            if parsed is not None:
                frames.append(parsed)
                continue
            error_match = ERROR_LINE.match(line.strip())
            if error_match is not None:
                error_type = error_match.group("type")
                message = error_match.group("message") or message

        language = self._language(frames)
        files = tuple(dict.fromkeys(frame.file_path for frame in frames))
        return StackTrace(
            raw=trace,
            language=language,
            error_type=error_type,
            message=message,
            frames=tuple(frames),
            files=files,
            stats=StackTraceStats(
                frame_count=len(frames),
                language=language,
                file_count=len(files),
            ),
        )

    def _frame(self, line: str) -> StackTraceFrame | None:
        python_match = PYTHON_FRAME.match(line)
        if python_match is not None:
            return self._matched_frame(line, "python", python_match)
        javascript_match = JAVASCRIPT_FRAME.match(line)
        if javascript_match is not None:
            return self._matched_frame(line, "javascript", javascript_match)
        java_match = JAVA_FRAME.match(line)
        if java_match is not None:
            return self._matched_frame(line, "java", java_match)
        go_match = GO_FRAME.match(line)
        if go_match is not None:
            return self._matched_frame(line, "go", go_match)
        return None

    def _matched_frame(
        self, raw: str, language: TraceLanguage, match: re.Match[str]
    ) -> StackTraceFrame:
        function = match.groupdict().get("function")
        column = match.groupdict().get("column")
        file_path = match.group("file").removeprefix("file://")
        return StackTraceFrame(
            file_path=self._normalize_file(file_path),
            line=int(match.group("line")),
            column=int(column) if column is not None else None,
            function=function.strip() if function else None,
            language=language,
            raw=raw.strip(),
        )

    def _language(self, frames: list[StackTraceFrame]) -> TraceLanguage:
        if not frames:
            return "unknown"
        counts: dict[TraceLanguage, int] = {frame.language: 0 for frame in frames}
        for frame in frames:
            counts[frame.language] += 1
        return max(counts, key=lambda language: counts[language])

    def _normalize_file(self, path: str) -> str:
        cleaned = path.strip()
        if cleaned.startswith("webpack://"):
            return cleaned
        return PurePath(cleaned).as_posix()
