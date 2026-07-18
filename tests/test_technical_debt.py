import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.technical_debt import TechnicalDebtService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_debt_fixture(path: Path) -> None:
    long_body = "\n".join(f"    value_{index} = {index}" for index in range(81))
    complex_body = "\n".join(
        f"    if value == {index}:\n        value += {index}" for index in range(10)
    )
    methods = "\n".join(
        f"    def method_{index}(self):\n        return {index}" for index in range(15)
    )
    write_file(path / "app" / "long.py", f"def long_function():\n{long_body}\n")
    write_file(path / "app" / "complex.py", f"def complex_function(value):\n{complex_body}\n")
    write_file(path / "app" / "wide.py", f"class WideService:\n{methods}\n")
    write_file(path / "src" / "a.ts", "import { b } from './b';\nexport const a = b;\n")
    write_file(path / "src" / "b.ts", "import { a } from './a';\nexport const b = a;\n")


def create_git_repository(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "forge@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CodeInsight"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    create_debt_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service() -> TechnicalDebtService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return TechnicalDebtService(
        scanner=scanner,
        parser=parser,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
    )


def test_technical_debt_service_reports_real_findings(tmp_path: Path) -> None:
    create_debt_fixture(tmp_path)

    report = create_service().analyze(tmp_path)

    categories = {finding.category for finding in report.findings}
    assert {"long_symbol", "high_complexity", "broad_type", "dependency_cycle"}.issubset(categories)
    assert report.stats.file_count == 5
    assert report.stats.parsed_file_count == 5
    assert report.stats.finding_count >= 3
    assert report.stats.max_complexity >= 10
    assert report.stats.complex_symbol_count >= 1
    assert report.stats.score < 100


def test_technical_debt_api_for_repository_path(tmp_path: Path) -> None:
    create_debt_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/technical-debt", json={"repository_path": str(tmp_path)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["finding_count"] >= 2
    assert any(
        finding["category"] in ("long_symbol", "high_complexity", "broad_type", "dependency_cycle")
        for finding in body["findings"]
    )


def test_technical_debt_api_for_imported_repository(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    create_git_repository(source)
    client = TestClient(
        create_app(Settings(environment="test", repository_storage_path=tmp_path / "imports"))
    )

    import_response = client.post(
        "/api/repositories/import",
        json={"source_type": "local", "source": str(source)},
    )

    assert import_response.status_code == 201
    import_id = import_response.json()["import_id"]

    debt_response = client.get(f"/api/repositories/imports/{import_id}/technical-debt")

    assert debt_response.status_code == 200
    assert debt_response.json()["stats"]["finding_count"] >= 2
