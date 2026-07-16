# Frontend

Next.js application code for Forge AI.

## Local Commands

- Start the dashboard: `npm run dev --workspace @forge-ai/frontend`
- Build the dashboard: `npm run build --workspace @forge-ai/frontend`
- Type check: `npm run typecheck --workspace @forge-ai/frontend`

## Environment

- `NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`.

The first screen is the dark-mode Forge AI dashboard with backend health, a repository explorer, repository search, workflow status, and graph panels.

The repository explorer can scan a backend-accessible local repository path or load a previously imported repository by import ID.

The repository search panel can index vectors for a repository path or import ID, then run hybrid retrieval with vector, keyword, and graph scores.

The technical debt panel analyzes a repository path or import ID and displays maintainability findings, severity counts, complexity metrics, and an architecture health score.

The circular dependencies panel detects file-level import cycles from a repository path or import ID and displays impact statistics plus participating edges.

The dead code panel reports candidate unreferenced files and uncalled functions from dependency and call graph evidence.

The architecture violations panel flags common layer-boundary import issues with severity, confidence, and edge evidence.

The stack trace parser panel extracts files, functions, line numbers, language, and error metadata from pasted traces.

The bug impact panel predicts likely root cause, affected files, risk level, and scoring factors from stack traces, changed files, and dependency graph evidence.

The README generator panel creates repository-grounded Markdown from scanner, parser, dependency graph, call graph, and embedding metadata.

The architecture docs panel exports architecture Markdown with components, dependency flow, call flow, observations, evidence paths, and confidence.

The Mermaid diagrams panel exports architecture, dependency, and call-flow Mermaid source from repository graph evidence.

The developer onboarding panel generates a first-day Markdown guide from repository facts, architecture docs, and Mermaid diagrams.

The PR review panel reviews changed files with dependency impact, technical debt, testing, and diff-size signals.

The dependency graph panel can build file-level import graphs from a repository path or import ID and render internal dependencies, unresolved imports, and detected cycles.

The knowledge graph panel can build and persist the repository architecture graph, then display graph size, relationship counts, and the selected persistence backend.

Graph panels include zoom, fit-view, minimap, node dragging, and edge-label controls. Dependency graph node selection highlights directly connected files.
