#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example — fill in secrets before production use."
  cp .env.example .env
fi

echo "Building and starting production stack..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head

echo "Deployment complete."
echo "  API: http://localhost:8000"
echo "  Health: http://localhost:8000/health"
