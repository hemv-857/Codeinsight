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
- `FORGE_AI_METADATA_DATABASE_PATH`
- `FORGE_AI_REPOSITORY_CLONE_TIMEOUT_SECONDS`
- `FORGE_AI_REPOSITORY_STORAGE_PATH`
- `FORGE_AI_REPOSITORY_ZIP_MAX_BYTES`
- `FORGE_AI_VERSION`

The health endpoint is available at `/api/health`.

Repository import endpoints:

- `POST /api/repositories/import`
- `POST /api/repositories/import/zip`
- `GET /api/repositories/imports/{import_id}`
- `POST /api/repositories/scan`
- `GET /api/repositories/imports/{import_id}/scan`
- `POST /api/repositories/metadata`
- `GET /api/repositories/metadata/{repository_id}`
- `GET /api/repositories/imports/{import_id}/metadata`
