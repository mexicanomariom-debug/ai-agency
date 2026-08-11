#!/usr/bin/env bash
# Remote redeploy helper — copied to Oracle by deploy-ai-ege-tutor-oracle.ps1
set -euo pipefail

REMOTE_DIR="${1:-/opt/opus5}"
ARCHIVE="/tmp/ai-ege-tutor-deploy.tar.gz"

echo "=== Redeploy in $REMOTE_DIR ==="
sudo mkdir -p "$REMOTE_DIR"
sudo chown -R "$(whoami):$(whoami)" "$REMOTE_DIR"
cd "$REMOTE_DIR"

if [ ! -f "$ARCHIVE" ]; then
  echo "ERROR: missing $ARCHIVE on server"
  exit 1
fi

tar -xzf "$ARCHIVE"
rm -f "$ARCHIVE"

if [ -f oracle-redeploy.sh ]; then
  chmod +x oracle-redeploy.sh oracle-setup.sh 2>/dev/null || true
  ./oracle-redeploy.sh
elif [ -f docker-compose.prod.yml ]; then
  if docker info &>/dev/null 2>&1; then
    docker compose -f docker-compose.prod.yml up -d --build
  else
    sudo docker compose -f docker-compose.prod.yml up -d --build
  fi
elif [ -f docker-compose.yml ]; then
  if docker info &>/dev/null 2>&1; then
    docker compose up -d --build
  else
    sudo docker compose up -d --build
  fi
elif [ -f requirements.txt ] && [ -f bot/main.py ]; then
  echo "Python bot detected — install deps and restart (no docker-compose)"
  python3 -m pip install -r requirements.txt -q
  pkill -f "python.*bot" 2>/dev/null || true
  nohup python3 -m bot.main > bot.log 2>&1 &
  sleep 3
  tail -20 bot.log || true
else
  echo "ERROR: no docker-compose.yml / oracle-redeploy.sh in project"
  ls -la
  exit 1
fi

echo "=== Done ==="
