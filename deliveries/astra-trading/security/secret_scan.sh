#!/usr/bin/env bash
# Astra Trading — secret hygiene scan.
#
# Scans the WORKING TREE and the GIT HISTORY for anything that looks like a real
# credential: Supabase keys, provider API keys, JWTs, private-key blocks, and
# wallet seed phrases. Prints every hit as file:line with the matched token
# MASKED (first/last chars only) so the scan output never becomes a new leak.
# Exits non-zero if any HIGH-confidence hit is found.
#
# Usage:
#   bash secret_scan.sh            # scan tree + history
#   bash secret_scan.sh --tree     # working tree only
#   bash secret_scan.sh --history  # git history only
set -uo pipefail

MODE="${1:---all}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
SELF="$HERE/secret_scan.sh"

HIGH_HITS=0

# name|extended-regex   (high-confidence = real-looking key material)
PATTERNS=(
  'supabase_mgmt|sbp_[A-Za-z0-9]{30,}'
  'supabase_secret|sb_secret_[A-Za-z0-9_-]{20,}'
  'supabase_publishable|sb_publishable_[A-Za-z0-9_-]{20,}'
  'openai_key|sk-(proj-|svcacct-)?[A-Za-z0-9_-]{20,}'
  'replicate|r8_[A-Za-z0-9]{30,}'
  'relay_token|rlwy_[A-Za-z0-9]{20,}'
  'google_api|AIza[0-9A-Za-z_-]{35}'
  'github_token|gh[pousr]_[A-Za-z0-9]{36,}'
  'aws_access_key|AKIA[0-9A-Z]{16}'
  'slack_token|xox[baprs]-[A-Za-z0-9-]{10,}'
  'stripe_live|(sk|rk)_live_[A-Za-z0-9]{20,}'
  'telegram_bot|[0-9]{8,10}:[A-Za-z0-9_-]{34,}'
  'jwt|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
  'private_key_block|-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'ssh_privkey|-----BEGIN OPENSSH PRIVATE KEY-----'
  'pgp_privkey|-----BEGIN PGP PRIVATE KEY BLOCK-----'
)

MENTION_PATTERN='(seed phrase|mnemonic|private key|secret key|api[_ -]?key|passphrase)'
EXCLUDES=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__
          --exclude-dir=.venv --exclude-dir=venv --exclude-dir=dist --exclude-dir=build
          --exclude-dir=.tmp_repos)

# mask a token: first 6 + "…" + last 4 + (length)
mask() { awk -v m="$1" 'BEGIN{l=length(m); if(l<=12){print "<"l" chars>"} else {print substr(m,1,6)"..."substr(m,l-3)" ("l" chars)"}}'; }

emit() {  # emit <name> <grep -H -o lines>
  local name="$1" hits="$2"
  echo "  [HIGH] $name"
  local line path rest ln tok
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    path="${line%%:*}"; rest="${line#*:}"; ln="${rest%%:*}"; tok="${rest#*:}"
    echo "    $path:$ln  $(mask "$tok")"
    HIGH_HITS=$((HIGH_HITS + 1))
  done <<< "$hits"
}

scan_tree() {
  echo "== working tree =="
  for entry in "${PATTERNS[@]}"; do
    name="${entry%%|*}"; re="${entry#*|}"
    hits=$(grep -rInHoE "$re" "${EXCLUDES[@]}" "$REPO_ROOT" 2>/dev/null | grep -vF "$SELF")
    [ -z "$hits" ] && continue
    emit "$name" "$hits"
  done
  echo "  -- markdown / config files (md,json,yaml,yml,toml,cfg,ini,env,sh) --"
  local found=0 line path rest ln tok
  for entry in "${PATTERNS[@]}"; do
    re="${entry#*|}"
    hits=$(grep -rInHoE "$re" "${EXCLUDES[@]}" \
             --include='*.md' --include='*.json' --include='*.yaml' --include='*.yml' \
             --include='*.toml' --include='*.cfg' --include='*.ini' --include='*.env*' \
             --include='*.sh' "$REPO_ROOT" 2>/dev/null | grep -vF "$SELF")
    [ -z "$hits" ] && continue
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      path="${line%%:*}"; rest="${line#*:}"; ln="${rest%%:*}"; tok="${rest#*:}"
      echo "    [HIGH] $path:$ln  $(mask "$tok")"
      found=1; HIGH_HITS=$((HIGH_HITS + 1))
    done <<< "$hits"
  done
  [ "$found" -eq 0 ] && echo "    none"
  echo "  -- informational: prose mentions (not key material) --"
  grep -rInE "$MENTION_PATTERN" "${EXCLUDES[@]}" "$REPO_ROOT" 2>/dev/null \
    | grep -vF "$SELF" | grep -viE '(hashing|hashed|\bhash\b|/password|passwords|passwordless|passphrase are never)' \
    | head -20 | cut -c1-160 | sed 's/^/    /'
}

scan_history() {
  echo "== git history (added lines across all refs) =="
  for entry in "${PATTERNS[@]}"; do
    name="${entry%%|*}"; re="${entry#*|}"
    n=$(git -C "$REPO_ROOT" log -p --all --no-color 2>/dev/null | grep -cE "^\+.*($re)")
    if [ "${n:-0}" -gt 0 ]; then
      echo "  [HIGH] $name: $n added line(s) in history"
      git -C "$REPO_ROOT" log -p --all --no-color 2>/dev/null \
        | grep -E "^\+.*($re)" | head -5 | grep -oE "$re" | while IFS= read -r tok; do
            echo "      $(mask "$tok")"
          done
      HIGH_HITS=$((HIGH_HITS + n))
    fi
  done
  echo "  -- committed files with secret-like names --"
  local names
  names=$(git -C "$REPO_ROOT" log --all --pretty=format: --name-only 2>/dev/null \
          | sort -u | grep -iE '(\.env$|\.env\.|secret|credential|\.pem$|\.key$|id_rsa|\.p12$|\.pfx$|keystore)' \
          | grep -vE '^$')
  if [ -n "$names" ]; then echo "$names" | sed 's/^/    /'; else echo "    none"; fi
  echo "  -- .gitignore coverage --"
  git -C "$REPO_ROOT" show HEAD:.gitignore 2>/dev/null | sed 's/^/    /'
}

echo "repo: $REPO_ROOT"
case "$MODE" in
  --tree)    scan_tree ;;
  --history) scan_history ;;
  *)         scan_tree; echo; scan_history ;;
esac

echo
echo "TOTAL high-confidence hits: $HIGH_HITS"
if [ "$HIGH_HITS" -gt 0 ]; then
  echo "RESULT: FAIL — review every hit above before committing."
  exit 1
fi
echo "RESULT: PASS — no real-looking credential found."
exit 0
