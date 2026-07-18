# CodeInsight Architecture

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                 │
│          23+ panels · React Flow graphs             │
│          Tabbed dashboard · Dark theme              │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│               FastAPI Backend (Python)              │
│          50+ endpoints · 25+ services               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Import   │  │ Analysis │  │ Generation       │  │
│  │ Service  │  │ Services │  │ Services         │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Parser   │  │ Graph    │  │ Embedding        │  │
│  │ Service  │  │ Service  │  │ Service          │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │
      ┌────────────────┼────────────────┐
      │                │                │
┌─────▼─────┐   ┌──────▼──────┐   ┌────▼────┐
│  SQLite   │   │  Neo4j      │   │ NetworkX│
│  (primary)│   │  (optional) │   │ (memory)│
└───────────┘   └─────────────┘   └─────────┘
```

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── core/
│   │   ├── config.py        # Settings (env vars, .env)
│   │   ├── dependencies.py  # FastAPI DI container
│   │   ├── errors.py        # Exception handlers
│   │   └── logging.py       # Structured logging
│   ├── api/
│   │   └── routes/
│   │       ├── health.py    # GET /api/health
│   │       └── repositories.py  # All repository endpoints
│   ├── services/            # 25+ service modules
│   │   ├── repository_import.py
│   │   ├── repository_scanner.py
│   │   ├── repository_qa.py
│   │   ├── repository_summary.py
│   │   ├── embedding.py
│   │   ├── retrieval.py
│   │   ├── technical_debt.py
│   │   ├── bug_impact.py
│   │   ├── dead_code.py
│   │   ├── security_review.py
│   │   └── ... (20+ more)
│   ├── schemas/             # Pydantic request/response models
│   ├── repositories/        # SQLite data access layer
│   └── database/
│       └── connection.py    # SQLite engine + WAL mode
├── graph/                   # Graph engine
│   ├── knowledge_graph.py
│   ├── dependency_graph.py
│   ├── call_graph.py
│   ├── neo4j_repository.py
│   ├── networkx_repository.py
│   ├── sqlite_repository.py
│   └── persistent_repository.py
├── parser/
│   └── tree_sitter_parser.py  # Tree-sitter + regex fallback
├── workers/
│   └── main.py              # Background worker scaffold
└── tests/                   # 177 pytest tests
```

---

## Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx             # Root page → Dashboard
│   ├── layout.tsx           # Root layout (Inter font, dark mode)
│   └── globals.css          # Tailwind CSS variables
├── components/
│   ├── dashboard.tsx        # Main dashboard with 6 tabs
│   ├── error-boundary.tsx   # React error boundary
│   ├── mermaid-diagram.tsx  # Mermaid SVG renderer
│   ├── ui/
│   │   └── button.tsx       # Shared button component
│   ├── repository-explorer.tsx
│   ├── dependency-graph-panel.tsx
│   ├── knowledge-graph-panel.tsx
│   ├── technical-debt-panel.tsx
│   ├── bug-impact-panel.tsx
│   ├── system-understanding-panel.tsx
│   ├── security-review-panel.tsx
│   ├── readme-generator-panel.tsx
│   └── ... (15+ more panels)
├── lib/
│   └── api.ts               # API client (fetch wrappers)
├── tailwind.config.ts
└── next.config.ts
```

---

## Repository Processing Pipeline

```
Import (GitHub / Local / ZIP)
    ↓
Clone / Extract
    ↓
Recursive Scan (language detection, file metadata)
    ↓
Tree-sitter Parse (8 languages) + Regex Fallback
    ↓
Symbol Extraction (functions, classes, methods, imports)
    ↓
Dependency Graph (file-level imports, cycles)
    ↓
Call Graph (function-level calls, recursion)
    ↓
Knowledge Graph (unified architecture model)
    ↓
Chunking → Embeddings (OpenAI or Ollama)
    ↓
SQLite Storage (vectors, graphs, metadata, conversations)
    ↓
