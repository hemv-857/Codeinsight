PYTHON := .venv/bin/python
BLACK := .venv/bin/black
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy

.PHONY: build docker-validate format format-check frontend-build install-python-tools lint test typecheck verify

build: typecheck frontend-build docker-validate

docker-validate:
	docker-compose config

frontend-build:
	npm run build --workspace @forge-ai/frontend

format:
	npm run format
	$(BLACK) .
	$(RUFF) format .

format-check:
	npm run format:check
	$(BLACK) --check .
	$(RUFF) format --check .

install-python-tools:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	npm run lint
	$(RUFF) check .

test:
	$(PYTHON) -m pytest

typecheck:
	npm run typecheck
	$(MYPY) backend workers graph parser tests

verify: format-check lint typecheck test build
