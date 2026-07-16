from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_milestone_one_foundation_files_exist() -> None:
    required_paths = {
        ".editorconfig",
        ".gitignore",
        ".prettierrc.json",
        "docker-compose.yml",
        "eslint.config.mjs",
        "Makefile",
        "package.json",
        "pyproject.toml",
        "requirements-dev.txt",
        "tsconfig.base.json",
    }

    missing_paths = sorted(path for path in required_paths if not (ROOT / path).is_file())

    assert missing_paths == []


def test_milestone_one_monorepo_directories_exist() -> None:
    required_directories = {
        "backend",
        "docker",
        "docs",
        "frontend",
        "graph",
        "parser",
        "shared",
        "tests",
        "workers",
    }

    missing_directories = sorted(
        path for path in required_directories if not (ROOT / path).is_dir()
    )

    assert missing_directories == []
