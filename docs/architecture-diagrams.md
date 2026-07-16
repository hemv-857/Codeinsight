# Architecture Diagrams

These Mermaid diagrams summarize the production release architecture and demo
workflow for Forge AI.

## Runtime Architecture

```mermaid
flowchart LR
  user[Developer] --> frontend[Next.js Dashboard]
  frontend --> api[FastAPI Backend]
  api --> services[Service Layer]
  services --> parser[Tree-sitter Parser]
  services --> metadata[(SQLite Metadata)]
  services --> vectors[(SQLite Vector Store)]
  services --> graph[Graph Engine]
  graph --> neo4j[(Neo4j)]
  graph --> networkx[NetworkX Fallback]
  api --> worker[Worker Health Service]
  worker --> redis[(Redis)]
```

## Repository Intelligence Pipeline

```mermaid
flowchart TB
  import[Repository Import] --> scan[Recursive Scan]
  scan --> metadata[Metadata Storage]
  scan --> parse[Tree-sitter Parse]
  parse --> symbols[Symbol Extraction]
  symbols --> deps[Dependency Graph]
  symbols --> calls[Call Graph]
  deps --> knowledge[Knowledge Graph]
  calls --> knowledge
  parse --> chunks[Repository Chunks]
  chunks --> embeddings[Embeddings]
  embeddings --> vectors[Vector Storage]
  vectors --> retrieval[Hybrid Retrieval]
  knowledge --> retrieval
  retrieval --> qa[Repository Q&A]
```

## Demo Workflow

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant UI as Forge AI Dashboard
  participant API as FastAPI API
  participant Graph as Graph Services
  participant AI as Repository Intelligence

  Dev->>UI: Import or select demo repository
  UI->>API: Scan, parse, index
  API->>Graph: Build dependency, call, and knowledge graphs
  API->>AI: Store chunks and retrieval evidence
  Dev->>UI: Ask architecture or bug question
  UI->>API: Request grounded answer
  API->>AI: Retrieve files, symbols, graph context
  AI-->>API: Answer with evidence and confidence
  API-->>UI: Render answer, affected files, and risks
```
