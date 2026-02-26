#!/usr/bin/env bash
# Smoke test for the Prometheus observability island.
# Run from the repo root:
#   bash scripts/test_prometheus.sh
set -euo pipefail

echo "=== Prometheus smoke test ==="

# Install test dependencies (pytest only).
python -m pip install --quiet --upgrade pip
python -m pip install --quiet pytest

# Run the Prometheus test suite.
python -m pytest prometheus/tests/ -q "$@"

echo "=== Prometheus smoke test passed ==="
