# Backend

FastAPI application code for Forge AI.

## Local Commands

- Run tests: `make test`
- Run verification: `make verify`
- Start the API locally: `.venv/bin/uvicorn backend.app.main:app --reload`

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
- `POST /api/repositories/architecture-explanation`
- `POST /api/repositories/imports/{import_id}/architecture-explanation`
- `POST /api/repositories/question`
- `POST /api/repositories/imports/{import_id}/question`
- `POST /api/repositories/question/stream`
- `POST /api/repositories/imports/{import_id}/question/stream`
- `GET /api/repositories/conversations/{session_id}`

Parse responses include compact AST metadata and extracted source symbols.
Supported parser languages are C, C++, Go, Java, JavaScript, Python, Rust, and TypeScript.
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
Stack trace parsing extracts normalized frames, files, functions, line numbers,
language, error type, and message from common Python, JavaScript, Java, and Go
trace formats.
Bug impact endpoints combine parsed stack traces, changed files, and dependency
graph evidence to predict likely root cause, impacted files, confidence,
recommendations, and a provisional risk score.
Repository summary endpoints generate grounded repository overviews from scanner,
parser, dependency graph, call graph, and vector index metadata.
Architecture explanation endpoints turn those grounded facts into component,
dependency-flow, call-flow, observation, evidence, and confidence sections.
Repository Q&A endpoints answer questions from repository summaries, architecture
explanations, and available hybrid retrieval evidence.
Streaming Q&A endpoints return Server-Sent Events with `answer.start`,
`answer.delta`, `answer.metadata`, and `answer.done` events.
Conversation memory persists Q&A sessions to SQLite and returns a `session_id`
that can be reused on later Q&A requests.
