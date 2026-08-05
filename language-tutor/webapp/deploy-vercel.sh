#!/usr/bin/env bash
# Deploy language-tutor webapp to Vercel (run as Vercel project owner)
# Usage: ./deploy-vercel.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Deploy webapp to Vercel (production) ==="
echo "Project: webapp  →  https://webapp-bay-three-75.vercel.app"
echo ""

if ! command -v npx >/dev/null 2>&1; then
  echo "ERROR: Node.js/npx not found. Install from https://nodejs.org"
  exit 1
fi

echo "1) Login (browser will open — use the Vercel account that owns project 'webapp')..."
npx vercel login

echo ""
echo "2) Link to existing project 'webapp'..."
npx vercel link --yes --project webapp

echo ""
echo "3) Production deploy..."
npx vercel --prod --yes

echo ""
echo "=== Done ==="
echo "Check: https://webapp-bay-three-75.vercel.app/voice"
echo "Expected: HTTP 200 (voice teacher page), not 404"
