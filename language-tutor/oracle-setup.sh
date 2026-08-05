#!/usr/bin/env bash
# Run ON Oracle server as ubuntu/opc after copying project to /opt/opus5
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Opus 5 — Oracle Server Setup ==="

if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  DOCKER="sudo docker"
fi

if ! $DOCKER compose version &>/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y docker-compose-plugin 2>/dev/null || true
fi

if [[ ! -f .env ]]; then
  if [[ -f .env.production ]]; then
    cp .env.production .env
  else
    cp .env.example .env
    echo "ERROR: Edit /opt/opus5/.env — set BOT_TOKEN and OPENAI_API_KEY"
    exit 1
  fi
fi

if command -v ufw &>/dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
  sudo ufw allow 8000/tcp || true
  sudo ufw allow 22/tcp || true
fi

echo "Starting database..."
$DOCKER compose -f docker-compose.prod.yml up -d db

echo "Waiting for database..."
for i in $(seq 1 30); do
  if $DOCKER compose -f docker-compose.prod.yml exec -T db pg_isready -U "${POSTGRES_USER:-language_tutor}" &>/dev/null; then
    break
  fi
  sleep 2
done

echo "Running migrations..."
$DOCKER compose -f docker-compose.prod.yml run --rm --no-deps api alembic upgrade head

echo "Building and starting all containers..."
$DOCKER compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services..."
sleep 10

echo ""
echo "=== Status ==="
$DOCKER compose -f docker-compose.prod.yml ps

echo ""
echo "=== Health check ==="
curl -sf http://localhost:8000/health && echo " API OK" || echo " API not responding yet"

echo ""
echo "=== Done ==="
echo "Logs: $DOCKER compose -f docker-compose.prod.yml logs -f bot"
