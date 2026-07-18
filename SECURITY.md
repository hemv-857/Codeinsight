# Security Policy

## Overview

CodeInsight processes untrusted code repositories. This document describes the security measures in place and how to report vulnerabilities.

## Sandboxing

- **No code execution** — CodeInsight never executes repository code. All analysis is static (parsing, pattern matching, graph traversal).
- **Safe parsing** — The default parser uses regex-based extraction, not Tree-sitter execution. Tree-sitter (when enabled) only builds syntax trees, never evaluates code.
- **Path validation** — All file paths are validated and normalized to prevent directory traversal attacks.
- **Upload limits** — ZIP uploads are capped at 100MB. Git clones use shallow depth (`--depth 1`) with timeout enforcement.

## Data Handling

### What is stored locally

- Repository files are cloned to `data/repositories/` (gitignored)
- SQLite databases for metadata, vectors, graphs, and conversations in `data/`
- All data stays on your machine

### What is sent externally

- **OpenAI API** (optional): Code chunks are sent for embedding generation and Q&A responses when `CODEINSIGHT_OPENAI_API_KEY` is configured
- **Ollama** (optional): If using local embeddings, nothing is sent externally
- **GitHub API** (optional): Repository cloning uses public HTTPS URLs by default. Private repos require `CODEINSIGHT_GITHUB_TOKEN`

### What is never sent

- Full repository contents are never transmitted in bulk
- No secrets, API keys, or credentials are sent to external services
- No user data is collected or analytics tracked

## API Key Security

- API keys are stored in environment variables, never in code
- `.env` files are gitignored
- Keys are loaded via `pydantic-settings` as `SecretStr` types (masked in logs)
- The `.env.example` file contains empty placeholders only

## Known Limitations

- Neo4j default credentials (`neo4j/codeinsight-dev`) in `docker-compose.yml` are for development only. Change them for production deployments.
- The tool processes arbitrary repository content. While no code is executed, malformed input could cause parser errors (caught and handled gracefully).

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Security Checklist for Deployment

- [ ] Change Neo4j default credentials
- [ ] Set `CODEINSIGHT_CORS_ORIGINS` to your domain
- [ ] Use HTTPS in production
- [ ] Restrict network access to Neo4j port (7687)
- [ ] Set appropriate file permissions on `data/` directory
- [ ] Rotate API keys periodically
