# Graph

Graph construction modules live here.

Milestone 11 provides a file-level dependency graph builder that resolves parsed
import symbols to repository files where possible, reports external imports, and
detects circular file dependencies.

Milestone 12 provides a callable-level call graph builder that extracts function
and method call sites, resolves calls to discovered repository callables where
possible, and reports unresolved and recursive calls.

Milestone 13 provides a repository knowledge graph builder and Neo4j writer for
repository, directory, file, symbol, import, call, containment, and inheritance
relationships.

Milestone 14 adds a NetworkX-backed repository fallback. Knowledge graph writes
try Neo4j first and fall back to an in-memory `networkx.MultiDiGraph` when the
primary graph backend is unavailable.
