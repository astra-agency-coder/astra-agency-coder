#!/usr/bin/env bash
# Durable (re)launcher for the AI ASTRA AGENCY company site (deliveries/astra-site).
#
# Idempotent and safe to re-run: it stops any prior instance bound to PORT
# (matched by port, never a blanket pkill), starts a detached server, and waits
# until it answers HTTP 200. Exits non-zero if the site did not come up.
#
#   ./serve.sh                    # port 12000, log /tmp/astra_site_new.log
#   ASTRA_SITE_PORT=8080 ./serve.sh
#
# Env overrides: ASTRA_SITE_PORT, ASTRA_SITE_LOG.
set -u

PORT="${ASTRA_SITE_PORT:-12000}"
SITE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${ASTRA_SITE_LOG:-/tmp/astra_site_new.log}"
HEALTH="http://127.0.0.1:${PORT}/"
# Anchored so we only ever match the exact `python3 server.py` invocation —
# never an unrelated process that merely mentions "server.py" in its args.
PATTERN='^python3 server\.py$'

log() { printf '[serve] %s\n' "$*"; }

# 1. Stop any prior instance bound to PORT. Targeted by port (not a blanket
#    pkill), so unrelated servers are never touched.
stop_prior() {
  local pids
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  [ -z "$pids" ] && return 0
  log "stopping prior instance(s): $(echo "$pids" | tr '\n' ' ')"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 0.5
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
  fi
}

# 2. Start a detached server serving the site source directly (server.py blocks
#    dev files, so they are never web-reachable).
start() {
  cd "$SITE_SRC" || exit 1
  ASTRA_SITE_PORT="$PORT" nohup python3 server.py >"$LOG" 2>&1 &
  log "started detached server (pid $!) on :${PORT} (log: $LOG)"
}

# 3. Wait until it answers 200.
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
start
code="$(wait_ready)"
log "healthcheck GET ${HEALTH} -> HTTP ${code}"
if [ "$code" = "200" ]; then
  log "OK — company site is up on :${PORT}"
  exit 0
fi
log "ERROR — site did not return 200 (last code ${code}); see ${LOG}"
exit 1
