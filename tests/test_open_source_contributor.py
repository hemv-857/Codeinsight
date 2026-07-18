import subprocess
from pathlib import Path

import pytest
from backend.app.services.open_source_contributor import (
    OpenSourceContributionError,
    OpenSourceContributionService,
)
from backend.app.services.repository_scanner import RepositoryScannerService


def test_open_source_contributor_finds_ranked_opportunities(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text(
        "\n".join(
            [
                "import pickle",
                "",
                "def risky(value):",
                "    result = ''",
                "    for item in value:",
                "        result += item",
                "    data = []",
                "    for item in value:",
                "        data.append(item)",
                "    if value == None:",
                "        print('debug')",
                "    eval(value)",
                "    pickle.loads(value)",
                "    try:",
                "        pass",
                "    except ValueError: pass",
                "    assert value",
                "    return result",
            ]
        )
    )

    report = OpenSourceContributionService(RepositoryScannerService()).analyze(tmp_path)

    assert report.repository_path == str(tmp_path.resolve())
    assert report.stats.file_count == 1
    assert report.stats.scanned_file_count == 1
    assert report.stats.finding_count == len(report.findings)
    assert report.stats.security_count >= 3
    assert report.stats.bug_count >= 3
    assert report.stats.performance_count >= 1
    assert report.stats.contribution_score < 95
    assert report.findings[0].severity == "critical"
    assert "Prioritize security findings." in report.recommendations
    assert "Contribution readiness score" in report.summary


def test_open_source_contributor_focus_filters_findings(tmp_path: Path) -> None:
    (tmp_path / "bug.py").write_text("def bug():\n    print('debug')\n")
    (tmp_path / "safe.py").write_text("def safe():\n    return 1\n")

    report = OpenSourceContributionService(RepositoryScannerService()).analyze(
        tmp_path, focus="Print"
    )

    assert report.focus == "Print"
    assert report.findings
    assert all("print" in finding.title.lower() for finding in report.findings)


def test_open_source_contributor_validates_github_urls() -> None:
    service = OpenSourceContributionService(RepositoryScannerService())

    assert (
        service._validate_github_url("https://github.com/openai/codex")
        == "https://github.com/openai/codex.git"
    )
    with pytest.raises(OpenSourceContributionError, match="Invalid URL scheme"):
        service._validate_github_url("ssh://github.com/openai/codex")
    with pytest.raises(OpenSourceContributionError, match="GitHub repository"):
        service._validate_github_url("https://example.com/openai/codex")
    with pytest.raises(OpenSourceContributionError, match="owner and repository"):
        service._validate_github_url("https://github.com/openai")


def test_open_source_contributor_reports_clone_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_clone(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, ["git"], stderr=b"not found")

    monkeypatch.setattr(subprocess, "run", fail_clone)

    with pytest.raises(OpenSourceContributionError, match="Failed to clone repository"):
        OpenSourceContributionService(RepositoryScannerService()).analyze_github_url(
            "https://github.com/openai/codex"
        )