Repository Ready for Q&A, Analysis, and Documentation
```

---

## AI Q&A Pipeline

```
User Question
    ↓
Intent Detection
    ↓
Hybrid Retrieval (semantic + keyword + graph)
    ↓
Relevant Files + Symbols + Dependencies
    ↓
Context Assembly (evidence-grounded prompt)
    ↓
LLM Response (GPT-5.6 via OpenAI API)
    ↓
Grounded Answer with Evidence + Confidence
```

---

## Storage Architecture

| Store          | Technology          | Purpose                                  |
| -------------- | ------------------- | ---------------------------------------- |
| **Primary DB** | SQLite + SQLAlchemy | Metadata, vectors, graphs, conversations |
| **Graph DB**   | Neo4j (optional)    | Architecture graph persistence           |
| **In-Memory**  | NetworkX            | Fast graph operations                    |
| **Embeddings** | SQLite vector store | Semantic search vectors                  |

---

## Dashboard Tabs

| Tab          | Panels                                                                                             |
| ------------ | -------------------------------------------------------------------------------------------------- |
| **Explorer** | System Understanding, Repository Search                                                            |
| **Analysis** | Technical Debt, Circular Dependencies, Dead Code, Architecture Violations, Bug Impact, Stack Trace |
| **Graphs**   | Dependency Graph, Knowledge Graph (React Flow visualization)                                       |
| **Docs**     | README Generator, Architecture Docs, Mermaid Diagrams, Developer Onboarding                        |
| **Review**   | PR Review, Architecture Review, Security Review                                                    |
| **AI Tools** | System Understanding, Repository Search (semantic + keyword + graph)                               |

---

## API Endpoints

All repository endpoints are under `/api/repositories/`:

| Method | Path                                     | Description                  |
| ------ | ---------------------------------------- | ---------------------------- |
| `GET`  | `/api/health`                            | Health check                 |
| `POST` | `/api/repositories/import`               | Import from GitHub/local/ZIP |
| `POST` | `/api/repositories/scan`                 | Scan repository files        |
| `POST` | `/api/repositories/qa`                   | Ask a question               |
| `POST` | `/api/repositories/technical-debt`       | Analyze technical debt       |
| `POST` | `/api/repositories/dead-code`            | Detect dead code             |
| `POST` | `/api/repositories/bug-impact`           | Predict bug impact           |
| `POST` | `/api/repositories/call-graph`           | Build call graph             |
| `POST` | `/api/repositories/dependency-graph`     | Build dependency graph       |
| `POST` | `/api/repositories/knowledge-graph`      | Build knowledge graph        |
| `POST` | `/api/repositories/embed`                | Generate embeddings          |
| `POST` | `/api/repositories/search`               | Hybrid search                |
| `POST` | `/api/repositories/system-understanding` | Full system report           |
| `POST` | `/api/repositories/readme`               | Generate README              |
| `POST` | `/api/repositories/architecture-docs`    | Generate architecture docs   |
| `POST` | `/api/repositories/mermaid-diagrams`     | Generate Mermaid diagrams    |
| `POST` | `/api/repositories/developer-onboarding` | Generate onboarding guide    |
| `POST` | `/api/repositories/security-review`      | Security review              |
| `POST` | `/api/repositories/pr-review`            | PR review                    |

---

## Security Principles

- Never execute repository code
- Never trust uploaded archives
- Validate all file paths
- Prevent directory traversal
- Sandbox parsing (Tree-sitter only)
- Limit upload size (100MB default)
- Protect API keys via environment variables
- CORS restricted to configured origins

---

## Design Principles

- **Single Responsibility** — each service does one thing
- **Dependency Injection** — FastAPI `Depends()` for all services
- **Repository Pattern** — data access separated from business logic
- **Immutable DTOs** — Pydantic `frozen=True` models
- **Graceful Fallback** — Neo4j → NetworkX → SQLite
- **Safe Defaults** — works without OpenAI key (Ollama mode)
- **Test Coverage** — 177 tests, 90%+ target
