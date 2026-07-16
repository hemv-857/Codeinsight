from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_documentation_artifacts_exist() -> None:
    required_paths = [
        "README.md",
        "docs/architecture-diagrams.md",
        "docs/demo-repository.md",
        "docs/production-release.md",
        "docs/screenshots/dashboard.png",
    ]

    missing_paths = [path for path in required_paths if not (ROOT / path).is_file()]

    assert missing_paths == []


def test_release_documentation_covers_milestone_outputs() -> None:
    readme = (ROOT / "README.md").read_text()
    diagrams = (ROOT / "docs" / "architecture-diagrams.md").read_text()
    demo = (ROOT / "docs" / "demo-repository.md").read_text()
    release = (ROOT / "docs" / "production-release.md").read_text()

    assert "Dashboard screenshot" in readme
    assert "```mermaid" in diagrams
    assert "https://github.com/fastapi/fastapi" in demo
    assert "make verify" in release
