#!/usr/bin/env bash
set -euo pipefail

# CI test runner — starts dependent services, runs tests, cleans up
cd "$(dirname "$0")/.."

echo "=== Starting test dependencies ==="
docker compose up -d postgres redis rabbitmq minio
docker compose run --rm migrate

echo "=== Installing dev dependencies ==="
pip install -e ".[dev]"

echo "=== Running tests ==="
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo "=== Cleaning up ==="
docker compose down
