#!/usr/bin/env bash
# Safe push helper for AI ASTRA AGENCY.
#
# Resolves the write-capable GitHub token from the secret store and passes it to
# git through an EPHEMERAL credential helper, so the token is never written to
# .git/config, never appears in `git remote -v`, and never lands in the repo.
#
# Usage:  ops/gitpush.sh <remote> <branch>
set -euo pipefail

REMOTE="${1:-company}"
BRANCH="${2:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Push from the current repo if we are inside one; otherwise from the project.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  REPO_DIR="$(git rev-parse --show-toplevel)"
else
  REPO_DIR="$SCRIPT_DIR"
fi

TOKEN="$(cd "$SCRIPT_DIR" && python3 -c "
import sys; sys.path.insert(0,'ops')
import secrets
print(secrets.resolve('GITHUB_TOKEN_WRITE') or '')
")"

if [ -z "$TOKEN" ]; then
  echo "ERROR: GITHUB_TOKEN_WRITE is not available (env or secret store)." >&2
  exit 1
fi

cd "$REPO_DIR"
git -c credential.helper= \
    -c "credential.helper=!f() { echo username=x-access-token; echo password=$TOKEN; }; f" \
    push "$REMOTE" "$BRANCH"
