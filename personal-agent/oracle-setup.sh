#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Personal Agent — Oracle Setup ==="

if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

PROJECT="personal-agent"

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
  echo "ERROR: .env missing — set BOT_TOKEN and OPENAI_API_KEY"
  exit 1
fi

# OAuth callback for Google Calendar (optional)
if command -v ufw &>/dev/null; then
  sudo ufw allow "${OAUTH_HOST_PORT:-8081}"/tcp || true
fi
sudo iptables -C INPUT -p tcp --dport "${OAUTH_HOST_PORT:-8081}" -j ACCEPT 2>/dev/null || \
  sudo iptables -I INPUT -p tcp --dport "${OAUTH_HOST_PORT:-8081}" -j ACCEPT || true

echo "Building and starting personal-agent bot..."
$DOCKER compose -p "$PROJECT" -f docker-compose.prod.yml up -d --build --force-recreate --remove-orphans

sleep 5
echo ""
echo "=== Status ==="
$DOCKER compose -p "$PROJECT" -f docker-compose.prod.yml ps

echo ""
echo "=== Bot logs ==="
$DOCKER compose -p "$PROJECT" -f docker-compose.prod.yml logs bot --tail 20

echo ""
echo "=== Done ==="
echo "Logs: $DOCKER compose -p $PROJECT -f docker-compose.prod.yml logs -f bot"
