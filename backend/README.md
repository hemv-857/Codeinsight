# Backend

FastAPI application code for Forge AI.

## Local Commands

- Run tests: `make test`
- Run verification: `make verify`
- Start the API locally: `FORGE_AI_PARSER_PROVIDER=safe .venv313/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8002`

Use Python 3.13 for local backend demos on macOS. Python 3.14.6 can segfault in
worker threads while scanning repositories. `FORGE_AI_PARSER_PROVIDER=safe`
keeps the demo API stable if native Tree-sitter bindings crash during parsing.

## Environment

Configuration is loaded from environment variables prefixed with `FORGE_AI_`.

- `FORGE_AI_APP_NAME`
- `FORGE_AI_CONVERSATION_DATABASE_PATH`
- `FORGE_AI_ENVIRONMENT`
- `FORGE_AI_GRAPH_DATABASE_PATH`
- `FORGE_AI_LOG_LEVEL`
- `FORGE_AI_METADATA_DATABASE_PATH`
- `FORGE_AI_NEO4J_DATABASE`
- `FORGE_AI_NEO4J_PASSWORD`
- `FORGE_AI_NEO4J_URI`
- `FORGE_AI_NEO4J_USERNAME`
- `FORGE_AI_OPENAI_API_KEY`
- `FORGE_AI_PARSER_PROVIDER`
- `FORGE_AI_EMBEDDING_BATCH_SIZE`
- `FORGE_AI_EMBEDDING_MODEL`
- `FORGE_AI_EMBEDDING_PROVIDER`
- `FORGE_AI_OLLAMA_BASE_URL`
- `FORGE_AI_OLLAMA_EMBEDDING_MODEL`
- `FORGE_AI_REPOSITORY_CHUNK_MAX_CHARS`
- `FORGE_AI_REPOSITORY_CLONE_TIMEOUT_SECONDS`
- `FORGE_AI_REPOSITORY_STORAGE_PATH`
- `FORGE_AI_REPOSITORY_ZIP_MAX_BYTES`
- `FORGE_AI_VECTOR_DATABASE_PATH`
- `FORGE_AI_VERSION`

The health endpoint is available at `/api/health`.

API errors use a stable JSON envelope and include an `X-Request-ID` response
header for correlation:

```json
{
  "error": "validation_error",
  "detail": "repository_path: Field required",
  "status_code": 422,
  "request_id": "request-id"
}
```

Clients may provide `X-Request-ID`; otherwise the backend generates one.
Unexpected failures are logged with the same request ID and returned as a
sanitized `internal_server_error` response.

Repository import endpoints:

- `POST /api/repositories/import`
- `POST /api/repositories/import/zip`
- `GET /api/repositories/imports/{import_id}`
- `POST /api/repositories/scan`
- `GET /api/repositories/imports/{import_id}/scan`
- `POST /api/repositories/metadata`
- `GET /api/repositories/metadata/{repository_id}`
- `GET /api/repositories/imports/{import_id}/metadata`
- `POST /api/repositories/parse-file`
- `POST /api/repositories/parse-import/{import_id}`
- `POST /api/repositories/dependency-graph`
- `GET /api/repositories/imports/{import_id}/dependency-graph`
- `POST /api/repositories/call-graph`
- `GET /api/repositories/imports/{import_id}/call-graph`
- `POST /api/repositories/knowledge-graph`
- `GET /api/repositories/imports/{import_id}/knowledge-graph`
- `POST /api/repositories/chunks`
- `GET /api/repositories/imports/{import_id}/chunks`
- `POST /api/repositories/embeddings`
- `GET /api/repositories/imports/{import_id}/embeddings`
- `POST /api/repositories/vector-store`
- `GET /api/repositories/imports/{import_id}/vector-store`
- `POST /api/repositories/retrieve`
- `POST /api/repositories/imports/{import_id}/retrieve`
- `POST /api/repositories/technical-debt`
- `GET /api/repositories/imports/{import_id}/technical-debt`
- `POST /api/repositories/circular-dependencies`
- `GET /api/repositories/imports/{import_id}/circular-dependencies`
- `POST /api/repositories/dead-code`
- `GET /api/repositories/imports/{import_id}/dead-code`
- `POST /api/repositories/architecture-violations`
- `GET /api/repositories/imports/{import_id}/architecture-violations`
- `POST /api/repositories/stack-trace/parse`
- `POST /api/repositories/bug-impact`
- `POST /api/repositories/imports/{import_id}/bug-impact`
- `POST /api/repositories/summary`
- `GET /api/repositories/imports/{import_id}/summary`
- `POST /api/repositories/readme`
- `GET /api/repositories/imports/{import_id}/readme`
- `POST /api/repositories/architecture-explanation`
- `POST /api/repositories/imports/{import_id}/architecture-explanation`
- `POST /api/repositories/architecture-docs`
- `POST /api/repositories/imports/{import_id}/architecture-docs`
- `POST /api/repositories/mermaid-diagrams`
- `POST /api/repositories/imports/{import_id}/mermaid-diagrams`
- `POST /api/repositories/developer-onboarding`
- `POST /api/repositories/imports/{import_id}/developer-onboarding`
- `POST /api/repositories/pr-review`
- `POST /api/repositories/imports/{import_id}/pr-review`
- `POST /api/repositories/architecture-review`
- `POST /api/repositories/imports/{import_id}/architecture-review`
- `POST /api/repositories/security-review`
- `POST /api/repositories/imports/{import_id}/security-review`
- `POST /api/repositories/question`
- `POST /api/repositories/imports/{import_id}/question`
- `POST /api/repositories/question/stream`
- `POST /api/repositories/imports/{import_id}/question/stream`
- `GET /api/repositories/conversations/{session_id}`

