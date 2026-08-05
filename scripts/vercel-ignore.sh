#!/usr/bin/env bash
# Vercel ignoreCommand: exit 0 = skip build, exit 1 = build.
set -euo pipefail

branch="${VERCEL_GIT_COMMIT_REF:-}"

# Marketing site (ai-agency) deploys from main only — skip preview branches.
if [ "$branch" != "main" ]; then
  echo "Skip: branch is $branch (main only)"
  exit 0
fi

# First commit or shallow clone — build to be safe.
if ! git rev-parse HEAD^ >/dev/null 2>&1; then
  echo "Build: no parent commit"
  exit 1
fi

# Skip when only language-tutor/ changed (separate Vercel project: webapp-bay).
if git diff HEAD^ HEAD --quiet -- . ':!language-tutor'; then
  echo "Skip: only language-tutor/ changed"
  exit 0
fi

echo "Build: marketing site files changed on main"
exit 1
