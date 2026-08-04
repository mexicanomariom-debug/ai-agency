#!/usr/bin/env bash
# Run FROM YOUR LOCAL MACHINE (where you have SSH access to Oracle)
set -euo pipefail

SERVER="${1:-ubuntu@140.84.183.154}"
REMOTE_DIR="/opt/opus5"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "→ Deploying to $SERVER:$REMOTE_DIR"

# Sync project (exclude node_modules, .next, .env)
rsync -avz --delete \
  --exclude node_modules \
  --exclude .next \
  --exclude .env \
  --exclude __pycache__ \
  --exclude .venv \
  "$SCRIPT_DIR/" "$SERVER:$REMOTE_DIR/"

# Copy production env if exists locally
if [[ -f "$SCRIPT_DIR/.env.production" ]]; then
  scp "$SCRIPT_DIR/.env.production" "$SERVER:$REMOTE_DIR/.env"
elif [[ -f "$SCRIPT_DIR/.env" ]]; then
  scp "$SCRIPT_DIR/.env" "$SERVER:$REMOTE_DIR/.env"
else
  echo "⚠️  No .env or .env.production found — create on server manually"
fi

echo "→ Running setup on server..."
ssh "$SERVER" "chmod +x $REMOTE_DIR/oracle-setup.sh && cd $REMOTE_DIR && ./oracle-setup.sh"

echo ""
echo "✅ Deploy complete!"
echo "   Web App: https://webapp-bay-three-75.vercel.app/app"
echo "   Bot:     https://t.me/All_languages_bot"
