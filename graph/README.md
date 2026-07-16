# Graph

Graph construction modules live here.

Milestone 11 provides a file-level dependency graph builder that resolves parsed
import symbols to repository files where possible, reports external imports, and
detects circular file dependencies.

Milestone 12 provides a callable-level call graph builder that extracts function
and method call sites, resolves calls to discovered repository callables where
possible, and reports unresolved and recursive calls.
