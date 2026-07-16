import re
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_rust
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
    calls: tuple["SourceCall", ...]


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
class SourceCall:
    """Call expression extracted from a supported syntax tree."""

    caller: str | None
    callee: str
    line: int
    column: int
    end_line: int
    end_column: int
    recursive: bool = False


@dataclass(frozen=True)
class LanguageDefinition:
    """Tree-sitter grammar metadata."""

    name: str
    load_language: Callable[[], object]


LANGUAGE_BY_EXTENSION = {
    ".c": LanguageDefinition("C", tree_sitter_c.language),
    ".cc": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".cpp": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".cxx": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".go": LanguageDefinition("Go", tree_sitter_go.language),
    ".h": LanguageDefinition("C", tree_sitter_c.language),
    ".hh": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".hpp": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".hxx": LanguageDefinition("C++", tree_sitter_cpp.language),
    ".java": LanguageDefinition("Java", tree_sitter_java.language),
    ".js": LanguageDefinition("JavaScript", tree_sitter_javascript.language),
    ".jsx": LanguageDefinition("JavaScript", tree_sitter_javascript.language),
    ".py": LanguageDefinition("Python", tree_sitter_python.language),
    ".rs": LanguageDefinition("Rust", tree_sitter_rust.language),
    ".ts": LanguageDefinition("TypeScript", tree_sitter_typescript.language_typescript),
    ".tsx": LanguageDefinition("TypeScript", tree_sitter_typescript.language_tsx),
}

DEFAULT_PARSE_CACHE_ENTRIES = 1024
ParseCacheKey = tuple[str, int, int]


