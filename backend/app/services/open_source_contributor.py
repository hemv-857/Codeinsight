import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService

ContributionSeverity = Literal["low", "medium", "high", "critical"]
ContributionCategory = Literal[
    "bug",
    "security",
    "code_smell",
    "missing_test",
    "missing_docs",
    "performance",
    "accessibility",
    "api_design",
]

MAX_FINDINGS = 50
MAX_SCANNED_BYTES = 512_000

BUG_PATTERNS = [
    (re.compile(r"\bexcept\s*:\s*$", re.MULTILINE), "bare_except", "high"),
    (re.compile(r"except Exception\b"), "broad_except", "medium"),
    (re.compile(r"TODO|FIXME|HACK|XXX|BUG"), "todo_marker", "low"),
    (re.compile(r"\.has_key\(|in\s+\w+\s+and\s+\w+\s+in\s+\w+"), "redundant_check", "low"),
    (re.compile(r"==\s*None|None\s*=="), "none_comparison", "low"),
    (re.compile(r"\bprint\s*\("), "debug_print", "low"),
    (re.compile(r"pass\s*$", re.MULTILINE), "empty_block", "medium"),
    (re.compile(r"\bglobal\s+\w+"), "global_usage", "medium"),
    (re.compile(r"except\s+\w+Error\s*:\s*pass"), "swallowed_error", "high"),
]

SECURITY_PATTERNS = [
    (re.compile(r"eval\s*\("), "eval_usage", "critical"),
    (re.compile(r"exec\s*\("), "exec_usage", "critical"),
    (re.compile(r"shell\s*=\s*True"), "shell_true", "high"),
    (re.compile(r"subprocess\.call|os\.system|os\.popen"), "shell_command", "high"),
    (re.compile(r"pickle\.loads?\s*\("), "pickle_deserialize", "high"),
    (re.compile(r"yaml\.load\s*\((?!.*Loader)"), "unsafe_yaml", "high"),
    (re.compile(r"assert\s+"), "assert_in_code", "medium"),
    (re.compile(r"\bverify\s*=\s*False|VERIFY_NONE"), "ssl_disabled", "critical"),
]

CODE_SMELL_PATTERNS = [
    (re.compile(r"def\s+\w+\(.*\)\s*->\s*\w+.*:\s*\n\s+pass", re.MULTILINE), "empty_function"),
    (re.compile(r"class\s+\w+.*:\s*\n\s+pass\s*$", re.MULTILINE), "empty_class"),
    (re.compile(r"except\s+\w+.*:\s*\n\s+pass", re.MULTILINE), "swallowed_exception"),
    (re.compile(r"\bprint\s*\("), "print_statement"),
    (re.compile(r"^\s*#\s*type:\s*ignore", re.MULTILINE), "type_ignore"),
    (re.compile(r"\.encode\(['\"]utf-8['\"]\)", re.MULTILINE), "redundant_encoding"),
]

PERFORMANCE_PATTERNS = [
    (re.compile(r"for\s+\w+\s+in\s+.*:\s*\n\s+.*\.append\(", re.MULTILINE), "append_in_loop"),
    (re.compile(r"\+\=\s*['\"]|['\"]\s*\+="), "string_concat_loop"),
    (re.compile(r"import\s+\*"), "wildcard_import"),
]


class OpenSourceContributionError(Exception):
    """Raised when open source contribution analysis cannot continue."""


@dataclass(frozen=True)
class ContributionFinding:
    """One contribution finding with suggested fix."""

    category: ContributionCategory
    severity: ContributionSeverity
    path: str
    line: int
    title: str
    description: str
    evidence: tuple[str, ...]
    suggested_fix: str
    impact: str
    effort: str


@dataclass(frozen=True)
class ContributionStats:
    """Summary metrics for contribution analysis."""

    file_count: int
    scanned_file_count: int
    finding_count: int
    bug_count: int
    security_count: int
    code_smell_count: int
    missing_test_count: int
    missing_docs_count: int
    performance_count: int
    contribution_score: int
    confidence: float


@dataclass(frozen=True)
class OpenSourceContributionReport:
    """Open source contribution analysis result."""

    repository_path: str
    focus: str | None
    findings: tuple[ContributionFinding, ...]
    recommendations: tuple[str, ...]
    summary: str
    stats: ContributionStats


