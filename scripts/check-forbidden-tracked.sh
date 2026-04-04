#!/usr/bin/env bash
# Fail if paths that must never be tracked are present in the git index.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

fail() {
  echo "::error::$1"
  exit 1
}

if [[ -n "$(git ls-files -- .claude/settings.local.json 2>/dev/null || true)" ]]; then
  fail ".claude/settings.local.json must not be tracked (use git rm --cached)"
fi

if [[ -n "$(git ls-files -- .claude/worktrees/ 2>/dev/null || true)" ]]; then
  fail ".claude/worktrees/ must not be tracked"
fi

exit 0
