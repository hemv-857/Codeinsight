from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Parser


class TreeSitterParseError(Exception):
    """Raised when a source file cannot be parsed with the supported grammars."""


@dataclass(frozen=True)
class Point:
    """A zero-indexed Tree-sitter source position."""

    row: int
    column: int


@dataclass(frozen=True)
class ParseTreeSummary:
    """Compact AST metadata for one parsed source file."""

    path: str
    language: str
    root_node_type: str
    start_byte: int
    end_byte: int
    start_point: Point
    end_point: Point
    has_error: bool
    named_child_count: int


@dataclass(frozen=True)
class LanguageDefinition:
    """Tree-sitter grammar metadata."""

    name: str
    load_language: Callable[[], object]


LANGUAGE_BY_EXTENSION = {
    ".js": LanguageDefinition("JavaScript", tree_sitter_javascript.language),
    ".jsx": LanguageDefinition("JavaScript", tree_sitter_javascript.language),
    ".py": LanguageDefinition("Python", tree_sitter_python.language),
    ".ts": LanguageDefinition("TypeScript", tree_sitter_typescript.language_typescript),
    ".tsx": LanguageDefinition("TypeScript", tree_sitter_typescript.language_tsx),
}


class TreeSitterParserService:
    """Parses supported source files with Tree-sitter."""

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def parse_file(self, path: Path) -> ParseTreeSummary:
        source_path = path.expanduser().resolve()
        if not source_path.is_file():
            raise TreeSitterParseError("Source file does not exist or is not a file.")

        definition = LANGUAGE_BY_EXTENSION.get(source_path.suffix.lower())
        if definition is None:
            raise TreeSitterParseError("Source file language is not supported by Tree-sitter yet.")

        source = source_path.read_bytes()
        parser = self._get_parser(source_path.suffix.lower(), definition)
        tree = parser.parse(source)
        root = tree.root_node
        return ParseTreeSummary(
            path=str(source_path),
            language=definition.name,
            root_node_type=root.type,
            start_byte=root.start_byte,
            end_byte=root.end_byte,
            start_point=Point(row=root.start_point.row, column=root.start_point.column),
            end_point=Point(row=root.end_point.row, column=root.end_point.column),
            has_error=root.has_error,
            named_child_count=root.named_child_count,
        )

    def supports_path(self, path: Path) -> bool:
        """Return whether a path has a supported parser extension."""
        return path.suffix.lower() in LANGUAGE_BY_EXTENSION

    def _get_parser(self, key: str, definition: LanguageDefinition) -> Parser:
        parser = self._parsers.get(key)
        if parser is None:
            parser = Parser(Language(definition.load_language()))
            self._parsers[key] = parser
        return parser
