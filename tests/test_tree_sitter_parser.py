import subprocess
from pathlib import Path

import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient
from parser.tree_sitter_parser import TreeSitterParseError, TreeSitterParserService


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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
        ["git", "config", "user.name", "Forge AI"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    write_file(path / "src" / "main.py", "print('hello')\n")
    write_file(path / "src" / "app.ts", "const value: number = 1;\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_parser_supports_python_javascript_typescript_and_tsx(tmp_path: Path) -> None:
    files = {
        "main.py": ("print('hello')\n", "Python", "module"),
        "app.js": ("const value = 1;\n", "JavaScript", "program"),
        "app.ts": ("const value: number = 1;\n", "TypeScript", "program"),
        "app.tsx": ("const element = <div />;\n", "TypeScript", "program"),
    }
    service = TreeSitterParserService()

    for filename, (content, language, root_node_type) in files.items():
        source_path = tmp_path / filename
        write_file(source_path, content)

        result = service.parse_file(source_path)

        assert result.language == language
        assert result.root_node_type == root_node_type
        assert result.has_error is False
        assert result.end_byte == len(content.encode())
        assert result.named_child_count > 0


def test_parser_rejects_unsupported_files(tmp_path: Path) -> None:
    source_path = tmp_path / "README.md"
    write_file(source_path, "# Demo\n")
    service = TreeSitterParserService()

    with pytest.raises(TreeSitterParseError, match="not supported"):
        service.parse_file(source_path)


def test_parse_file_api(tmp_path: Path) -> None:
    source_path = tmp_path / "main.py"
    write_file(source_path, "print('hello')\n")
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post("/api/repositories/parse-file", json={"path": str(source_path)})

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "Python"
    assert body["root_node_type"] == "module"
    assert body["has_error"] is False


def test_parse_imported_repository_api(tmp_path: Path) -> None:
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

    parse_response = client.post(f"/api/repositories/parse-import/{import_id}")

    assert parse_response.status_code == 200
    parsed = parse_response.json()["parsed_files"]
    assert [file["language"] for file in parsed] == ["TypeScript", "Python"]