class OpenSourceContributionService:
    """Analyzes repository for open source contribution opportunities."""

    def __init__(self, scanner: RepositoryScannerService) -> None:
        self.scanner = scanner

    def analyze(
        self,
        repository_path: Path,
        focus: str | None = None,
    ) -> OpenSourceContributionReport:
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
        except RepositoryScanError as error:
            raise OpenSourceContributionError(str(error)) from error

        findings: list[ContributionFinding] = []
        scanned_count = 0

        for file_entry in scan.files:
            if file_entry.language is None:
                continue
            file_path = root / file_entry.path
            if file_path.stat().st_size > MAX_SCANNED_BYTES:
                continue
            try:
                content = file_path.read_text(errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            scanned_count += 1
            findings.extend(self._analyze_file(file_entry.path, content, file_entry.language))

        if focus:
            findings = [
                f
                for f in findings
                if focus.lower() in f.path.lower() or focus.lower() in f.title.lower()
            ]

        ordered = tuple(
            sorted(findings, key=lambda f: (_severity_rank(f.severity), f.path, f.line))
        )[:MAX_FINDINGS]

        stats = self._stats(scan, scanned_count, ordered)
        return OpenSourceContributionReport(
            repository_path=str(root),
            focus=focus,
            findings=ordered,
            recommendations=self._recommendations(ordered),
            summary=self._summary(scan, scanned_count, ordered, stats),
            stats=stats,
        )

    def analyze_github_url(
        self,
        github_url: str,
        focus: str | None = None,
    ) -> OpenSourceContributionReport:
        clone_url = self._validate_github_url(github_url)
        repo_name = Path(urlparse(clone_url).path).stem
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"forge_{repo_name}_"))
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--", clone_url, str(tmp_dir / repo_name)],
                check=True,
                capture_output=True,
                timeout=120,
            )
            repo_path = tmp_dir / repo_name
            if not repo_path.is_dir():
                raise OpenSourceContributionError("Failed to clone repository.")
            return self.analyze(repo_path, focus=focus)
        except subprocess.TimeoutExpired as error:
            raise OpenSourceContributionError("Repository clone timed out.") from error
        except subprocess.CalledProcessError as error:
            raise OpenSourceContributionError(
                f"Failed to clone repository: {error.stderr.decode(errors='ignore')[:200]}"
            ) from error
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _validate_github_url(self, url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("https", "http", ""):
            raise OpenSourceContributionError("Invalid URL scheme. Use https://github.com/...")
        if "github.com" not in (parsed.hostname or ""):
            raise OpenSourceContributionError("URL must be a GitHub repository URL.")
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 2:
            raise OpenSourceContributionError("URL must include owner and repository name.")
        return f"https://github.com/{path_parts[0]}/{path_parts[1]}.git"

    def _analyze_file(
        self, relative_path: str, content: str, language: str
    ) -> list[ContributionFinding]:
        findings: list[ContributionFinding] = []
        lines = content.splitlines()

        for pattern, category, severity in BUG_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                evidence_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                findings.append(
                    self._finding(
                        "bug",
                        severity,  # type: ignore[arg-type]
                        relative_path,
                        line_num,
                        self._bug_title(category),
                        self._bug_description(category),
                        evidence_line,
                        self._bug_fix(category),
                        "Prevents runtime errors",
                        "Trivial",
                    )
                )

        for pattern, category, severity in SECURITY_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                evidence_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                findings.append(
                    self._finding(
                        "security",
                        severity,  # type: ignore[arg-type]
                        relative_path,
                        line_num,
                        self._security_title(category),
                        self._security_description(category),
                        evidence_line,
                        self._security_fix(category),
                        "Reduces attack surface",
                        "Low" if severity == "medium" else "Medium",
                    )
                )

        for pattern, category in CODE_SMELL_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                evidence_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                findings.append(
                    self._finding(
                        "code_smell",
                        "low",
                        relative_path,
                        line_num,
                        self._smell_title(category),
                        self._smell_description(category),
                        evidence_line,
                        self._smell_fix(category),
                        "Improves code maintainability and readability",
                        "Trivial",
                    )
                )

        for pattern, category in PERFORMANCE_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                evidence_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                findings.append(
                    self._finding(
                        "performance",
                        "medium",
                        relative_path,
                        line_num,
                        self._perf_title(category),
                        self._perf_description(category),
                        evidence_line,
                        self._perf_fix(category),
                        "Improves runtime performance",
                        "Low",
                    )
                )

        findings.extend(self._check_missing_docs(relative_path, content, language))
        findings.extend(self._check_missing_tests(relative_path, scan_files=None))

        return findings

    def _check_missing_docs(
        self, path: str, content: str, language: str
    ) -> list[ContributionFinding]:
        findings: list[ContributionFinding] = []
        if language in ("Python",):
            if "'''" not in content and '"""' not in content and len(content.splitlines()) > 20:
                findings.append(
                    self._finding(
                        "missing_docs",
                        "low",
                        path,
                        1,
                        "No module docstring",
                        "Python module lacks a docstring explaining its purpose.",
                        "",
                        "Add a module-level docstring at the top of the file.",
                        "Helps contributors understand the module's purpose",
                        "Trivial",
                    )
                )
        return findings

    def _check_missing_tests(self, path: str, scan_files: None) -> list[ContributionFinding]:
        return []

    def _finding(
        self,
        category: ContributionCategory,
        severity: ContributionSeverity,
        path: str,
        line: int,
        title: str,
        description: str,
        evidence: str,
        suggested_fix: str,
        impact: str,
        effort: str,
    ) -> ContributionFinding:
        return ContributionFinding(
            category=category,
            severity=severity,
            path=path,
            line=line,
            title=title,
            description=description,
            evidence=(evidence[:200],) if evidence else (),
            suggested_fix=suggested_fix,
            impact=impact,
            effort=effort,
        )

    def _bug_title(self, category: str) -> str:
        titles = {
            "bare_except": "Bare except clause",
            "broad_except": "Broad exception handler",
            "todo_marker": "TODO/FIXME marker",
            "redundant_check": "Redundant membership check",
            "none_comparison": "Non-idiomatic None comparison",
            "debug_print": "Debug print statement",
            "empty_block": "Empty code block",
            "global_usage": "Global variable usage",
            "swallowed_error": "Silently swallowed error",
        }
        return titles.get(category, "Potential bug")

    def _bug_description(self, category: str) -> str:
        descriptions = {
            "bare_except": "Catches all exceptions including SystemExit.",
            "broad_except": "Catching Exception hides specific errors.",
            "todo_marker": "Unresolved TODO/FIXME marker.",
            "redundant_check": "Redundant membership check.",
            "none_comparison": "Use 'is None' instead of '== None'.",
            "debug_print": "Debug print left in code.",
            "empty_block": "Empty code block, possibly incomplete.",
            "global_usage": "Global variable usage.",
            "swallowed_error": "Exception caught and ignored.",
        }
        return descriptions.get(category, "Potential bug detected.")

    def _bug_fix(self, category: str) -> str:
        fixes = {
            "bare_except": "Replace with 'except Exception:'.",
            "broad_except": "Catch specific exceptions.",
            "todo_marker": "Address the TODO or create issue.",
            "redundant_check": "Use 'if key in dict:'.",
            "none_comparison": "Use 'is None' or 'is not None'.",
            "debug_print": "Replace with logging.debug().",
            "empty_block": "Implement or raise NotImplementedError.",
            "global_usage": "Use parameters or class attributes.",
            "swallowed_error": "Add logging or re-raise.",
        }
        return fixes.get(category, "Review and fix the issue.")

    def _security_title(self, category: str) -> str:
        titles = {
            "eval_usage": "Dynamic code evaluation",
            "exec_usage": "Dynamic code execution",
            "shell_true": "Shell execution enabled",
            "shell_command": "Shell command execution",
            "pickle_deserialize": "Unsafe pickle deserialization",
            "unsafe_yaml": "Unsafe YAML loading",
            "assert_in_code": "Assert used in non-test code",
            "ssl_disabled": "SSL verification disabled",
        }
        return titles.get(category, "Security issue")

    def _security_description(self, category: str) -> str:
        descriptions = {
            "eval_usage": "eval() executes arbitrary code.",
            "exec_usage": "exec() executes arbitrary code.",
            "shell_true": "shell=True allows injection.",
            "shell_command": "Direct shell execution.",
            "pickle_deserialize": "pickle can execute arbitrary code.",
            "unsafe_yaml": "yaml.load() can execute code.",
            "assert_in_code": "Asserts stripped with -O flag.",
            "ssl_disabled": "SSL verification disabled.",
        }
        return descriptions.get(category, "Security vulnerability detected.")

    def _security_fix(self, category: str) -> str:
        fixes = {
            "eval_usage": "Use ast.literal_eval() instead.",
            "exec_usage": "Use explicit function calls.",
            "shell_true": "Use subprocess with list args.",
            "shell_command": "Use subprocess with arg lists.",
            "pickle_deserialize": "Use JSON for serialization.",
            "unsafe_yaml": "Use yaml.safe_load().",
            "assert_in_code": "Use proper validation.",
            "ssl_disabled": "Enable SSL verification.",
        }
        return fixes.get(category, "Apply security best practices.")

    def _smell_title(self, category: str) -> str:
        titles = {
            "empty_function": "Empty function body",
            "empty_class": "Empty class definition",
            "swallowed_exception": "Swallowed exception",
            "print_statement": "Print statement in production code",
            "type_ignore": "Type ignore comment",
            "redundant_encoding": "Redundant UTF-8 encoding",
        }
        return titles.get(category, "Code smell")

    def _smell_description(self, category: str) -> str:
        descriptions = {
            "empty_function": "Function has no implementation, may be incomplete.",
            "empty_class": "Class has no methods or attributes.",
            "swallowed_exception": "Exception caught and ignored without logging.",
            "print_statement": "Print statement should use proper logging.",
            "type_ignore": "Type ignore comment suppresses type checking.",
            "redundant_encoding": "UTF-8 is the default encoding in Python 3.",
        }
        return descriptions.get(category, "Code smell detected.")

    def _smell_fix(self, category: str) -> str:
        fixes = {
            "empty_function": "Implement the function or raise NotImplementedError.",
            "empty_class": "Add methods and attributes, or remove if unused.",
            "swallowed_exception": "Add logging.exception() or re-raise the exception.",
            "print_statement": "Replace with logging.info(), logging.debug(), etc.",
            "type_ignore": "Fix the underlying type issue instead of suppressing it.",
            "redundant_encoding": "Remove .encode('utf-8') calls; use strings directly.",
        }
        return fixes.get(category, "Refactor to improve code quality.")

    def _perf_title(self, category: str) -> str:
        titles = {
            "append_in_loop": "Append in loop",
            "string_concat_loop": "String concatenation in loop",
            "wildcard_import": "Wildcard import",
        }
        return titles.get(category, "Performance issue")

    def _perf_description(self, category: str) -> str:
        descriptions = {
            "append_in_loop": "Use list comprehension instead.",
            "string_concat_loop": "Use join() instead of +=",
            "wildcard_import": "Import specific names.",
        }
        return descriptions.get(category, "Performance concern detected.")

    def _perf_fix(self, category: str) -> str:
        fixes = {
            "append_in_loop": "Use a list comprehension or generator expression instead.",
            "string_concat_loop": "Collect items in a list and use ''.join(items) at the end.",
            "wildcard_import": "Import specific names: 'from module import name1, name2'.",
        }
        return fixes.get(category, "Optimize for better performance.")

    def _stats(
        self, scan: object, scanned_count: int, findings: tuple[ContributionFinding, ...]
    ) -> ContributionStats:
        file_count = len(scan.files) if hasattr(scan, "files") else 0
        return ContributionStats(
            file_count=file_count,
            scanned_file_count=scanned_count,
            finding_count=len(findings),
            bug_count=sum(1 for f in findings if f.category == "bug"),
            security_count=sum(1 for f in findings if f.category == "security"),
            code_smell_count=sum(1 for f in findings if f.category == "code_smell"),
            missing_test_count=sum(1 for f in findings if f.category == "missing_test"),
            missing_docs_count=sum(1 for f in findings if f.category == "missing_docs"),
            performance_count=sum(1 for f in findings if f.category == "performance"),
            contribution_score=self._contribution_score(findings),
            confidence=min(0.92, 0.50 + min(scanned_count, 10) * 0.04),
        )

    def _contribution_score(self, findings: tuple[ContributionFinding, ...]) -> int:
        if not findings:
            return 95
        severity_weights = {"critical": 15, "high": 8, "medium": 3, "low": 1}
        penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        return max(5, min(95, 95 - penalty))

    def _recommendations(self, findings: tuple[ContributionFinding, ...]) -> tuple[str, ...]:
        recommendations = [
            "Review each finding in context before applying fixes.",
            "Run existing tests after making changes to prevent regressions.",
        ]
        if any(f.category == "security" for f in findings):
            recommendations.append("Prioritize security findings.")
        if any(f.category == "bug" for f in findings):
            recommendations.append("Fix bug findings before merging.")
        if any(f.category == "missing_docs" for f in findings):
            recommendations.append("Add docs to help contributors.")
        if any(f.category == "performance" for f in findings):
            recommendations.append("Consider performance benchmarks.")
        return tuple(dict.fromkeys(recommendations))

    def _summary(
        self,
        scan: object,
        scanned_count: int,
        findings: tuple[ContributionFinding, ...],
        stats: ContributionStats,
    ) -> str:
        file_count = len(scan.files) if hasattr(scan, "files") else 0
        return (
            f"Analyzed {scanned_count} of {file_count} files and found "
            f"{len(findings)} contribution opportunities. "
            f"Contribution readiness score: {stats.contribution_score}/100."
        )


def _severity_rank(severity: ContributionSeverity) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}[severity]
