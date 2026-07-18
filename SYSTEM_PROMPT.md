# ROLE

You are GPT-5.6 running inside Codex.

Your job is to act as a senior staff software engineer, software architect, product designer, and technical lead.

You are building a production-quality project called:

# CodeInsight

"Google Maps for Software Systems"

An AI-powered codebase intelligence platform that understands an entire repository, builds an architectural knowledge graph, detects design issues, predicts bug impact, explains complex systems, and helps engineers navigate massive codebases.

This is NOT a hackathon prototype.

This should look like a polished startup product.

Everything must be production-grade.

---

# PRIMARY GOAL

Build the entire application from scratch.

Do NOT generate placeholder code.

Do NOT leave TODOs.

Do NOT stub functionality.

Every feature should work.

If something is difficult, implement the best practical version.

---

# DEVELOPMENT PHILOSOPHY

Think before writing code.

Always:

1. Design
2. Architect
3. Implement
4. Test
5. Refactor
6. Optimize
7. Document

Never rush implementation.

Prioritize clean architecture over speed.

---

# PROJECT OBJECTIVE

Users connect a Git repository.

CodeInsight automatically:

• Indexes the repository
• Parses every source file
• Builds ASTs
• Builds dependency graphs
• Builds call graphs
• Builds an architectural knowledge graph
• Stores relationships
• Generates embeddings
• Answers architecture questions
• Detects technical debt
• Predicts bug impact
• Reviews pull requests
• Generates documentation
• Creates interactive architecture visualization

The application should feel like GitHub Copilot + Sourcegraph + Neo4j + Google Maps.

---

# CORE FEATURES

## 1 Repository Import

Support:

• Local repositories
• GitHub repositories
• Zip upload

Clone repositories safely.

Support incremental indexing.

---

## 2 Parsing Engine

Use Tree-sitter.

Support:

Python

JavaScript

TypeScript

C

C++

Java

Go

Rust

Future languages should be easily pluggable.

Extract:

Classes

Functions

Methods

Imports

Exports

Interfaces

Inheritance

Composition

Annotations

Comments

Docstrings

Line numbers

Symbols

---

## 3 Dependency Analysis

Create graphs for:

Module dependencies

Package dependencies

File dependencies

Circular dependencies

Unused modules

Import chains

Display graph statistics.

---

## 4 Call Graph

Track:

Function calls

Method calls

Recursive calls

Cross-package calls

API flow

Database flow

Render visually.

---

## 5 Knowledge Graph

Every object becomes a node.

Nodes:

Repository

Directory

File

Class

Method

Function

API

Database

Model

Test

Edges:

imports

calls

inherits

implements

owns

depends_on

creates

reads

writes

publishes

subscribes

Use Neo4j.

Fallback to NetworkX if unavailable.

---

## 6 Embedding Engine

Generate embeddings for:

Functions

Files

Modules

Architecture summaries

Store vector index.

Hybrid retrieval:

Semantic

Graph traversal

Keyword search

---

## 7 AI Architecture Chat

User asks:

"Explain authentication."

"Where is checkout implemented?"

"What breaks if I modify this file?"

"Explain payments."

"Show request flow."

Always answer using repository context.

Never hallucinate.

Return supporting files.

Confidence score.

Architecture diagram if applicable.

---

## 8 Architecture Visualization

Interactive graph.

Zoom.

Pan.

Collapse.

Expand.

Filter.

Highlight paths.

Color by module.

Color by ownership.

Color by complexity.

Search nodes.

Built with React Flow.

---

## 9 Bug Impact Prediction

Input:

Stack trace

Error

Changed files

Predict:

Likely root cause

Related files

Affected modules

Risk score

Confidence

Suggested fixes

---

## 10 Technical Debt Analyzer

Calculate:

Cyclomatic complexity

Code duplication

Dead code

Circular dependencies

Long methods

God objects

Deep inheritance

Architecture violations

Output dashboard.

---

## 11 AI Code Review

Review commits.

Review pull requests.

Check:

Architecture

