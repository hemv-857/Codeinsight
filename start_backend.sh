#!/usr/bin/env bash
# Workaround for Python 3.13.5 binary_op segfault on macOS ARM
export PYTHON_DISABLE_SPECIALIZATION=1
export PYTHON_JIT=0

exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8002 --reload
