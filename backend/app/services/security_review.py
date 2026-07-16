import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService

SecuritySeverity = Literal["low", "medium", "high", "critical"]

MAX_FINDINGS = 40
MAX_REVIEWED_BYTES = 512_000
SECRET_NAME_PATTERN = re.compile(
    r"\b(api[_-]?key|auth[_-]?token|password|private[_-]?key|secret|token)\b",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(r"[:=]\s*['\"][^'\"]{8,}['\"]")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
SQL_PATTERN = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)


class SecurityReviewError(Exception):
    """Raised when security review cannot continue."""


@dataclass(frozen=True)
class SecurityFinding:
    """One security review finding."""

    category: str
    severity: SecuritySeverity
    path: str
    line: int
    title: str
    description: str
    evidence: tuple[str, ...]
    remediation: str


@dataclass(frozen=True)
class SecurityReviewStats:
    """Summary metrics for a security review."""

    changed_file_count: int
    reviewed_file_count: int
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_score: int
    risk_level: SecuritySeverity
    confidence: float


@dataclass(frozen=True)
class SecurityReview:
    """Grounded security review result."""

    repository_path: str
    focus: str | None
    changed_files: tuple[str, ...]
    findings: tuple[SecurityFinding, ...]
    recommendations: tuple[str, ...]
    summary: str
    stats: SecurityReviewStats