class TreeSitterParserService:
    """Parses supported source files with Tree-sitter."""

    def __init__(self, max_cache_entries: int = DEFAULT_PARSE_CACHE_ENTRIES) -> None:
        if max_cache_entries <= 0:
            raise ValueError("max_cache_entries must be positive.")
        self._parsers: dict[str, Parser] = {}
        self._max_cache_entries = max_cache_entries
        self._cache: OrderedDict[ParseCacheKey, ParseTreeSummary] = OrderedDict()
        self._cache_lock = Lock()

    def parse_file(self, path: Path) -> ParseTreeSummary:
        source_path = path.expanduser().resolve()
        if not source_path.is_file():
            raise TreeSitterParseError("Source file does not exist or is not a file.")

        definition = LANGUAGE_BY_EXTENSION.get(source_path.suffix.lower())
        if definition is None:
            raise TreeSitterParseError("Source file language is not supported by Tree-sitter yet.")

        stat = source_path.stat()
        cache_key = (str(source_path), stat.st_mtime_ns, stat.st_size)
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        source = source_path.read_bytes()
        parser = self._get_parser(source_path.suffix.lower(), definition)
        tree = parser.parse(source)
        root = tree.root_node
        symbols = tuple(self._extract_symbols(root, source))
        calls = tuple(self._extract_calls(root, source))
        summary = ParseTreeSummary(
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
            calls=calls,
        )
        self._store_cache(cache_key, summary)
        return summary

    def supports_path(self, path: Path) -> bool:
        """Return whether a path has a supported parser extension."""
        return path.suffix.lower() in LANGUAGE_BY_EXTENSION

    def _get_parser(self, key: str, definition: LanguageDefinition) -> Parser:
        parser = self._parsers.get(key)
        if parser is None:
            parser = Parser(Language(definition.load_language()))
            self._parsers[key] = parser
        return parser

    def _cached(self, cache_key: ParseCacheKey) -> ParseTreeSummary | None:
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached is None:
                return None
            self._cache.move_to_end(cache_key)
            return cached

    def _store_cache(self, cache_key: ParseCacheKey, summary: ParseTreeSummary) -> None:
        with self._cache_lock:
            path = cache_key[0]
            for key in tuple(self._cache):
                if key[0] == path and key != cache_key:
                    self._cache.pop(key)
            self._cache[cache_key] = summary
            self._cache.move_to_end(cache_key)
            while len(self._cache) > self._max_cache_entries:
                self._cache.popitem(last=False)

    def _extract_symbols(self, root: Node, source: bytes) -> list[SourceSymbol]:
        symbols: list[SourceSymbol] = []
        self._walk_symbols(root, source, symbols, parent=None, exported=False)
        return symbols

    def _extract_calls(self, root: Node, source: bytes) -> list[SourceCall]:
        calls: list[SourceCall] = []
        self._walk_calls(root, source, calls, caller=None)
        return calls

    def _walk_calls(
        self,
        node: Node,
        source: bytes,
        calls: list[SourceCall],
        *,
        caller: str | None,
    ) -> None:
        next_caller = self._scope_name(node, source) or caller
        if node.type in {"call", "call_expression", "method_invocation"}:
            callee = self._call_name(node, source)
            if callee is not None:
                calls.append(
                    SourceCall(
                        caller=caller,
                        callee=callee,
                        line=node.start_point.row + 1,
                        column=node.start_point.column,
                        end_line=node.end_point.row + 1,
                        end_column=node.end_point.column,
                        recursive=caller == callee,
                    )
                )

        for child in self._named_children(node):
            self._walk_calls(child, source, calls, caller=next_caller)

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

        if node.type in {
            "import_declaration",
            "import_from_statement",
            "import_statement",
            "preproc_include",
            "use_declaration",
        }:
            symbols.extend(self._extract_import_symbols(node, source))
            return

        if node.type in {
            "class_declaration",
            "class_definition",
            "class_specifier",
            "struct_item",
            "struct_specifier",
            "type_spec",
        }:
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

        if node.type in {"interface_declaration", "trait_item"}:
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

        if node.type == "impl_item":
            parent_name = self._field_text(node, source, "type")
            self._walk_children(node, source, symbols, parent=parent_name, exported=False)
            return

        if node.type in {"function_declaration", "function_definition", "function_item"}:
            name = self._field_text(node, source, "name") or self._declarator_name(node, source)
            if name is None:
                return
            kind = "method" if parent else "function"
            symbols.append(
                self._symbol(node, kind=kind, name=name, parent=parent, exported=is_exported)
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type in {"function_signature_item", "method_declaration", "method_definition"}:
            name = self._field_text(node, source, "name")
            if name is None:
                return
            symbols.append(
                self._symbol(node, kind="method", name=name, parent=parent, exported=is_exported)
            )
            self._walk_children(node, source, symbols, parent=name, exported=False)
            return

        if node.type in {
            "assignment",
            "declaration",
            "field_declaration",
            "let_declaration",
            "short_var_declaration",
            "variable_declarator",
        }:
            name = (
                self._field_text(node, source, "left")
                or self._field_text(node, source, "name")
                or self._declarator_name(node, source)
                or self._first_identifier_text(node, source)
            )
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
        for child in self._named_children(node):
            self._walk_symbols(child, source, symbols, parent=parent, exported=exported)

    def _scope_name(self, node: Node, source: bytes) -> str | None:
        if node.type in {
            "function_declaration",
            "function_definition",
            "function_item",
            "function_signature_item",
            "method_declaration",
            "method_definition",
        }:
            return self._field_text(node, source, "name") or self._declarator_name(node, source)
        return None

    def _call_name(self, node: Node, source: bytes) -> str | None:
        name = self._field_text(node, source, "name")
        if name is not None:
            return name
        function = node.child_by_field_name("function")
        if function is None:
            return None
        field = self._field_text(function, source, "field")
        if field is not None:
            return field
        return self._last_identifier_text(function, source) or self._node_text(function, source)

    def _extract_import_symbols(self, node: Node, source: bytes) -> list[SourceSymbol]:
        if node.type == "import_from_statement":
            module = self._field_text(node, source, "module_name")
            name = self._field_text(node, source, "name")
            return [self._symbol(node, kind="import", name=name, source=module)] if name else []

        if node.type == "preproc_include":
            path = self._field_text(node, source, "path")
            name = self._strip_include(path)
            return [self._symbol(node, kind="import", name=name, source=path)] if name else []

        source_name = self._strip_quotes(self._field_text(node, source, "source"))
        if source_name is None:
            path = self._first_field_text(node, source, "path")
            source_name = self._strip_quotes(path) or path
        if source_name is None:
            source_name = self._first_child_text(node, source, "scoped_identifier")
        import_name = self._field_text(node, source, "name")
        if import_name is None:
            clause = self._first_child_text(node, source, "import_clause")
            import_name = clause or self._last_identifier_text(node, source) or source_name
        if import_name is None:
            return []
        return [self._symbol(node, kind="import", name=import_name, source=source_name)]

    def _extract_inheritance(self, node: Node, source: bytes) -> tuple[str, ...]:
        inherited: list[str] = []
        for child_type in (
            "argument_list",
            "base_class_clause",
            "class_heritage",
            "extends_type_clause",
            "superclass",
            "interfaces",
        ):
            child = node.child_by_field_name(child_type) or self._first_child(node, child_type)
            if child is not None:
                inherited.extend(self._identifier_texts(child, source))
        return tuple(dict.fromkeys(inherited))

    def _identifier_texts(self, node: Node, source: bytes) -> list[str]:
        names: list[str] = []
        if node.type in {"identifier", "type_identifier"}:
            names.append(self._node_text(node, source))
        for child in self._named_children(node):
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

    def _first_field_text(self, node: Node, source: bytes, field_name: str) -> str | None:
        child = node.child_by_field_name(field_name)
        if child is not None:
            return self._node_text(child, source)
        for named_child in self._named_children(node):
            text = self._first_field_text(named_child, source, field_name)
            if text is not None:
                return text
        return None

    def _first_child(self, node: Node, child_type: str) -> Node | None:
        for child in self._named_children(node):
            if child.type == child_type:
                return child
        return None

    def _declarator_name(self, node: Node, source: bytes) -> str | None:
        declarator = node.child_by_field_name("declarator")
        if declarator is None:
            return None
        return self._first_identifier_text(declarator, source)

    def _first_identifier_text(self, node: Node, source: bytes) -> str | None:
        if node.type in {
            "field_identifier",
            "identifier",
            "package_identifier",
            "property_identifier",
            "type_identifier",
        }:
            return self._node_text(node, source)
        for child in self._named_children(node):
            text = self._first_identifier_text(child, source)
            if text is not None:
                return text
        return None

    def _last_identifier_text(self, node: Node, source: bytes) -> str | None:
        identifiers = self._identifier_texts(node, source)
        return identifiers[-1] if identifiers else None

    def _node_text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    def _strip_quotes(self, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip("\"'")

    def _strip_include(self, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip('<>"')

    def _is_simple_identifier(self, value: str) -> bool:
        return value.replace("_", "").isalnum()

    def _named_children(self, node: Node) -> tuple[Node, ...]:
        children: list[Node] = []
        for index in range(node.named_child_count):
            child = node.named_child(index)
            if child is not None:
                children.append(child)
        return tuple(children)


class SafeSourceParserService(TreeSitterParserService):
    """Thread-safe source parser fallback for demo environments."""

    def __init__(self, max_cache_entries: int = DEFAULT_PARSE_CACHE_ENTRIES) -> None:
        if max_cache_entries <= 0:
            raise ValueError("max_cache_entries must be positive.")
        self._max_cache_entries = max_cache_entries
        self._cache: OrderedDict[ParseCacheKey, ParseTreeSummary] = OrderedDict()
        self._cache_lock = Lock()

    def parse_file(self, path: Path) -> ParseTreeSummary:
        source_path = path.expanduser().resolve()
        if not source_path.is_file():
            raise TreeSitterParseError("Source file does not exist or is not a file.")

        definition = LANGUAGE_BY_EXTENSION.get(source_path.suffix.lower())
        if definition is None:
            raise TreeSitterParseError("Source file language is not supported by Tree-sitter yet.")

        stat = source_path.stat()
        cache_key = (str(source_path), stat.st_mtime_ns, stat.st_size)
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        source = source_path.read_text(encoding="utf-8", errors="replace")
        symbols = tuple(self._safe_symbols(source, source_path.suffix.lower()))
        calls = tuple(self._safe_calls(source))
        line_count = max(1, source.count("\n") + 1)
        summary = ParseTreeSummary(
            path=str(source_path),
            language=definition.name,
            root_node_type="module",
            start_byte=0,
            end_byte=stat.st_size,
            start_point=Point(row=0, column=0),
            end_point=Point(row=line_count - 1, column=0),
            has_error=False,
            named_child_count=len(symbols),
            symbols=symbols,
            calls=calls,
        )
        self._store_cache(cache_key, summary)
        return summary

    def _safe_symbols(self, source: str, extension: str) -> list[SourceSymbol]:
        symbols: list[SourceSymbol] = []
        parent_stack: list[tuple[int, str]] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            indent = len(line) - len(line.lstrip(" "))
            parent_stack = [(level, name) for level, name in parent_stack if level < indent]
            parent = parent_stack[-1][1] if parent_stack else None

            import_symbol = self._safe_import_symbol(line, line_number)
            if import_symbol is not None:
                symbols.append(import_symbol)

            class_match = re.match(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if extension == ".py":
                class_match = re.match(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if class_match is not None:
                name = class_match.group(1)
                symbols.append(self._safe_symbol("class", name, line, line_number, parent=None))
                parent_stack.append((indent, name))
                continue

            function_match = re.match(
                r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
                line,
            )
            if extension == ".py":
                function_match = re.match(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if function_match is not None:
                name = function_match.group(1)
                symbols.append(
                    self._safe_symbol(
                        "method" if parent else "function", name, line, line_number, parent
                    )
                )
                parent_stack.append((indent, name))
                continue

            variable_match = re.match(
                r"^\s*(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
                line,
            )
            if extension == ".py":
                variable_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if variable_match is not None:
                symbols.append(
                    self._safe_symbol(
                        "variable", variable_match.group(1), line, line_number, parent
                    )
                )
        return symbols

    def _safe_import_symbol(self, line: str, line_number: int) -> SourceSymbol | None:
        python_import = re.match(r"^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w*.,\s]+)", line)
        if python_import is not None:
            source = python_import.group(1)
            name = python_import.group(2).split(",")[0].strip()
            return self._safe_symbol("import", name, line, line_number, source=source)

        js_import = re.match(r"^\s*import\s+(.+?)\s+from\s+[\"']([^\"']+)[\"']", line)
        if js_import is not None:
            return self._safe_symbol(
                "import", js_import.group(1).strip(), line, line_number, source=js_import.group(2)
            )
        return None

    def _safe_calls(self, source: str) -> list[SourceCall]:
        calls: list[SourceCall] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", line):
                callee = match.group(1)
                if callee in {"class", "def", "function", "if", "for", "while"}:
                    continue
                calls.append(
                    SourceCall(
                        caller=None,
                        callee=callee,
                        line=line_number,
                        column=match.start(1),
                        end_line=line_number,
                        end_column=match.end(1),
                    )
                )
        return calls

    def _safe_symbol(
        self,
        kind: str,
        name: str,
        line: str,
        line_number: int,
        parent: str | None = None,
        source: str | None = None,
    ) -> SourceSymbol:
        column = max(0, line.find(name))
        return SourceSymbol(
            kind=kind,
            name=name,
            line=line_number,
            column=column,
            end_line=line_number,
            end_column=column + len(name),
            parent=parent,
            source=source,
        )
