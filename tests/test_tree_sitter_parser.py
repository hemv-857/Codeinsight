import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient
from parser.tree_sitter_parser import SourceSymbol, TreeSitterParseError, TreeSitterParserService


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


def symbol_names(result_symbols: Sequence[SourceSymbol], kind: str) -> list[str]:
    return [symbol.name for symbol in result_symbols if symbol.kind == kind]


def test_parser_supports_all_configured_languages(tmp_path: Path) -> None:
    files = {
        "main.c": ("#include <stdio.h>\nint main(void) { return 0; }\n", "C", "translation_unit"),
        "main.cpp": ("#include <vector>\nint main() { return 0; }\n", "C++", "translation_unit"),
        "main.go": ("package main\nfunc main() {}\n", "Go", "source_file"),
        "Main.java": ("class Main {}\n", "Java", "program"),
        "main.py": ("print('hello')\n", "Python", "module"),
        "app.js": ("const value = 1;\n", "JavaScript", "program"),
        "main.rs": ("fn main() {}\n", "Rust", "source_file"),
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


def test_parser_extracts_c_and_cpp_symbols(tmp_path: Path) -> None:
    files = {
        "main.c": (
            "\n".join(
                [
                    "#include <stdio.h>",
                    "int count = 0;",
                    "struct User { int id; };",
                    "int add(int a, int b) {",
                    "  int total = a + b;",
                    "  return total;",
                    "}",
                    "",
                ]
            ),
            "C",
            ["stdio.h"],
            ["User"],
            ["add"],
            ["count", "id", "total"],
            (),
        ),
        "main.cpp": (
            "\n".join(
                [
                    "#include <vector>",
                    "class Service : public Base {",
                    " public:",
                    "  int run(int x) {",
                    "    int value = x;",
                    "    return value;",
                    "  }",
                    "};",
                    "int make() {",
                    "  auto item = Service();",
                    "  return 1;",
                    "}",
                    "",
                ]
            ),
            "C++",
            ["vector"],
            ["Service"],
            ["make"],
            ["value", "item"],
            ("Base",),
        ),
    }
    service = TreeSitterParserService()

    for filename, (
        content,
        language,
        imports,
        classes,
        functions,
        variables,
        inherits,
    ) in files.items():
        source_path = tmp_path / filename
        write_file(source_path, content)

        result = service.parse_file(source_path)

        assert result.language == language
        assert symbol_names(result.symbols, "import") == imports
        assert symbol_names(result.symbols, "class") == classes
        assert symbol_names(result.symbols, "function") == functions
        assert symbol_names(result.symbols, "variable") == variables
        parsed_class = next(symbol for symbol in result.symbols if symbol.name == classes[0])
        assert parsed_class.inherits == inherits


def test_parser_extracts_java_go_and_rust_symbols(tmp_path: Path) -> None:
    files = {
        "Main.java": (
            "\n".join(
                [
                    "import java.util.List;",
                    "interface Named {}",
                    "class UserService extends BaseService implements Named {",
                    "  private int count;",
                    "  int load(int id) {",
                    "    int value = id;",
                    "    return value;",
                    "  }",
                    "}",
                    "",
                ]
            ),
            "Java",
            ["List"],
            ["UserService"],
            ["Named"],
            [],
            ["load"],
            ["count", "value"],
            ("BaseService", "Named"),
        ),
        "main.go": (
            "\n".join(
                [
                    "package main",
                    'import "fmt"',
                    "type User struct { ID int }",
                    'func (u User) Name() string { value := "x"; return value }',
                    "func main() { count := 1; fmt.Println(count) }",
                    "",
                ]
            ),
            "Go",
            ["fmt"],
            ["User"],
            [],
            ["main"],
            ["Name"],
            ["ID", "value", "count"],
            (),
        ),
        "main.rs": (
            "\n".join(
                [
                    "use std::fmt;",
                    "struct User { id: i32 }",
                    "trait Named { fn name(&self) -> String; }",
                    "impl User { fn load(&self) -> i32 { let value = self.id; value } }",
                    "fn make_user() -> User { let user = User { id: 1 }; user }",
                    "",
                ]
            ),
            "Rust",
            ["fmt"],
            ["User"],
            ["Named"],
            ["make_user"],
            ["name", "load"],
            ["id", "value", "user"],
            (),
        ),
    }
    service = TreeSitterParserService()

    for (
        filename,
        (content, language, imports, classes, interfaces, functions, methods, variables, inherits),
    ) in files.items():
        source_path = tmp_path / filename
        write_file(source_path, content)

        result = service.parse_file(source_path)

        assert result.language == language
        assert symbol_names(result.symbols, "import") == imports
        assert symbol_names(result.symbols, "class") == classes
        assert symbol_names(result.symbols, "interface") == interfaces
        assert symbol_names(result.symbols, "function") == functions
        assert symbol_names(result.symbols, "method") == methods
        assert symbol_names(result.symbols, "variable") == variables
        parsed_class = next(symbol for symbol in result.symbols if symbol.name == classes[0])
        assert parsed_class.inherits == inherits


def test_parser_extracts_python_symbols(tmp_path: Path) -> None:
    source_path = tmp_path / "main.py"
    write_file(
        source_path,
        "\n".join(
            [
                "import os",
                "from service.base import BaseService",
                "",
                "class UserService(BaseService):",
                "    version = 1",
                "",
                "    def load(self, user_id):",
                "        result = user_id",
                "        return result",
                "",
                "def make_user(name):",
                "    user = name",
                "    return user",
                "",
            ]
        ),
    )
    service = TreeSitterParserService()

    result = service.parse_file(source_path)

    assert symbol_names(result.symbols, "import") == ["os", "BaseService"]
    assert symbol_names(result.symbols, "class") == ["UserService"]
    assert symbol_names(result.symbols, "method") == ["load"]
    assert symbol_names(result.symbols, "function") == ["make_user"]
    assert symbol_names(result.symbols, "variable") == ["version", "result", "user"]
    user_service = next(symbol for symbol in result.symbols if symbol.name == "UserService")
    load = next(symbol for symbol in result.symbols if symbol.name == "load")
    base_import = next(symbol for symbol in result.symbols if symbol.name == "BaseService")
    assert user_service.inherits == ("BaseService",)
    assert load.parent == "UserService"
    assert base_import.source == "service.base"
    assert user_service.line == 4


def test_parser_extracts_javascript_and_typescript_symbols(tmp_path: Path) -> None:
    files = {
        "app.js": (
            "\n".join(
                [
                    "import fs from 'fs';",
                    "export class Worker extends BaseWorker {",
                    "  run(input) {",
                    "    const value = input;",
                    "    return value;",
                    "  }",
                    "}",
                    "export function start() {",
                    "  var enabled = true;",
                    "  return enabled;",
                    "}",
                    "export const workerName = 'forge';",
                    "",
                ]
            ),
            "Worker",
            "BaseWorker",
            ["Worker", "start", "workerName"],
        ),
        "app.ts": (
            "\n".join(
                [
                    "import React from 'react';",
                    "export interface User extends Person {",
                    "  id: string;",
                    "}",
                    "export class UserStore extends BaseStore {",
                    "  find(id: string) {",
                    "    const value = id;",
                    "    return value;",
                    "  }",
                    "}",
                    "export const storeName: string = 'users';",
                    "",
                ]
            ),
            "UserStore",
            "BaseStore",
            ["User", "UserStore", "storeName"],
        ),
    }
    service = TreeSitterParserService()

    for filename, (content, class_name, inherited_name, exported_names) in files.items():
        source_path = tmp_path / filename
        write_file(source_path, content)

        result = service.parse_file(source_path)

        exported = [symbol.name for symbol in result.symbols if symbol.exported]
        parsed_class = next(symbol for symbol in result.symbols if symbol.name == class_name)
        assert exported == exported_names
        assert parsed_class.inherits == (inherited_name,)
        assert symbol_names(result.symbols, "import")
        assert symbol_names(result.symbols, "method")
        assert symbol_names(result.symbols, "variable")


def test_parser_rejects_unsupported_files(tmp_path: Path) -> None:
    source_path = tmp_path / "README.md"
    write_file(source_path, "# Demo\n")
    service = TreeSitterParserService()

    with pytest.raises(TreeSitterParseError, match="not supported"):
        service.parse_file(source_path)


def test_parse_file_api(tmp_path: Path) -> None:
    source_path = tmp_path / "main.py"
    write_file(source_path, "def hello():\n    return 'world'\n")
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post("/api/repositories/parse-file", json={"path": str(source_path)})

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "Python"
    assert body["root_node_type"] == "module"
    assert body["has_error"] is False
    assert [symbol["name"] for symbol in body["symbols"]] == ["hello"]


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
