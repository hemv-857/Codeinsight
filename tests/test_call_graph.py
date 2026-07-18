import subprocess
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.repository_scanner import RepositoryScannerService
from fastapi.testclient import TestClient
from graph.call_graph import CallGraphService
from parser.tree_sitter_parser import TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_call_graph_fixture(path: Path) -> None:
    write_file(
        path / "app" / "main.py",
        "\n".join(
            [
                "def helper():",
                "    return 1",
                "",
                "def main():",
                "    helper()",
                "    main()",
                "    missing()",
                "",
            ]
        ),
    )
    write_file(
        path / "web" / "app.ts",
        "\n".join(
            [
                "export function render() {",
                "  hydrate();",
                "}",
                "",
                "function hydrate() {",
                "  render();",
                "}",
                "",
            ]
        ),
    )


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
    create_call_graph_fixture(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_parser_extracts_call_sites(tmp_path: Path) -> None:
    source_path = tmp_path / "main.py"
    write_file(source_path, "def main():\n    main()\n    print('done')\n")
    service = TreeSitterParserService()

    result = service.parse_file(source_path)

    assert [(call.caller, call.callee, call.recursive) for call in result.calls] == [
        ("main", "main", True),
        ("main", "print", False),
    ]


def test_call_graph_resolves_recursive_and_unresolved_calls(tmp_path: Path) -> None:
    create_call_graph_fixture(tmp_path)
    service = CallGraphService(
        scanner=RepositoryScannerService(),
        parser=TreeSitterParserService(),
    )

    graph = service.build(tmp_path)

    assert sorted(node.id for node in graph.nodes) == [
        "app/main.py:helper",
        "app/main.py:main",
        "web/app.ts:hydrate",
        "web/app.ts:render",
    ]
    resolved_edges = {
        (edge.source, edge.target, edge.callee) for edge in graph.edges if edge.target
    }
    assert resolved_edges == {
        ("app/main.py:main", "app/main.py:helper", "helper"),
        ("app/main.py:main", "app/main.py:main", "main"),
        ("web/app.ts:hydrate", "web/app.ts:render", "render"),
        ("web/app.ts:render", "web/app.ts:hydrate", "hydrate"),
    }
    assert graph.unresolved_calls == ("missing",)
    assert graph.stats.callable_count == 4
    assert graph.stats.call_count == 5
    assert graph.stats.resolved_call_count == 4
    assert graph.stats.unresolved_call_count == 1
    assert graph.stats.recursive_call_count == 1


def test_call_graph_api_for_repository_path(tmp_path: Path) -> None:
    create_call_graph_fixture(tmp_path)
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/call-graph",
        json={"repository_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["callable_count"] == 4
    assert body["stats"]["recursive_call_count"] == 1
    assert body["unresolved_calls"] == ["missing"]


def test_call_graph_api_for_imported_repository(tmp_path: Path) -> None:
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

    graph_response = client.get(f"/api/repositories/imports/{import_id}/call-graph")

    assert graph_response.status_code == 200
    assert graph_response.json()["stats"]["resolved_call_count"] == 4
