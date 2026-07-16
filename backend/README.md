# Backend

FastAPI application code for Forge AI.

## Local Commands

- Run tests: `make test`
- Run verification: `make verify`
- Start the API locally: `.venv/bin/uvicorn backend.app.main:app --reload`

## Environment

Configuration is loaded from environment variables prefixed with `FORGE_AI_`.

- `FORGE_AI_APP_NAME`
- `FORGE_AI_ENVIRONMENT`
- `FORGE_AI_LOG_LEVEL`
- `FORGE_AI_VERSION`

The health endpoint is available at `/api/health`.
