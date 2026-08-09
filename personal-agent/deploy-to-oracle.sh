#!/usr/bin/env bash
# Deploy personal-agent to Oracle (runs alongside language-tutor at /opt/opus5)
set -euo pipefail

SERVER="${1:-ubuntu@140.84.183.154}"
REMOTE_DIR="/opt/personal-agent"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="/tmp/personal-agent-deploy-$$.tar.gz"
HOST_IP="${ORACLE_HOST_IP:-140.84.183.154}"

cleanup() { rm -f "$ARCHIVE"; }
trap cleanup EXIT

echo "-> Building archive..."
tar -czf "$ARCHIVE" \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='data' \
  --exclude='.env' \
  -C "$SCRIPT_DIR" .

echo "-> Uploading to $SERVER:$REMOTE_DIR ..."
ssh "$SERVER" "sudo mkdir -p $REMOTE_DIR && sudo chown -R \$(whoami):\$(whoami) $REMOTE_DIR"
scp "$ARCHIVE" "$SERVER:/tmp/personal-agent-deploy.tar.gz"

if [[ -f "$SCRIPT_DIR/.env.production" ]]; then
  scp "$SCRIPT_DIR/.env.production" "$SERVER:$REMOTE_DIR/.env"
elif [[ -f "$SCRIPT_DIR/.env" ]]; then
  scp "$SCRIPT_DIR/.env" "$SERVER:$REMOTE_DIR/.env"
else
  echo "WARNING: No .env found locally — server must already have $REMOTE_DIR/.env"
fi

echo "-> Extracting and redeploying..."
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
cd $REMOTE_DIR
tar -xzf /tmp/personal-agent-deploy.tar.gz
rm -f /tmp/personal-agent-deploy.tar.gz
chmod +x oracle-redeploy.sh oracle-setup.sh deploy-to-oracle.sh
./oracle-redeploy.sh
REMOTE

echo ""
echo "Deploy complete!"
echo "   Personal Agent bot running at $REMOTE_DIR"
echo "   OAuth (Calendar): http://${HOST_IP}:8081/oauth/google/callback"
echo "   Logs: ssh $SERVER 'cd $REMOTE_DIR && docker compose -f docker-compose.prod.yml logs -f bot'"
