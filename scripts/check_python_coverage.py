import argparse
import ast
import sys
import trace
from pathlib import Path

import pytest

SOURCE_DIRECTORIES = (
    "backend/app/repositories",
    "backend/app/services",
    "graph",
    "parser",
    "workers",
)
DEFAULT_MINIMUM = 90.0
OMITTED_FILES = frozenset({"__init__.py", "main.py"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest with first-party coverage checks.")
    parser.add_argument("--min", type=float, default=DEFAULT_MINIMUM, dest="minimum")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix, sys.base_prefix])
    namespace = {"pytest": pytest}
    tracer.runctx('result = pytest.main(["-q"])', namespace, namespace)
    pytest_status = int(namespace["result"])

    report = coverage_report(root=root, counts=tracer.results().counts)
    print(
        "\nPython coverage: "
        f"{report.covered_lines}/{report.total_lines} lines "
        f"({report.percent:.2f}%, minimum {args.minimum:.2f}%)"
    )
    if report.percent < args.minimum:
        print("\nLowest covered first-party files:")
        for row in report.lowest_files[:10]:
            print(f"{row.percent:6.2f}% {row.covered_lines:4}/{row.total_lines:<4} {row.path}")
        return 1
    return pytest_status


class CoverageFile:
    def __init__(self, path: str, covered_lines: int, total_lines: int) -> None:
        self.path = path
        self.covered_lines = covered_lines
        self.total_lines = total_lines

    @property
    def percent(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return self.covered_lines / self.total_lines * 100


class CoverageReport:
    def __init__(self, files: list[CoverageFile]) -> None:
        self.files = files
        self.covered_lines = sum(file.covered_lines for file in files)
        self.total_lines = sum(file.total_lines for file in files)

    @property
    def percent(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return self.covered_lines / self.total_lines * 100

    @property
    def lowest_files(self) -> list[CoverageFile]:
        return sorted(self.files, key=lambda file: (file.percent, file.path))


def coverage_report(root: Path, counts: dict[tuple[str, int], int]) -> CoverageReport:
    covered_by_file: dict[str, set[int]] = {}
    for (filename, line_number), count in counts.items():
        if count <= 0:
            continue
        covered_by_file.setdefault(str(Path(filename).resolve()), set()).add(line_number)

    files: list[CoverageFile] = []
    for path in source_files(root):
        executable_lines = executable_statement_lines(path)
        covered_lines = covered_by_file.get(str(path.resolve()), set())
        files.append(
            CoverageFile(
                path=path.relative_to(root).as_posix(),
                covered_lines=len(executable_lines & covered_lines),
                total_lines=len(executable_lines),
            )
        )
    return CoverageReport(files)


def source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in SOURCE_DIRECTORIES:
        files.extend(
            path
            for path in (root / directory).rglob("*.py")
            if "__pycache__" not in path.parts and path.name not in OMITTED_FILES
        )
    return sorted(files)


def executable_statement_lines(path: Path) -> set[int]:
    tree = ast.parse(path.read_text(), filename=str(path))
    return {node.lineno for node in ast.walk(tree) if isinstance(node, ast.stmt)}


if __name__ == "__main__":
    raise SystemExit(main())
