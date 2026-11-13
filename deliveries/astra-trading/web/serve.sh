#!/usr/bin/env bash
# Durable (re)launcher for the Astra Trading Command Deck.
#
# Idempotent: stops any prior instance bound to PORT (matched by the exact
# `python3 server.py` invocation, never a blanket pkill), starts a detached
# server, and waits until /api/health answers 200.
#
#   ./serve.sh                       # port 8090, log /tmp/astra_trading.log
#   ASTRA_TRADING_PORT=9000 ./serve.sh
set -u

PORT="${ASTRA_TRADING_PORT:-8090}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${ASTRA_TRADING_LOG:-/tmp/astra_trading.log}"
HEALTH="http://127.0.0.1:${PORT}/api/health"
# Anchored to our UNIQUE argv (server.py --command-deck) so we never match or
# kill the company site's own `python3 server.py`, which has an identical argv.
PATTERN='^python3 server\.py --command-deck$'

log() { printf '[astra-trading] %s\n' "$*"; }

stop_prior() {
  local pids
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  [ -z "$pids" ] && return 0
  log "stopping prior instance(s): $(echo "$pids" | tr '\n' ' ')"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 0.5
  pids="$(pgrep -f "$PATTERN" 2>/dev/null || true)"
  [ -n "$pids" ] && { kill -9 $pids 2>/dev/null || true; }
}

start() {
  cd "$SRC" || exit 1
  ASTRA_TRADING_PORT="$PORT" nohup python3 server.py --command-deck >"$LOG" 2>&1 &
  log "started detached server (pid $!) on :${PORT} (log: $LOG)"
}

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
  log "OK — Command Deck is up on http://127.0.0.1:${PORT}/"
  exit 0
fi
log "ERROR — deck did not return 200 (last code ${code}); see ${LOG}"
exit 1
