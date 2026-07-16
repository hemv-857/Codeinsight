from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_make_test_enforces_python_coverage_gate() -> None:
    makefile = (ROOT / "Makefile").read_text()
    coverage_script = (ROOT / "scripts" / "check_python_coverage.py").read_text()

    assert "scripts/check_python_coverage.py --min 90" in makefile
    assert "SOURCE_DIRECTORIES" in coverage_script
    assert "DEFAULT_MINIMUM = 90.0" in coverage_script
