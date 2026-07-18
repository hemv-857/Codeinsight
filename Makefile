PYTHON := .venv313/bin/python
BLACK := .venv313/bin/black
RUFF := .venv313/bin/ruff
MYPY := .venv313/bin/mypy

.PHONY: build docker-build docker-validate format format-check frontend-build install-python-tools lint test typecheck verify

build: typecheck frontend-build docker-validate

docker-validate:
	docker-compose config

docker-build:
	docker-compose build backend frontend worker

frontend-build:
	npm run build --workspace @codeinsight/frontend

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
	$(PYTHON) scripts/check_python_coverage.py --min 90

typecheck:
	npm run typecheck
	$(MYPY) backend workers graph parser tests

verify: format-check lint typecheck test build
