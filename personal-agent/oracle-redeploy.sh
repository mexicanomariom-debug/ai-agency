#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Personal Agent — Redeploy ==="

if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

COMPOSE_FILE="docker-compose.prod.yml"

echo "--- Stopping old containers ---"
$DOCKER compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
$DOCKER rm -f personal-agent-bot personal-agent-oauth 2>/dev/null || true

rm -rf __pycache__ .venv 2>/dev/null || true

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing"
  exit 1
fi

chmod +x oracle-setup.sh
./oracle-setup.sh

echo "--- Verify containers ---"
$DOCKER compose -f "$COMPOSE_FILE" ps

BOT_STATUS=$($DOCKER inspect -f '{{.State.Status}}' personal-agent-bot 2>/dev/null || echo "missing")
OAUTH_STATUS=$($DOCKER inspect -f '{{.State.Status}}' personal-agent-oauth 2>/dev/null || echo "missing")

if [[ "$BOT_STATUS" != "running" ]]; then
  echo "ERROR: personal-agent-bot is not running (status=$BOT_STATUS)"
  $DOCKER compose -f "$COMPOSE_FILE" logs bot --tail 50 || true
  exit 1
fi

if [[ "$OAUTH_STATUS" != "running" ]]; then
  echo "ERROR: personal-agent-oauth is not running (status=$OAUTH_STATUS)"
  $DOCKER compose -f "$COMPOSE_FILE" logs oauth --tail 50 || true
  exit 1
fi

echo "=== Redeploy OK ==="
