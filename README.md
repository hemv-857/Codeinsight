# Forge AI

Forge AI is "Google Maps for Software Systems": a dark-first codebase
intelligence app that imports repositories, parses source code, builds graph
views, answers repository questions, predicts bug impact, reviews changes, and
generates documentation from real repository evidence.

## What Works

- Repository import from local paths, GitHub URLs, and zip uploads
- Recursive repository scanning with language, file, directory, and extension metadata
- Tree-sitter parsing for Python, JavaScript, TypeScript, C, C++, Java, Go, and Rust
- Symbol extraction for functions, classes, methods, variables, imports, exports, inheritance, and interfaces
- Dependency graph, call graph, knowledge graph, Neo4j integration, NetworkX fallback, and SQLite graph persistence
- Repository chunking, OpenAI or Ollama embeddings, SQLite vector storage, and hybrid retrieval
- Repository summaries, architecture explanations, grounded Q&A, streaming responses, and conversation memory
- Repository explorer, search, dependency graph UI, knowledge graph UI, and interactive graph controls
- Technical debt, complexity, circular dependency, dead code, architecture violation, bug impact, risk scoring, PR review, architecture review, and security review
- README, architecture docs, Mermaid diagrams, and developer onboarding generation
- Structured API errors, accessibility affordances, production logging, Docker Compose, and coverage-gated verification

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, TanStack Query, React Flow, Framer Motion
- Backend: FastAPI, Pydantic, SQLite, Tree-sitter, NetworkX, Neo4j driver, OpenAI-compatible embeddings
- Worker: Python health service scaffold for background processing
- Infrastructure: Docker Compose with frontend, backend, worker, Neo4j, Redis, and durable volumes

## Quick Start

Install dependencies:

```bash
npm install
python3.13 -m venv .venv313
.venv313/bin/pip install -r requirements-dev.txt
```

Run the backend:

```bash
FORGE_AI_PARSER_PROVIDER=safe .venv313/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

Run the dashboard:

```bash
npm run dev --workspace @forge-ai/frontend
```

For local demos, point the frontend at the backend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8002 npm run dev --workspace @forge-ai/frontend -- --port 3002
```

Open the dashboard at `http://localhost:3002`.

Run the full release verifier:

```bash
make verify
```

## Docker

Validate the stack:

```bash
docker-compose config
```

Build runtime images:

```bash
make docker-build
```

Start the stack:

```bash
docker-compose up --build
```

## Embeddings

OpenAI embeddings require `FORGE_AI_OPENAI_API_KEY`.

For local demos without an OpenAI key:

```bash
export FORGE_AI_EMBEDDING_PROVIDER=ollama
export FORGE_AI_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Then run Ollama locally before vector indexing.

## Demo

Use the official flow in [DEMO.md](DEMO.md). The recommended real demo
repository is FastAPI because it is large enough to exercise parsing, graphs,
search, documentation, Q&A, debt, and bug analysis without being too large for
a short recording.

Release assets:

- [Architecture diagrams](docs/architecture-diagrams.md)
- [Demo repository setup](docs/demo-repository.md)
- [Production release checklist](docs/production-release.md)
- [Dashboard screenshot](docs/screenshots/dashboard.png)

## Verification Status

The release gate is `make verify`, which runs formatting checks, linting, type
checking, coverage-gated Python tests, the Next.js production build, and Docker
Compose config validation.

Current quality target: Python coverage above 90%.

Note: avoid Python 3.14 for local backend demos on macOS. Python 3.14.6 can
segfault in worker threads while scanning repositories. Use
`FORGE_AI_PARSER_PROVIDER=safe` for live demos if native Tree-sitter bindings
crash while parsing a large repository.
