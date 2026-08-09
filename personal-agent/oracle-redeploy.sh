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
PROJECT="personal-agent"

compose() {
  $DOCKER compose -p "$PROJECT" -f "$COMPOSE_FILE" "$@"
}

echo "--- Stopping conflicting bots on this host (same BOT_TOKEN) ---"
if [[ -d /opt/opus5 ]]; then
  echo "Stopping language-tutor at /opt/opus5..."
  (cd /opt/opus5 && $DOCKER compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null) || true
fi
for name in opus5-bot opus5-api language-tutor-bot; do
  $DOCKER rm -f "$name" 2>/dev/null || true
done
pkill -f "[p]ython -m bot.main" 2>/dev/null || true

echo "--- Stopping old personal-agent containers ---"
compose down --remove-orphans 2>/dev/null || true
$DOCKER rm -f personal-agent-bot personal-agent-oauth 2>/dev/null || true
$DOCKER network rm "${PROJECT}_default" 2>/dev/null || true

rm -rf __pycache__ .venv 2>/dev/null || true

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing"
  exit 1
fi

chmod +x oracle-setup.sh
./oracle-setup.sh

echo "--- Verify containers ---"
compose ps

BOT_STATUS=$($DOCKER inspect -f '{{.State.Status}}' personal-agent-bot 2>/dev/null || echo "missing")
OAUTH_STATUS=$($DOCKER inspect -f '{{.State.Status}}' personal-agent-oauth 2>/dev/null || echo "missing")

if [[ "$BOT_STATUS" != "running" ]]; then
  echo "ERROR: personal-agent-bot is not running (status=$BOT_STATUS)"
  compose logs bot --tail 50 || true
  exit 1
fi

if [[ "$OAUTH_STATUS" != "running" ]]; then
  echo "ERROR: personal-agent-oauth is not running (status=$OAUTH_STATUS)"
  compose logs oauth --tail 50 || true
  exit 1
fi

echo "=== Redeploy OK ==="
