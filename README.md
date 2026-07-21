# CodeInsight

> **OpenAI Hackathon Submission — Developer Tools Track**

CodeInsight is "Google Maps for Software Systems": a dark-first codebase
intelligence app that imports repositories, parses source code, builds graph
views, answers repository questions, predicts bug impact, reviews changes, and
generates documentation from real repository evidence.

**Live Demo:** [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

## Built with Codex

**Codex Session ID:** `019f69f5-05dd-7bc2-9303-f1ba8c7486cf`

Codex with GPT-5.6 was the primary development accelerator for CodeInsight. Here's how it was used:

### Architecture & Scaffolding

- Codex designed the full monorepo structure (`frontend/`, `backend/`, `parser/`, `graph/`, `shared/`, `workers/`) and generated the initial scaffolding for all modules
- Generated the FastAPI application factory, dependency injection container, and Pydantic schema layer from a high-level feature spec
- Created the Docker Compose orchestration with 5 services, health checks, and persistent volumes

### Core Intelligence Pipeline

- **Parser** (`parser/tree_sitter_parser.py`): Codex implemented the Tree-sitter multi-language parser with safe regex fallback for 8 languages (Python, JS, TS, C, C++, Java, Go, Rust)
- **Graph Engine** (`graph/`): Generated the knowledge graph, dependency graph, and call graph builders with Neo4j primary, NetworkX in-memory, and SQLite persistence layers
- **Embedding & Retrieval** (`backend/app/services/embedding.py`, `retrieval.py`, `vector_store.py`): Built the hybrid retrieval system combining semantic search, keyword matching, and graph traversal

### 25+ Backend Services

Codex generated the implementation for every service module:

- `repository_import.py` — GitHub, local path, and ZIP upload ingestion
- `repository_qa.py` — grounded Q&A with streaming responses and conversation memory
- `technical_debt.py`, `bug_impact.py`, `risk_scoring.py` — codebase analysis engines
- `security_review.py`, `pull_request_review.py`, `architecture_explanation.py`
- `readme_generator.py`, `architecture_docs.py`, `mermaid_diagrams.py`, `developer_onboarding.py`

### Frontend (23+ Panels)

- Codex built the dark-themed dashboard with React Flow graph visualization, TanStack Query data fetching, and Framer Motion animations
- Generated all interactive panels: repository explorer, dependency graph, knowledge graph, bug impact, technical debt, security review, architecture docs, README generator, and more
- Implemented the streaming Q&A interface and conversation history UI

### Quality & DevOps

- Codex set up the `make verify` release gate: formatting, linting, mypy strict, 90%+ coverage-gated tests, Next.js production build, Docker Compose validation
- Generated 45+ pytest test files covering parser, graph, service, and API layers
- Created the CI scripts, coverage enforcement, and Dockerfiles

### Key Decisions Made with Codex

1. **Neo4j + NetworkX + SQLite triple persistence**: Codex evaluated tradeoffs and implemented graceful fallback (Neo4j → NetworkX → SQLite) for zero-config local demos
2. **Hybrid retrieval over pure vector search**: Codex recommended combining semantic embeddings with keyword matching and graph traversal for grounded answers
3. **Tree-sitter + regex fallback**: Codex designed the parser to use native Tree-sitter when available but fall back to regex patterns for portability
4. **OpenAI + Ollama embedding support**: Codex implemented provider abstraction so the app works with or without an OpenAI API key

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
.venv313/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

Run the dashboard:

```bash
npm run dev --workspace @codeinsight/frontend
```

For local demos, point the frontend at the backend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8002 npm run dev --workspace @codeinsight/frontend -- --port 3002
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

OpenAI embeddings require `CODEINSIGHT_OPENAI_API_KEY`.

For local demos without an OpenAI key:

```bash
export CODEINSIGHT_EMBEDDING_PROVIDER=ollama
export CODEINSIGHT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Then run Ollama locally before vector indexing.

## Demo

**Live App:** [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

Use the official flow in [DEMO.md](DEMO.md). The recommended real demo
repository is FastAPI because it is large enough to exercise parsing, graphs,
search, documentation, Q&A, debt, and bug analysis without being too large for
a short recording.

Release assets:

- [Architecture diagrams](docs/architecture-diagrams.md)
- [Demo repository setup](docs/demo-repository.md)
- [Production release checklist](docs/production-release.md)
- [Dashboard screenshot](docs/screenshots/dashboard.png)

## Documentation

| Document                                   | Description                                         |
| ------------------------------------------ | --------------------------------------------------- |
| [ARCHITECTURE.md](ARCHITECTURE.md)         | System architecture, modules, and design principles |
| [PRODUCT_SPEC.md](PRODUCT_SPEC.md)         | Product specification and requirements              |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | Code style, testing, and quality standards          |
| [CONTRIBUTING.md](CONTRIBUTING.md)         | How to contribute to the project                    |
| [SECURITY.md](SECURITY.md)                 | Security policy and vulnerability reporting         |
| [CHANGELOG.md](CHANGELOG.md)               | Version history and changes                         |
| [DEMO.md](DEMO.md)                         | Demo script and recording guide                     |
| [TASKS.md](TASKS.md)                       | Development roadmap and milestones                  |
| [LICENSE](LICENSE)                         | MIT License                                         |

## Verification Status

The release gate is `make verify`, which runs formatting checks, linting, type
checking, coverage-gated Python tests, the Next.js production build, and Docker
Compose config validation.

Current quality target: Python coverage above 90%.

Note: avoid Python 3.14 for local backend demos on macOS. Python 3.14.6 can
segfault in worker threads while scanning repositories. CodeInsight defaults to
the crash-resistant safe parser for live demos. Set
`CODEINSIGHT_PARSER_PROVIDER=tree_sitter` only when the native Tree-sitter bindings
are stable on your machine.

---

## Hackathon Submission

| Field                | Value                                           |
| -------------------- | ----------------------------------------------- |
| **Track**            | Developer Tools                                 |
| **Project**          | CodeInsight — Google Maps for Software Systems  |
| **Live Demo**        | [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/) |
| **Codex Session ID** | `019f69f5-05dd-7bc2-9303-f1ba8c7486cf`          |
| **Demo Video**       | [YouTube](https://www.youtube.com/watch?v=nFeFmnWsQbw)         |
| **Repository**       | [GitHub](https://github.com/hemv-857/Codeinsight) |

### What We Built

A full-stack codebase intelligence platform that imports any repository, parses source code across 8 languages, builds architectural knowledge graphs, and provides AI-powered Q&A, bug impact analysis, technical debt detection, security reviews, and documentation generation — all grounded in real repository evidence.

### How Codex Was Used

Codex with GPT-5.6 was used to build the entire application — from architecture design and scaffolding through implementing 25+ backend services, 23+ frontend panels, a multi-language parser, graph engines, hybrid retrieval, and production DevOps. See the **Built with Codex** section above for the full breakdown.
