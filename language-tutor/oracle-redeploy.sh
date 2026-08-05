#!/usr/bin/env bash
# Clean redeploy on Oracle server — run via deploy script or manually over SSH
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Opus 5 — Clean Redeploy ==="

if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

if command -v docker &>/dev/null; then
  echo "Stopping old containers..."
  $DOCKER compose -f docker-compose.prod.yml down -v 2>/dev/null || true
fi

echo "Removing old build artifacts..."
rm -rf webapp/node_modules webapp/.next backend/__pycache__ backend/.venv 2>/dev/null || true

if [[ ! -f .env ]]; then
  if [[ -f .env.production ]]; then
    cp .env.production .env
  else
    echo "ERROR: .env missing — set BOT_TOKEN and OPENAI_API_KEY"
    exit 1
  fi
fi

chmod +x oracle-setup.sh
./oracle-setup.sh
