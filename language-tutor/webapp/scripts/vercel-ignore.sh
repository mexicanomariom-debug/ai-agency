#!/usr/bin/env bash
# Vercel ignoreCommand for language-tutor webapp (webapp-bay project).
# exit 0 = skip, exit 1 = build.
set -euo pipefail

branch="${VERCEL_GIT_COMMIT_REF:-}"

if [ "$branch" != "main" ]; then
  echo "Skip: branch is $branch (main only)"
  exit 0
fi

if ! git rev-parse HEAD^ >/dev/null 2>&1; then
  echo "Build: no parent commit"
  exit 1
fi

# Paths are relative to repo root (Vercel clones full repo).
if git diff HEAD^ HEAD --quiet -- language-tutor/webapp; then
  echo "Skip: no webapp changes"
  exit 0
fi

echo "Build: language-tutor/webapp changed on main"
exit 1
