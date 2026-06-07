#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Run all tests with coverage report
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Running tests with coverage ==="
../.venv/bin/pytest \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=85 \
    -v \
    "$@"

echo ""
echo "=========================================="
echo "Coverage report: backend/htmlcov/index.html"
echo "=========================================="
