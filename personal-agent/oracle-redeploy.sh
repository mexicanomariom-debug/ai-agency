#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Personal Agent — Redeploy ==="

if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

$DOCKER compose -f docker-compose.prod.yml down 2>/dev/null || true
rm -rf __pycache__ .venv 2>/dev/null || true

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing"
  exit 1
fi

chmod +x oracle-setup.sh
./oracle-setup.sh
