# Changelog

All notable changes to CodeInsight will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-07-16

### Added

#### Core Platform

- Repository import from GitHub, local paths, and ZIP uploads
- Recursive file scanning with language detection (8 languages)
- Tree-sitter parser with regex-based safe fallback
- SQLite primary storage with optional Neo4j graph persistence

#### Graph Engine

- Dependency graph construction from imports
- Call graph construction from function calls
- Knowledge graph with unified architecture model
- NetworkX in-memory fallback when Neo4j unavailable
- SQLite graph persistence with WAL mode

#### Analysis Services

- Technical debt detection with severity scoring
- Dead code detection (unused files and functions)
- Circular dependency detection
- Architecture violation detection
- Bug impact prediction from stack traces
- Security review with pattern-based scanning
- Stack trace parser (Python, JavaScript, Java, Go)

#### Documentation Generation

- README generator from repository facts
- Architecture documentation generator
- Mermaid diagram generation (architecture, dependency, call flow)
- Developer onboarding guide generator

#### AI Features

- Repository Q&A with evidence-grounded answers
- Hybrid retrieval (semantic + keyword + graph search)
- System understanding report generation
- Open source contribution analysis (bug detection, code smells, security issues)

#### Frontend

- 23+ panel components with dark theme
- 6-tab dashboard (Explorer, Analysis, Graphs, Docs, Review, AI Tools)
- React Flow graph visualization
- Mermaid diagram rendering with SVG export
- Error boundary with retry UI
- Clipboard copy feedback

#### DevOps

- Docker Compose stack (backend, frontend, Neo4j, worker)
- Python 3.13 Docker images (fixed 3.14 segfault)
- SQLite WAL mode for concurrent access
- CORS configuration via environment variables

#### Quality

- 177 pytest tests with 90%+ coverage gate
- mypy strict type checking
- ruff linting
- Next.js production build verification

### Fixed

- Vector store unbounded INSERT crash (batched inserts)
- CORS hardcoded to localhost (configurable origins)
- Non-atomic SQLite graph replace (batched inserts)
- Dependency graph refresh button (hardcoded path)
- Knowledge graph refresh button (hardcoded path)
- Embedding error message for non-OpenAI providers
- Safe parser multi-import dropping, comment filtering, scope tracking
- Function declarations counted as calls in parser
- Docker Python 3.14 → 3.13 (segfault fix)
- Docker missing graph/ and parser/ modules

### Removed

- Redis from Docker Compose (unused)
- Architecture preview component (dead code)
