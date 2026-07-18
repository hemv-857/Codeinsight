import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.bug_impact import BugImpactService
from backend.app.services.repository_scanner import RepositoryScannerService
from backend.app.services.risk_scoring import RiskScoringService
from backend.app.services.stack_trace import StackTraceParserService
from fastapi.testclient import TestClient
from graph.dependency_graph import DependencyGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_bug_fixture(path: Path) -> None:
    write_file(
        path / "api" / "checkout.py",
        "from services.payment import charge\n\n\ndef route():\n    charge()\n",
    )
    write_file(
        path / "services" / "payment.py",
        "from services.gateway import submit\n\n\ndef charge():\n    submit()\n",
    )
    write_file(path / "services" / "gateway.py", "def submit():\n    return True\n")


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
    create_bug_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def create_service() -> BugImpactService:
    scanner = RepositoryScannerService()
    parser = TreeSitterParserService()
    return BugImpactService(
        scanner=scanner,
        dependency_graph=DependencyGraphService(scanner=scanner, parser=parser),
        stack_trace_parser=StackTraceParserService(),
        risk_scoring=RiskScoringService(),
    )


def stack_trace() -> str:
    return """Traceback (most recent call last):
  File "api/checkout.py", line 4, in route
    charge()
  File "services/payment.py", line 4, in charge
    submit()
PaymentError: card declined"""


def test_bug_impact_service_predicts_root_cause_and_neighbors(tmp_path: Path) -> None:
    create_bug_fixture(tmp_path)

    prediction = create_service().predict(tmp_path, stack_trace())

    assert prediction.root_cause is not None
    assert prediction.root_cause.path == "services/payment.py"
    assert prediction.error_type == "PaymentError"
    impacted_paths = {file.path for file in prediction.impacted_files}
    assert "services/payment.py" in impacted_paths
    assert "api/checkout.py" in impacted_paths
    assert "services/gateway.py" in impacted_paths
    assert prediction.stats.risk_score > 20
    assert prediction.stats.risk_level in {"medium", "high", "critical"}
    assert prediction.stats.confidence > 0.5
    assert prediction.risk.factors


def test_bug_impact_api_for_repository_path(tmp_path: Path) -> None:
    create_bug_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/bug-impact",
        json={"repository_path": str(tmp_path), "stack_trace": stack_trace()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["root_cause"]["path"] == "services/payment.py"
    assert body["stats"]["impacted_file_count"] >= 3
    assert body["risk"]["factors"][0]["name"] == "stack_trace_match"


def test_bug_impact_api_for_imported_repository(tmp_path: Path) -> None:
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

    impact_response = client.post(
        f"/api/repositories/imports/{import_id}/bug-impact",
        json={"stack_trace": stack_trace(), "changed_files": ["services/payment.py"]},
    )

    assert impact_response.status_code == 200
    assert impact_response.json()["root_cause"]["score"] == 0.9
