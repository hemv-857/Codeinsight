# Contributing to CodeInsight

Thank you for your interest in contributing to CodeInsight! This document provides guidelines for contributing.

## Development Setup

### Prerequisites

- Python 3.13+ (avoid 3.14 — known segfault)
- Node.js 22+
- Docker and Docker Compose (optional, for containerized development)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/hemang/codeinsight.git
cd codeinsight

# Create Python virtual environment
python3.13 -m venv .venv313
source .venv313/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Copy environment config
cp .env.example .env

# Run verification
make verify
```

### Running the App

```bash
# Terminal 1: Backend (port 8002)
.venv313/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 2: Frontend (port 3002)
cd frontend && npm run dev -- --port 3002
```

## Code Standards

- **Python**: Follow `CODING_STANDARDS.md`. All code must pass `ruff`, `mypy`, and `pytest`.
- **TypeScript**: Follow existing patterns. All code must pass `tsc --noEmit` and `next build`.
- **No TODOs**: Never leave TODO comments in code.
- **No eval/exec**: Never use `eval()` or `exec()` in production code.
- **Type safety**: Use strict typing in both Python and TypeScript.

## Testing

```bash
# Run all tests
make test

# Run Python tests only
.venv313/bin/pytest tests/ -x -q

# Run type checks
make typecheck
```

- All new features must include tests
- Target 90%+ code coverage
- Tests run in CI on every push

## Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Make your changes** following the code standards
3. **Add tests** for new functionality
4. **Run verification**: `make verify`
5. **Write a clear PR description** explaining:
   - What changed and why
   - How to test the changes
   - Any breaking changes
6. **Submit the PR** and wait for review

### PR Title Format

```
type(scope): description

Examples:
feat(parser): add Rust language support
fix(graph): resolve circular dependency detection
docs(readme): update setup instructions
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Specify your environment (OS, Python version, Node version)

## Architecture Decisions

Major architectural changes should be discussed in a GitHub Issue before implementation. Reference existing decisions in `ARCHITECTURE.md`.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