Parse responses include compact AST metadata and extracted source symbols.
Supported parser languages are C, C++, Go, Java, JavaScript, Python, Rust, and TypeScript.
Tree-sitter parse results are cached in process by file path, size, and
modification time to avoid repeated parsing during graph, summary, and review
workflows.
Dependency graph responses include file nodes, dependency edges, external imports,
unresolved imports, circular dependencies, and graph statistics.
Call graph responses include callable nodes, call edges, unresolved calls, recursive
calls, and graph statistics.
Knowledge graph endpoints build repository architecture nodes and relationships,
then replace the repository graph in Neo4j. If Neo4j is unavailable, the backend
falls back to an in-memory NetworkX graph and reports the selected persistence
backend in the response. Each knowledge graph build also writes a durable SQLite
snapshot for read-back and recovery.
Repository chunk endpoints generate deterministic file and symbol chunks for the
embedding pipeline without generating embeddings.
Embedding endpoints generate OpenAI embeddings for repository chunks. They require
`FORGE_AI_OPENAI_API_KEY` and default to `text-embedding-3-small`.
For demos without an OpenAI key, set `FORGE_AI_EMBEDDING_PROVIDER=ollama`, run
Ollama locally, and use `FORGE_AI_OLLAMA_EMBEDDING_MODEL=nomic-embed-text`.
Vector storage endpoints persist generated embeddings to SQLite and return compact
storage statistics instead of full vector payloads.
Hybrid retrieval endpoints search stored vectors with semantic similarity, keyword
overlap, and dependency-graph context. Run vector storage for the repository before
calling retrieval.
Technical debt endpoints analyze parsed source files and dependencies for
maintainability risks such as large files, long symbols, broad types, high fan-out,
parser errors, dependency cycles, and estimated cyclomatic complexity.
Circular dependency endpoints return dedicated file-level import cycles with
affected file counts, maximum cycle length, and the import edges in each cycle.
Dead code endpoints report conservative candidates for unreferenced source files
and uncalled functions or methods from dependency and call graph evidence.
Architecture violation endpoints flag common layer-boundary problems from import
edges, including production-to-test imports, UI-to-infrastructure imports, and
route/controller imports that skip the service layer.
Architecture review endpoints evaluate proposed changed files against dependency
impact, key architecture files, layer spread, and scoped boundary violations.
Security review endpoints evaluate changed files for static security signals such
as hardcoded secrets, dangerous execution, unsafe deserialization, weak crypto,
dynamic SQL, disabled security controls, and unsafe memory APIs.
Stack trace parsing extracts normalized frames, files, functions, line numbers,
language, error type, and message from common Python, JavaScript, Java, and Go
trace formats.
Bug impact endpoints combine parsed stack traces, changed files, and dependency
graph evidence to predict likely root cause, impacted files, confidence,
recommendations, and an explainable risk score with weighted factors.
Repository summary endpoints generate grounded repository overviews from scanner,
parser, dependency graph, call graph, and vector index metadata.
README generation endpoints turn the repository summary into Markdown sections
for overview, stats, languages, key files, notable symbols, architecture
signals, setup entry points, and Forge AI evidence.
Architecture explanation endpoints turn those grounded facts into component,
dependency-flow, call-flow, observation, evidence, and confidence sections.
Architecture documentation endpoints export those grounded architecture facts as
Markdown with overview, components, dependency flow, call flow, observations,
evidence, and confidence metadata.
Mermaid diagram endpoints generate architecture overview, dependency flow, and
call flow diagram source from the same repository graph evidence.
Developer onboarding endpoints combine generated README, architecture docs, and
Mermaid diagrams into a first-day Markdown guide with setup, key files,
workflow, validation checklist, and follow-up questions.
Pull request review endpoints evaluate changed files with dependency impact,
technical debt, architecture boundary, testing, and diff-size signals.
Repository Q&A endpoints answer questions from repository summaries, architecture
explanations, and available hybrid retrieval evidence.
Streaming Q&A endpoints return Server-Sent Events with `answer.start`,
`answer.delta`, `answer.metadata`, and `answer.done` events.
Conversation memory persists Q&A sessions to SQLite and returns a `session_id`
that can be reused on later Q&A requests.