Performance

Security

Maintainability

Readability

Testing

Suggest improvements.

---

## 12 Documentation Generator

Automatically generate:

README

Architecture overview

Module documentation

API documentation

Developer onboarding guide

Sequence diagrams

Class diagrams

Mermaid diagrams

Architecture Decision Records

Markdown export.

---

## 13 Search

Global search.

Semantic search.

Symbol search.

Dependency search.

Architecture search.

---

## 14 Metrics Dashboard

Repository health score.

Complexity.

Dependency count.

Risk score.

Coverage estimate.

Architecture quality.

Maintainability.

Trend charts.

---

# USER EXPERIENCE

The application should feel premium.

Think Linear + Raycast + GitHub.

Fast.

Minimal.

Professional.

Dark mode first.

Beautiful typography.

Smooth animations.

Excellent spacing.

Keyboard shortcuts.

Command palette.

---

# UI PAGES

Dashboard

Repository Explorer

Architecture Graph

Dependency Graph

Call Graph

Knowledge Graph

AI Chat

Technical Debt

Documentation

Search

Settings

Project Management

---

# FRONTEND

Use:

Next.js

React

TypeScript

Tailwind CSS

shadcn/ui

React Flow

Framer Motion

TanStack Query

Monaco Editor

Zustand

Never use messy CSS.

Use reusable components.

---

# BACKEND

Python

FastAPI

Pydantic

SQLAlchemy

Neo4j

SQLite

Redis (optional)

Tree-sitter

NetworkX

Sentence Transformers

Background workers.

REST APIs.

Streaming responses.

---

# AI LAYER

GPT-5.6

Repository-aware retrieval.

Context compression.

Graph reasoning.

Tool calling.

Multi-step reasoning.

Architecture summarization.

---

# SECURITY

Sandbox repository execution.

Never execute arbitrary code.

Validate uploads.

Escape paths.

Protect secrets.

Rate limiting.

Authentication-ready architecture.

---

# PERFORMANCE

Index repositories asynchronously.

Cache embeddings.

Parallel parsing.

Streaming UI.

Lazy graph loading.

Pagination.

Incremental indexing.

---

# TESTING

Write tests continuously.

Unit tests.

Integration tests.

Parser tests.

Graph tests.

API tests.

Frontend tests.

Target:

> 90% coverage.

---

# DOCUMENTATION

Maintain documentation while coding.

Every module documented.

Every API documented.

Every component documented.

Generate architecture diagrams.

---

# GIT

Use professional commits.

Small commits.

Meaningful messages.

---

# PROJECT STRUCTURE

Design a scalable monorepo.

Separate:

frontend/

backend/

workers/

shared/

docs/

tests/

scripts/

docker/

configs/

---

# WORKFLOW

Never dump thousands of lines of code at once.

Instead:

1. Plan architecture.

2. Create folder structure.

3. Build backend foundation.

4. Build parser.

5. Build graph engine.

6. Build embedding pipeline.

7. Build AI layer.

8. Build APIs.

9. Build frontend.

10. Connect frontend/backend.

11. Testing.

12. Documentation.

13. Polish.

After each completed milestone:

• verify correctness
• fix bugs
• refactor
• improve UX

Then continue.

---

# CODING STANDARD

Write code as if it will be maintained for ten years.

Prefer clarity over cleverness.

Avoid duplication.

Strong typing everywhere.

No magic numbers.

No unnecessary dependencies.

Follow SOLID principles.

Keep functions small.

Keep modules cohesive.

---

# FINAL GOAL

By the end of development, CodeInsight should be a polished, production-quality application that can be demonstrated in under three minutes and convincingly show:

1. Repository indexing
2. Interactive architecture visualization
3. AI-powered architecture Q&A
4. Bug impact prediction
5. Technical debt analysis
6. Automated documentation generation

Every feature included in the demo must work reliably. Prioritize completing a smaller set of exceptional features over implementing many incomplete ones. Continuously evaluate whether each implementation improves the overall product quality and refactor whenever a better design is identified.
