# Production Release

Milestone 50 packages Forge AI for demonstration and release review.

## Release Artifacts

- Root README: `README.md`
- Architecture diagrams: `docs/architecture-diagrams.md`
- Dashboard screenshot: `docs/screenshots/dashboard.png`
- Demo repository guide: `docs/demo-repository.md`
- Final release checklist: this document

## Build Verification

Run the full release gate:

```bash
make verify
```

The gate includes:

- Prettier, Black, and Ruff format checks
- ESLint and Ruff linting
- TypeScript and mypy type checks
- Python tests with at least 90% coverage
- Next.js production build
- Docker Compose config validation

## Runtime Verification

Start the backend:

```bash
.venv313/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

Start the frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8002 npm run dev --workspace @forge-ai/frontend -- --port 3002
```

Optional full stack:

```bash
docker-compose up --build
```

## Demo Checklist

- Prepare a real repository before recording.
- Scan and index the repository before the demo.
- Cache embeddings before the demo if using semantic search.
- Keep the dashboard in dark mode.
- Use a large browser viewport.
- Show repository explorer, dependency graph, knowledge graph, Q&A, bug impact,
  technical debt, search, and documentation generation.
- Avoid terminal clutter and debug logs in the recording.

## Operational Notes

- OpenAI embeddings require `FORGE_AI_OPENAI_API_KEY`.
- Local demos can use Ollama via `FORGE_AI_EMBEDDING_PROVIDER=ollama`.
- Neo4j is optional at runtime; the backend falls back to NetworkX and writes
  durable graph snapshots to SQLite.
- API errors return structured JSON envelopes with `X-Request-ID` correlation.
- Use Python 3.13 for local macOS demos; Python 3.14.6 can segfault while
  scanning repositories from AnyIO worker threads.
