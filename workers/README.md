# Workers

Background indexing and analysis workers live here.

Milestone 4 provides a real worker health process so Docker can supervise the worker service before indexing jobs are introduced.

- Local health server: `.venv/bin/python -m workers.main`
- Health endpoint: `http://localhost:8001/health`
