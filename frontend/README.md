# Frontend

Next.js application code for Forge AI.

## Local Commands

- Start the dashboard: `npm run dev --workspace @forge-ai/frontend`
- Build the dashboard: `npm run build --workspace @forge-ai/frontend`
- Type check: `npm run typecheck --workspace @forge-ai/frontend`

## Environment

- `NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000`.

The first screen is the dark-mode Forge AI dashboard with backend health, a repository explorer, workflow status, and a dependency graph panel.

The repository explorer can scan a backend-accessible local repository path or load a previously imported repository by import ID.

The dependency graph panel can build file-level import graphs from a repository path or import ID and render internal dependencies, unresolved imports, and detected cycles.
