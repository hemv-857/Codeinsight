# CodeInsight — Google Maps for Software Systems

**Live Demo:** [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

## Inspiration

Every engineer has experienced the dread of joining a new codebase. You clone a repository, open your editor, and stare at hundreds of files with no idea where to begin. The documentation is outdated, the architecture is implicit, and the only way to understand the system is to read every file one by one.

We asked ourselves: **what if you could navigate a codebase the way you navigate a city — with a map?**

Traditional AI coding assistants like Copilot understand your current file. They answer "what does this function do?" but not "how does authentication work across the entire application?" That gap — between **local context** and **system understanding** — is where most engineering time disappears.

CodeInsight was born from this frustration. We wanted to build a tool that lets you zoom out and see the architecture, zoom in and see the symbols, and ask questions that span the entire codebase.

## What it does

CodeInsight is a full-stack codebase intelligence platform that imports any repository, parses source code across 8 languages, builds architectural knowledge graphs, and provides AI-powered analysis — all grounded in real repository evidence.

**Core capabilities:**

- **Repository Import** — GitHub URLs, local paths, and ZIP uploads
- **Multi-language Parsing** — Python, JavaScript, TypeScript, C, C++, Java, Go, and Rust via Tree-sitter with regex fallback
- **Graph Engine** — Dependency graph, call graph, and knowledge graph with Neo4j, NetworkX, and SQLite persistence
- **Hybrid Retrieval** — Semantic search + keyword matching + graph traversal for grounded answers
- **Repository Q&A** — Ask questions about your codebase and get evidence-cited answers with streaming responses
- **Technical Debt Detection** — Cyclomatic complexity, god objects, dead code, circular dependencies, architecture violations
- **Bug Impact Prediction** — Paste a stack trace, get affected modules, root cause analysis, and confidence scores
- **Documentation Generation** — README, architecture docs, Mermaid diagrams, and developer onboarding guides
- **Code Review** — PR review, architecture review, and security review engines
- **Dark-first Dashboard** — 23+ interactive panels with React Flow graph visualization

Try it now: [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

## How we built it

CodeInsight is a monorepo with six modules:

| Module | Technology | Purpose |
|--------|-----------|---------|
| `frontend/` | Next.js, React, TypeScript, Tailwind CSS, React Flow | Dark-themed dashboard with 23+ panels |
| `backend/` | FastAPI, Pydantic, SQLite | 50+ API endpoints, 25+ services |
| `parser/` | Tree-sitter, Python | Multi-language source code parsing |
| `graph/` | Neo4j, NetworkX, SQLite | Knowledge, dependency, and call graph engines |
| `shared/` | TypeScript, Python | Shared types and utilities |
| `workers/` | Python | Background processing scaffold |

**The processing pipeline:**

```
Import → Clone → Scan → Parse → Extract Symbols
→ Build Graphs → Chunk → Embed → Store → Ready
```

**Key architectural decisions:**

1. **Triple persistence** — Neo4j (optional) → NetworkX (in-memory) → SQLite (primary). The app works with zero configuration.
2. **Hybrid retrieval** — Combines semantic embeddings, keyword matching, and graph traversal for grounded answers instead of hallucinated responses.
3. **Tree-sitter + regex fallback** — Native grammars when available, portable regex patterns when not.
4. **OpenAI + Ollama** — Works with or without an API key. Local demos use Ollama for embeddings.

**Quality gate:** `make verify` runs formatting, linting, mypy strict, 90%+ coverage-gated tests, Next.js production build, and Docker Compose validation.

## Challenges we ran into

**1. Python 3.14 Segfaults**
Python 3.14.6 segfaults in worker threads while scanning repositories on macOS. This was a showstopper for live demos. Fixed by pinning Docker images to Python 3.13 and defaulting to the safe regex parser for demos.

**2. Vector Store Crash**
Inserting all embeddings in a single transaction caused SQLite to run out of memory on large repositories. Solved with batched inserts — chunking the embedding vector table into manageable batches.

**3. Non-Atomic Graph Operations**
Replacing an entire graph in one transaction caused data corruption on concurrent access. Implemented batched inserts with WAL (Write-Ahead Logging) mode for concurrent reads during writes.

**4. CORS Hardcoded to Localhost**
CORS was hardcoded to `localhost:3000` during early development, breaking Docker deployments. Made CORS origins configurable via environment variables.

**5. Parser Accuracy**
The safe regex parser initially missed multi-import statements, included comments in symbol extraction, and counted function declarations as calls. Required careful iteration on scope tracking, declaration separation, and import chain detection.

**6. Graph Visualization at Scale**
Rendering hundreds of nodes in React Flow required lazy loading, virtualized rendering, and interactive zoom/pan controls to maintain 60 FPS performance.

## Accomplishments that we're proud of

- **177 tests with 90%+ coverage gate** — Every PR must pass `make verify` before merge
- **Zero-config local demo** — Works without Neo4j, without an OpenAI key, just Python and Node.js
- **Real answers grounded in code** — Every Q&A response cites specific files, functions, and lines
- **8 languages parsed** — Python, JavaScript, TypeScript, C, C++, Java, Go, Rust with one unified API
- **25+ backend services** — From repository import to bug impact prediction to documentation generation
- **23+ frontend panels** — Dark-themed dashboard with interactive graph visualization
- **Production-ready architecture** — Docker Compose, health checks, structured logging, CORS, error recovery
- **Streaming Q&A** — Users see answers as they generate, not after a long wait
- **Live and deployed** — [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

## What we learned

**Graph structure is non-negotiable.** Source code is not just text — it is a graph. Every import creates an edge. Every function call creates a relationship. Traditional grep-based search and file-tree navigation fundamentally cannot answer questions about system behavior.

**Hybrid retrieval beats pure vector search.** Pure embedding search produces hallucinated answers. Pure keyword search misses semantic connections. Grounded answers require combining semantic, keyword, and graph signals.

$$
\text{score}(q, d) = \alpha \cdot \text{semantic}(q, d) + \beta \cdot \text{keyword}(q, d) + \gamma \cdot \text{graph}(q, d)
$$

**Graceful degradation is a core principle.** Neo4j → NetworkX → SQLite. Tree-sitter → regex. OpenAI → Ollama. Every dependency has a fallback so the app always works.

**Documentation is a feature, not an afterthought.** Generating README, architecture docs, and onboarding guides from real repository evidence produces better documentation than manual writing.

## What's next for CodeInsight - Google Maps for Software Systems

- **Incremental indexing** — Re-index only changed files instead of full repository scans
- **Live repository monitoring** — Watch for changes and update graphs in real-time
- **CI/CD integration** — GitHub Actions bot that comments on PRs with impact analysis
- **Team collaboration** — Shared repositories with conversation history
- **Plugin marketplace** — Community-contributed language parsers and analysis engines
- **Cloud hosting** — Managed version with persistent storage and team features
- **Architecture decision records** — Auto-generate ADRs from code changes
- **Cross-repository analysis** — Understand dependencies across multiple repositories in a monorepo or organization

---

**Try CodeInsight:** [codeinsight-iota.vercel.app](https://codeinsight-iota.vercel.app/)

*Built for the OpenAI Hackathon · Developer Tools Track*
*Codex Session: `019f69f5-05dd-7bc2-9303-f1ba8c7486cf`*
