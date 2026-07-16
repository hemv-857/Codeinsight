# Docker

Dockerfiles and deployment support for the Forge AI development stack.

## Services

- `frontend`: Next.js dashboard on port `3000`
- `backend`: FastAPI API on port `8000`
- `worker`: background worker health service on port `8001`
- `neo4j`: graph database on ports `7474` and `7687`
- `redis`: cache and job coordination on port `6379`

The backend connects to Neo4j through `FORGE_AI_NEO4J_URI`, which defaults to the
Compose service URL inside the stack.

## Commands

- Validate Compose: `make docker-validate`
- Build app images: `make docker-build`
- Start the stack: `docker-compose up --build`
