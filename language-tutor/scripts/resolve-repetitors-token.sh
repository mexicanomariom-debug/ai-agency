#!/usr/bin/env bash
# Pick Telegram token for @repetitors_ai_bot from env vars or .env files.
set -euo pipefail

pick_token() {
  local t="${1:-}"
  [ -z "$t" ] && return 1
  local me
  me=$(curl -sS --max-time 15 "https://api.telegram.org/bot${t}/getMe" || true)
  if echo "$me" | grep -q 'repetitors_ai_bot'; then
    printf '%s' "$t"
    return 0
  fi
  return 1
}

try_file() {
  local f="$1"
  [ -f "$f" ] || return 1
  local t
  t=$(grep -m1 '^BOT_TOKEN=' "$f" | cut -d= -f2- || true)
  pick_token "$t"
}

# 1) Explicit env (CI secrets)
if [ -n "${REPETITORS_BOT_TOKEN:-}" ]; then
  if pick_token "$REPETITORS_BOT_TOKEN"; then exit 0; fi
fi
if [ -n "${BOT_TOKEN:-}" ]; then
  if pick_token "$BOT_TOKEN"; then exit 0; fi
fi

# 2) Local / server Projects layout
candidates=(
  "/opt/opus5/.env"
  "/opt/opus5/.env.production"
  "/opt/opus5/.env.local"
  "/opt/opus5/.env.bak"
  "/home/ubuntu/Projects/opus5/.env"
  "/home/ubuntu/Projects/language-tutor/.env"
  "/home/ubuntu/Projects/ai-agency/language-tutor/.env"
  "/home/ubuntu/ai-agency/language-tutor/.env"
  "/home/ubuntu/opus5/.env"
  "$HOME/Projects/opus5/.env"
  "$HOME/Projects/language-tutor/.env"
  "$HOME/Projects/ai-agency/language-tutor/.env"
)

if [ -d /home/ubuntu ]; then
  while IFS= read -r f; do
    candidates+=("$f")
  done < <(find /home/ubuntu -maxdepth 5 -name '.env' 2>/dev/null)
fi

for f in "${candidates[@]}"; do
  if try_file "$f"; then exit 0; fi
done

if [ -d /home/ubuntu/Projects ]; then
  while IFS= read -r f; do
    if try_file "$f"; then exit 0; fi
  done < <(find /home/ubuntu/Projects -maxdepth 5 -name '.env' 2>/dev/null)
fi

if [ -d /home/ubuntu ]; then
  while IFS= read -r f; do
    if try_file "$f"; then exit 0; fi
  done < <(find /home/ubuntu -maxdepth 5 -name '.env' 2>/dev/null)
fi

echo "ERROR: no @repetitors_ai_bot token in REPETITORS_BOT_TOKEN, BOT_TOKEN, or Projects/.env files" >&2
exit 1
