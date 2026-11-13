#!/usr/bin/env bash
# Durable (re)launcher for the AI ASTRA AGENCY intro site  (D-W1).
#
# Idempotent and safe to re-run: it stops any prior instance bound to PORT,
# rebuilds a CLEAN doc root that contains ONLY the built site (never the
# project tree — see D-W3), then starts a detached server and waits until it
# answers HTTP 200. Exits non-zero if the site did not come up.
#
#   ./serve.sh                 # port 12000, doc root /tmp/astra_site
#   ASTRA_SITE_PORT=8080 ./serve.sh
#
# Env overrides: ASTRA_SITE_PORT, ASTRA_SITE_ROOT, ASTRA_SITE_LOG.
set -u

PORT="${ASTRA_SITE_PORT:-12000}"
SITE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOC_ROOT="${ASTRA_SITE_ROOT:-/tmp/astra_site}"
LOG="${ASTRA_SITE_LOG:-/tmp/astra_site.log}"
HEALTH="http://127.0.0.1:${PORT}/"
PATTERN="http\\.server ${PORT}( |$)"

log() { printf '[serve] %s\n' "$*"; }

# 1. Stop any prior instance bound to PORT. Targeted by port (not a blanket
#    pkill), so unrelated servers are never touched.
stop_prior() {
  local pids
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  [ -z "$pids" ] && return 0
  log "stopping prior instance(s) on :${PORT}: $(echo "$pids" | tr '\n' ' ')"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 0.5
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
  fi
}

# 2. Build a clean doc root: ONLY the shipped site. Dev/verify artefacts
#    (VERIFY.md, verify_site.py, this script) must never be web-reachable.
build_doc_root() {
  rm -rf "$DOC_ROOT"
  mkdir -p "$DOC_ROOT"
  cp -a "$SITE_SRC/index.html" "$SITE_SRC/styles.css" "$SITE_SRC/main.js" "$DOC_ROOT"/
  cp -a "$SITE_SRC/assets" "$DOC_ROOT"/
  # Belt-and-braces: drop any stray dev file that might have been copied.
  rm -f "$DOC_ROOT"/VERIFY.md "$DOC_ROOT"/verify_site.py \
        "$DOC_ROOT"/serve.sh "$DOC_ROOT"/healthcheck.sh
}

# 3. Start a detached server.
start() {
  cd "$DOC_ROOT" || exit 1
  nohup python3 -m http.server "$PORT" --directory "$DOC_ROOT" \
        >"$LOG" 2>&1 &
  log "started detached server (pid $!) -> $DOC_ROOT (log: $LOG)"
}

# 4. Wait until it answers 200.
wait_ready() {
  local i code="000"
  for i in $(seq 1 40); do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$HEALTH" 2>/dev/null || true)"
    [ "$code" = "200" ] && break
    sleep 0.25
  done
  printf '%s' "$code"
}

stop_prior
build_doc_root
start
code="$(wait_ready)"
log "healthcheck GET ${HEALTH} -> HTTP ${code}"
if [ "$code" = "200" ]; then
  log "OK — site is up on :${PORT}"
  exit 0
fi
log "ERROR — site did not return 200 (last code ${code}); see ${LOG}"
exit 1
