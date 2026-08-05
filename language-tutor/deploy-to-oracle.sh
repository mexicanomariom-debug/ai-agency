#!/usr/bin/env bash
# Fast deploy to Oracle via tar archive (excludes node_modules, .next, etc.)
set -euo pipefail

SERVER="${1:-ubuntu@140.84.183.154}"
REMOTE_DIR="/opt/opus5"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="/tmp/opus5-deploy-$$.tar.gz"

cleanup() { rm -f "$ARCHIVE"; }
trap cleanup EXIT

echo "-> Building archive (no node_modules)..."
tar -czf "$ARCHIVE" \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='.git' \
  -C "$SCRIPT_DIR" .

echo "-> Uploading to $SERVER..."
ssh "$SERVER" "sudo mkdir -p $REMOTE_DIR && sudo chown -R \$(whoami):\$(whoami) $REMOTE_DIR"
scp "$ARCHIVE" "$SERVER:/tmp/opus5-deploy.tar.gz"

# Copy .env separately (may be gitignored locally)
if [[ -f "$SCRIPT_DIR/.env.production" ]]; then
  scp "$SCRIPT_DIR/.env.production" "$SERVER:$REMOTE_DIR/.env"
elif [[ -f "$SCRIPT_DIR/.env" ]]; then
  scp "$SCRIPT_DIR/.env" "$SERVER:$REMOTE_DIR/.env"
fi

echo "-> Extracting and redeploying..."
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
cd $REMOTE_DIR
tar -xzf /tmp/opus5-deploy.tar.gz
rm -f /tmp/opus5-deploy.tar.gz
chmod +x oracle-redeploy.sh oracle-setup.sh
./oracle-redeploy.sh
REMOTE

echo ""
echo "Deploy complete!"
echo "   API:     http://140.84.183.154:8000/health"
echo "   Web App: https://webapp-bay-three-75.vercel.app/app"
echo "   Bot:     https://t.me/All_languages_bot"
