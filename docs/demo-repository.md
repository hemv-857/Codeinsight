# Demo Repository

Use a real repository for the final demo. The recommended target is FastAPI:

```text
https://github.com/fastapi/fastapi
```

FastAPI matches the demo criteria because it has enough source files to show
system-level understanding, is Python-heavy for Tree-sitter parsing, and has
clear routing, documentation, and test structure for search, graph, debt, and
Q&A scenes.

## Preparation

Clone the repository before recording:

```bash
git clone https://github.com/fastapi/fastapi /tmp/codeinsight-demo-fastapi
```

Start CodeInsight:

```bash
.venv/bin/uvicorn backend.app.main:app --reload
npm run dev --workspace @codeinsight/frontend
```

In the dashboard, scan `/tmp/codeinsight-demo-fastapi`, then run:

- Repository explorer
- Dependency graph
- Knowledge graph
- Vector indexing
- Repository search
- Repository Q&A
- Technical debt
- Bug impact
- README, architecture docs, Mermaid diagrams, and onboarding generation

## Offline Alternative

If network access is unavailable during rehearsal, use any already-cloned
100-1000 source-file repository on the machine and scan its local path. Do not
use synthetic files or hardcoded responses for the recording.

## Recording Prompts

- "Explain how authentication works."
- "What happens if I modify auth.py?"
- Search for `APIRoute` or another symbol that exists in the prepared repository.
- Paste a real stack trace from the selected repository or from a small local
  reproduction using repository file paths.