class SecurityReviewService:
    """Reviews changed files for practical security risks without executing code."""

    def __init__(self, scanner: RepositoryScannerService) -> None:
        self.scanner = scanner

    def review(
        self,
        repository_path: Path,
        changed_files: tuple[str, ...],
        focus: str | None = None,
    ) -> SecurityReview:
        """Review changed files for static security signals."""
        root = repository_path.expanduser().resolve()
        try:
            scan = self.scanner.scan(root)
        except RepositoryScanError as error:
            raise SecurityReviewError(str(error)) from error

        repository_files = tuple(file.path for file in scan.files)
        normalized_changed = self._changed_files(changed_files, repository_files)
        reviewable = tuple(path for path in normalized_changed if path in set(repository_files))
        findings: list[SecurityFinding] = []
        for relative_path in reviewable:
            path = root / relative_path
            if path.stat().st_size > MAX_REVIEWED_BYTES:
                findings.append(self._large_file_skipped(relative_path))
                continue
            findings.extend(self._findings_for_file(relative_path, path))

        ordered_findings = tuple(
            sorted(findings, key=lambda item: (severity_rank(item.severity), item.path, item.line))
        )[:MAX_FINDINGS]
        stats = self._stats(normalized_changed, reviewable, ordered_findings)
        return SecurityReview(
            repository_path=str(root),
            focus=focus,
            changed_files=normalized_changed,
            findings=ordered_findings,
            recommendations=self._recommendations(ordered_findings),
            summary=self._summary(normalized_changed, reviewable, ordered_findings, stats),
            stats=stats,
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

    def _findings_for_file(self, relative_path: str, path: Path) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        for index, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
            stripped = line.strip()
            findings.extend(self._line_findings(relative_path, index, stripped))
        return findings

    def _line_findings(self, path: str, line_number: int, line: str) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        if PRIVATE_KEY_PATTERN.search(line):
            findings.append(
                self._finding(
                    "hardcoded_private_key",
                    "critical",
                    path,
                    line_number,
                    "Private key material is committed",
                    "The changed file contains a private key marker.",
                    line,
                    "Remove the key, rotate it, and load credentials from a secret manager.",
                )
            )
        if SECRET_NAME_PATTERN.search(line) and SECRET_VALUE_PATTERN.search(line):
            findings.append(
                self._finding(
                    "hardcoded_secret",
                    "high",
                    path,
                    line_number,
                    "Hardcoded secret-like value",
                    "A credential-like name is assigned a literal value.",
                    line,
                    "Move the value to environment-backed configuration or a secret manager.",
                )
            )
        findings.extend(self._dangerous_execution(path, line_number, line))
        findings.extend(self._unsafe_deserialization(path, line_number, line))
        findings.extend(self._weak_crypto(path, line_number, line))
        findings.extend(self._transport_findings(path, line_number, line))
        findings.extend(self._sql_findings(path, line_number, line))
        findings.extend(self._memory_unsafe_findings(path, line_number, line))
        return findings

    def _dangerous_execution(self, path: str, line_number: int, line: str) -> list[SecurityFinding]:
        lowered = line.lower()
        risky = (
            "eval(" in line,
            "exec(" in line,
            "new function(" in lowered,
            "shell=true" in lowered,
            "child_process.exec" in line,
            "runtime.getruntime().exec" in lowered,
            "system(" in line,
        )
        if not any(risky):
            return []
        return [
            self._finding(
                "dangerous_code_execution",
                "high",
                path,
                line_number,
                "Dangerous code or command execution",
                "The changed line executes dynamic code or shell commands.",
                line,
                "Avoid dynamic execution; use explicit APIs and validate all command arguments.",
            )
        ]

    def _unsafe_deserialization(
        self, path: str, line_number: int, line: str
    ) -> list[SecurityFinding]:
        lowered = line.lower()
        unsafe_yaml = "yaml.load(" in lowered and "safeloader" not in lowered
        if not any(
            (
                unsafe_yaml,
                "pickle.load" in lowered,
                "pickle.loads" in lowered,
                "objectinputstream" in lowered,
            )
        ):
            return []
        return [
            self._finding(
                "unsafe_deserialization",
                "high",
                path,
                line_number,
                "Unsafe deserialization",
                "Untrusted serialized input can instantiate unexpected objects or code paths.",
                line,
                "Use safe parsers and typed validation before accepting serialized input.",
            )
        ]

    def _weak_crypto(self, path: str, line_number: int, line: str) -> list[SecurityFinding]:
        lowered = line.lower()
        if not any(
            (
                "md5(" in lowered,
                "sha1(" in lowered,
                "createhash('md5'" in lowered,
                'createhash("md5"' in lowered,
                "des.new" in lowered,
            )
        ):
            return []
        return [
            self._finding(
                "weak_crypto",
                "medium",
                path,
                line_number,
                "Weak cryptographic primitive",
                "The changed line uses a weak hash or cipher.",
                line,
                "Use modern primitives such as SHA-256, bcrypt, scrypt, Argon2, or AES-GCM.",
            )
        ]

    def _transport_findings(self, path: str, line_number: int, line: str) -> list[SecurityFinding]:
        lowered = line.lower().replace(" ", "")
        if not any(
            (
                "verify=false" in lowered,
                "rejectunauthorized:false" in lowered,
                "debug=true" in lowered,
                'allow_origins=["*"]' in lowered,
                "access-control-allow-origin" in lowered and "*" in lowered,
            )
        ):
            return []
        return [
            self._finding(
                "security_controls_disabled",
                "high",
                path,
                line_number,
                "Security control is weakened",
                "The changed line disables or broadens a runtime security control.",
                line,
                "Keep verification and restrictive origins enabled outside local development.",
            )
        ]

    def _sql_findings(self, path: str, line_number: int, line: str) -> list[SecurityFinding]:
        lowered = line.lower()
        dynamic_execute = "execute(" in lowered and SQL_PATTERN.search(line)
        if not dynamic_execute or not any(
            token in line for token in ("f'", 'f"', "+", "%", ".format(")
        ):
            return []
        return [
            self._finding(
                "dynamic_sql",
                "high",
                path,
                line_number,
                "Dynamic SQL construction",
                "SQL appears to be built with interpolation or concatenation.",
                line,
                "Use parameterized queries or query-builder bindings.",
            )
        ]

    def _memory_unsafe_findings(
        self, path: str, line_number: int, line: str
    ) -> list[SecurityFinding]:
        if not any(token in line for token in ("gets(", "strcpy(", "strcat(", "sprintf(")):
            return []
        return [
            self._finding(
                "unsafe_memory_api",
                "high",
                path,
                line_number,
                "Unsafe memory API",
                "The changed line uses a C/C++ API associated with buffer overflows.",
                line,
                "Use bounded alternatives and validate destination buffer sizes.",
            )
        ]

    def _finding(
        self,
        category: str,
        severity: SecuritySeverity,
        path: str,
        line_number: int,
        title: str,
        description: str,
        evidence: str,
        remediation: str,
    ) -> SecurityFinding:
        return SecurityFinding(
            category=category,
            severity=severity,
            path=path,
            line=line_number,
            title=title,
            description=description,
            evidence=(evidence[:160],),
            remediation=remediation,
        )

    def _large_file_skipped(self, path: str) -> SecurityFinding:
        return SecurityFinding(
            category="file_too_large",
            severity="low",
            path=path,
            line=1,
            title="Large file skipped",
            description="The changed file is too large for inline security review.",
            evidence=(f"larger than {MAX_REVIEWED_BYTES} bytes",),
            remediation="Run a dedicated security scanner for large generated or bundled files.",
        )

    def _recommendations(self, findings: tuple[SecurityFinding, ...]) -> tuple[str, ...]:
        recommendations = ["Review each finding with the changed line and surrounding context."]
        if any(finding.category.startswith("hardcoded") for finding in findings):
            recommendations.append("Rotate exposed credentials before merging.")
        if any(finding.category == "dynamic_sql" for finding in findings):
            recommendations.append("Add tests that prove parameterized query behavior.")
        if any(finding.severity in {"critical", "high"} for finding in findings):
            recommendations.append(
                "Block merge until high-severity security findings are resolved."
            )
        return tuple(dict.fromkeys(recommendations))

    def _summary(
        self,
        changed_files: tuple[str, ...],
        reviewed_files: tuple[str, ...],
        findings: tuple[SecurityFinding, ...],
        stats: SecurityReviewStats,
    ) -> str:
        return (
            f"Reviewed {len(reviewed_files)} of {len(changed_files)} changed files with "
            f"{len(findings)} security findings. Security risk score: {stats.risk_score}."
        )

    def _stats(
        self,
        changed_files: tuple[str, ...],
        reviewed_files: tuple[str, ...],
        findings: tuple[SecurityFinding, ...],
    ) -> SecurityReviewStats:
        risk_score = self._risk_score(findings)
        return SecurityReviewStats(
            changed_file_count=len(changed_files),
            reviewed_file_count=len(reviewed_files),
            finding_count=len(findings),
            critical_count=sum(1 for item in findings if item.severity == "critical"),
            high_count=sum(1 for item in findings if item.severity == "high"),
            medium_count=sum(1 for item in findings if item.severity == "medium"),
            low_count=sum(1 for item in findings if item.severity == "low"),
            risk_score=risk_score,
            risk_level=self._level(risk_score),
            confidence=min(0.94, 0.55 + min(len(reviewed_files), 5) * 0.05),
        )

    def _risk_score(self, findings: tuple[SecurityFinding, ...]) -> int:
        severity_points = {"low": 3, "medium": 10, "high": 24, "critical": 45}
        return min(sum(severity_points[finding.severity] for finding in findings), 100)

    def _level(self, score: int) -> SecuritySeverity:
        if score >= 80:
            return "critical"
        if score >= 55:
            return "high"
        if score >= 25:
            return "medium"
        return "low"


def severity_rank(severity: SecuritySeverity) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}[severity]
