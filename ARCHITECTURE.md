# Forge AI Architecture

---

# High-Level Architecture

                    Frontend
                 (Next.js + React)
                         │
                         │
             REST API / WebSocket
                         │
                    FastAPI Backend
                         │
        ┌─────────────────────────────────┐
        │                                 │
        │        Service Layer            │
        │                                 │
        ├─────────────────────────────────┤
        │ Repository Service              │
        │ Parser Service                  │
        │ Graph Service                   │
        │ Embedding Service               │
        │ Search Service                  │
        │ AI Service                      │
        │ Documentation Service           │
        │ Metrics Service                 │
        └─────────────────────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │

PostgreSQL Neo4j Vector Store
│ │ │
└──────────── Redis Cache ────────────┘

---

# Backend Modules

backend/

api/

core/

config/

database/

repositories/

services/

models/

schemas/

workers/

utils/

tests/

---

# Frontend

frontend/

components/

pages/

hooks/

stores/

services/

layouts/

graphs/

editor/

chat/

dashboard/

---

# Repository Processing Pipeline

Repository Import

↓

Repository Validation

↓

Clone

↓

File Discovery

↓

Language Detection

↓

Tree-sitter Parsing

↓

AST Generation

↓

Dependency Extraction

↓

Call Graph Construction

↓

Knowledge Graph Generation

↓

Embeddings

↓

Database Storage

↓

Repository Ready

---

# AI Request Pipeline

Question

↓

Intent Detection

↓

Hybrid Search

↓

Graph Traversal

↓

Relevant Files

↓

Relevant Symbols

↓

Architecture Context

↓

Prompt Assembly

↓

GPT-5.6

↓

Grounded Response

↓

Evidence Returned

---

# Storage

## PostgreSQL

Repository metadata

Files

Symbols

Metrics

Search index

User settings

---

## Neo4j

Architecture graph

Dependencies

Call graph

Relationships

Ownership graph

---

## Redis

Cache

Streaming state

Background jobs

Temporary sessions

---

# API Design

/api/repositories

/api/search

/api/chat

/api/graph

/api/docs

/api/debt

/api/metrics

/api/review

/api/health

---

# Background Workers

Repository indexing

Embedding generation

Graph updates

Documentation generation

Metric calculation

Scheduled cleanup

---

# Security

Never execute repository code.

Never trust uploaded archives.

Validate paths.

Prevent directory traversal.

Sandbox parsing.

Limit upload size.

Protect secrets.

---

# Scalability

Stateless backend.

Horizontal worker scaling.

Independent parser service.

Independent embedding service.

Independent graph service.

Streaming responses.

Incremental indexing.

Caching.

---

# Design Principles

Single Responsibility

Dependency Injection

Repository Pattern

Service Layer

Typed Interfaces

Immutable DTOs

Async-first

Testable architecture

No business logic inside controllers.

No database logic inside routes.

No UI logic inside API layer.
