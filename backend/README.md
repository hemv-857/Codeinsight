# Backend

FastAPI application code for Forge AI.

## Local Commands

- Run tests: `make test`
- Run verification: `make verify`
- Start the API locally: `.venv/bin/uvicorn backend.app.main:app --reload`

## Environment

Configuration is loaded from environment variables prefixed with `FORGE_AI_`.

- `FORGE_AI_APP_NAME`
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
