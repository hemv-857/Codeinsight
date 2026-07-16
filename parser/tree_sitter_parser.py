from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser


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
    symbols: tuple["SourceSymbol", ...]


@dataclass(frozen=True)
class SourceSymbol:
    """Source-level symbol extracted from a supported syntax tree."""

    kind: str
    name: str
    line: int
    column: int
    end_line: int
    end_column: int
    parent: str | None = None
    source: str | None = None
    exported: bool = False
    inherits: tuple[str, ...] = ()


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
        symbols = tuple(self._extract_symbols(root, source))
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
            symbols=symbols,
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

    def _extract_symbols(self, root: Node, source: bytes) -> list[SourceSymbol]:
        symbols: list[SourceSymbol] = []
        self._walk_symbols(root, source, symbols, parent=None, exported=False)
        return symbols

    def _walk_symbols(
        self,
        node: Node,
        source: bytes,
        symbols: list[SourceSymbol],
        *,
        parent: str | None,
        exported: bool,
    ) -> None:
        is_exported = exported or node.type == "export_statement"

        if node.type in {"import_statement", "import_from_statement"}:
            symbols.extend(self._extract_import_symbols(node, source))
            return

        if node.type in {"class_definition", "class_declaration"}:
            name = self._field_text(node, source, "name")
            if name is None:
                return
            symbols.append(
                self._symbol(
                    node,
                    kind="class",
                    name=name,
                    parent=parent,
                    exported=is_exported,
                    inherits=self._extract_inheritance(node, source),
                )
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type == "interface_declaration":
            name = self._field_text(node, source, "name")
            if name is None:
                return
            symbols.append(
                self._symbol(
                    node,
                    kind="interface",
                    name=name,
                    parent=parent,
                    exported=is_exported,
                    inherits=self._extract_inheritance(node, source),
                )
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type in {"function_definition", "function_declaration"}:
            name = self._field_text(node, source, "name")
            if name is None:
                return
            kind = "method" if parent else "function"
            symbols.append(
                self._symbol(node, kind=kind, name=name, parent=parent, exported=is_exported)
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type == "method_definition":
            name = self._field_text(node, source, "name")
            if name is None:
                return
            symbols.append(
                self._symbol(node, kind="method", name=name, parent=parent, exported=is_exported)
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type in {"assignment", "variable_declarator"}:
            name = self._field_text(node, source, "left") or self._field_text(node, source, "name")
            if name is not None and self._is_simple_identifier(name):
                symbols.append(
                    self._symbol(
                        node,
                        kind="variable",
                        name=name,
                        parent=parent,
                        exported=is_exported,
                    )
                )
            return

        self._walk_children(node, source, symbols, parent=parent, exported=is_exported)

    def _walk_children(
        self,
        node: Node,
        source: bytes,
        symbols: list[SourceSymbol],
        *,
        parent: str | None,
        exported: bool,
    ) -> None:
        for child in node.named_children:
            self._walk_symbols(child, source, symbols, parent=parent, exported=exported)

    def _extract_import_symbols(self, node: Node, source: bytes) -> list[SourceSymbol]:
        if node.type == "import_from_statement":
            module = self._field_text(node, source, "module_name")
            name = self._field_text(node, source, "name")
            return [self._symbol(node, kind="import", name=name, source=module)] if name else []

        source_name = self._strip_quotes(self._field_text(node, source, "source"))
        import_name = self._field_text(node, source, "name")
        if import_name is None:
            clause = self._first_child_text(node, source, "import_clause")
            import_name = clause or source_name
        if import_name is None:
            return []
        return [self._symbol(node, kind="import", name=import_name, source=source_name)]

    def _extract_inheritance(self, node: Node, source: bytes) -> tuple[str, ...]:
        inherited: list[str] = []
        for child_type in ("argument_list", "class_heritage", "extends_type_clause"):
            child = self._first_child(node, child_type)
            if child is not None:
                inherited.extend(self._identifier_texts(child, source))
        return tuple(dict.fromkeys(inherited))

    def _identifier_texts(self, node: Node, source: bytes) -> list[str]:
        names: list[str] = []
        if node.type in {"identifier", "type_identifier"}:
            names.append(self._node_text(node, source))
        for child in node.named_children:
            names.extend(self._identifier_texts(child, source))
        return names

    def _symbol(
        self,
        node: Node,
        *,
        kind: str,
        name: str,
        parent: str | None = None,
        source: str | None = None,
        exported: bool = False,
        inherits: tuple[str, ...] = (),
    ) -> SourceSymbol:
        return SourceSymbol(
            kind=kind,
            name=name,
            line=node.start_point.row + 1,
            column=node.start_point.column,
            end_line=node.end_point.row + 1,
            end_column=node.end_point.column,
            parent=parent,
            source=source,
            exported=exported,
            inherits=inherits,
        )

    def _field_text(self, node: Node, source: bytes, field_name: str) -> str | None:
        child = node.child_by_field_name(field_name)
        return self._node_text(child, source) if child is not None else None

    def _first_child_text(self, node: Node, source: bytes, child_type: str) -> str | None:
        child = self._first_child(node, child_type)
        return self._node_text(child, source) if child is not None else None

    def _first_child(self, node: Node, child_type: str) -> Node | None:
        for child in node.named_children:
            if child.type == child_type:
                return child
        return None

    def _node_text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    def _strip_quotes(self, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip("\"'")

    def _is_simple_identifier(self, value: str) -> bool:
        return value.replace("_", "").isalnum()
