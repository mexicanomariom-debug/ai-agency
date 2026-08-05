#!/usr/bin/env bash
# Run ON Oracle server as ubuntu/opc after copying project to /opt/opus5
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Opus 5 — Oracle Server Setup ==="

# Use sudo for docker if user is not in docker group (common on fresh Oracle VMs)
if docker info &>/dev/null 2>&1; then
  DOCKER="docker"
else
  DOCKER="sudo docker"
fi

# Install Docker if missing
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

# Create .env if missing
if [[ ! -f .env ]]; then
  if [[ -f .env.production ]]; then
    cp .env.production .env
  else
    cp .env.example .env
    echo "ERROR: Edit /opt/opus5/.env — set BOT_TOKEN and OPENAI_API_KEY"
    exit 1
  fi
fi

# Open port 8000 in local firewall (if ufw active)
if command -v ufw &>/dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
  sudo ufw allow 8000/tcp || true
  sudo ufw allow 22/tcp || true
fi

echo "Building and starting containers..."
$DOCKER compose -f docker-compose.prod.yml down 2>/dev/null || true
$DOCKER compose -f docker-compose.prod.yml up -d --build

echo "Waiting for database..."
sleep 15

echo "Running migrations..."
$DOCKER compose -f docker-compose.prod.yml exec -T api alembic upgrade head

echo ""
echo "=== Status ==="
$DOCKER compose -f docker-compose.prod.yml ps

echo ""
echo "=== Health check ==="
curl -sf http://localhost:8000/health && echo " API OK" || echo " API not responding"

echo ""
echo "=== Done ==="
echo "API:  http://$(curl -sf ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8000"
echo "Logs: $DOCKER compose -f docker-compose.prod.yml logs -f bot"
