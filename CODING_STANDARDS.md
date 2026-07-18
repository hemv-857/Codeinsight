# CodeInsight Coding Standards

---

# Philosophy

Write software that another engineer can confidently maintain ten years from now.

Code should prioritize:

Correctness

Readability

Maintainability

Performance

Testability

Security

---

# General Rules

Never write placeholder code.

Never leave TODO comments.

Never ignore exceptions.

Never duplicate logic.

Never use magic numbers.

Prefer composition over inheritance.

Always use meaningful names.

Avoid premature optimization.

---

# Function Rules

Functions should have one responsibility.

Prefer fewer than 50 lines.

Return early.

Avoid deep nesting.

Document public APIs.

Avoid side effects.

---

# Class Rules

Small cohesive classes.

Constructor injection.

No God objects.

Single responsibility.

High cohesion.

Low coupling.

---

# Architecture

Business logic belongs in services.

Database logic belongs in repositories.

Routes only coordinate requests.

Never place business logic inside UI components.

Keep modules independent.

---

# Type Safety

Python

Use type hints everywhere.

Run mypy-compatible code.

TypeScript

Strict mode enabled.

Avoid any.

Prefer interfaces.

Use discriminated unions when appropriate.

---

# Error Handling

Never swallow exceptions.

Log failures.

Return meaningful errors.

Gracefully recover when possible.

Validate all external input.

---

# Security

Validate every upload.

Escape paths.

Sanitize user input.

Never execute repository code.

Protect secrets.

Never expose stack traces to users.

---

# Testing

Every feature requires tests.

Unit tests

Integration tests

Regression tests

Target coverage above 90%.

Tests must be deterministic.

No flaky tests.

---

# Performance

Avoid unnecessary allocations.

Cache expensive operations.

Lazy load large datasets.

Batch database operations.

Use async IO where appropriate.

Profile before optimizing.

---

# Documentation

Every module documented.

Every API documented.

README updated after major changes.

Architecture diagrams updated after structural changes.

---

# Git

Small commits.

Atomic commits.

Descriptive commit messages.

No unrelated changes in one commit.

---

# Code Review Checklist

Before marking work complete verify:

✓ Builds successfully

✓ Tests pass

✓ Lint passes

✓ Formatting passes

✓ No duplicate code

✓ No dead code

✓ Documentation updated

✓ Type checks pass

✓ No security issues introduced

✓ Performance impact considered

---

# Definition of Done

A feature is complete only if:

- It is implemented.
- It is tested.
- It is documented.
- It passes linting.
- It passes formatting.
- It passes type checking.
- It integrates with the existing architecture.
- It includes error handling.
- It includes logging where appropriate.
- It requires no placeholder implementation.
