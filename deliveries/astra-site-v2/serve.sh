#!/usr/bin/env bash
# Launcher for the AI ASTRA AGENCY company site (Next.js, deliveries/astra-site-v2).
#
# Idempotent: safe to run repeatedly. Builds only when there is no production
# build, then serves it. This is the canonical public site on :12000.
#
#   ASTRA_SITE_PORT=12000 bash serve.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${ASTRA_SITE_PORT:-12000}"
LOG="${ASTRA_SITE_LOG:-/tmp/astra-site-v2.log}"

cd "$HERE"

# Dependencies survive a runtime recycle less often than the source does.
if [ ! -d node_modules ]; then
  echo "[site] installing dependencies"
  npm install --no-audit --no-fund >>"$LOG" 2>&1 || { echo "[site] npm install failed"; exit 1; }
fi

if [ ! -f .next/BUILD_ID ]; then
  echo "[site] building"
  npm run build >>"$LOG" 2>&1 || { echo "[site] build failed"; exit 1; }
fi

# Already serving? Leave it alone.
if curl -fsS -o /dev/null --max-time 3 "http://127.0.0.1:${PORT}/en"; then
  echo "[site] already up on :${PORT}"
  exit 0
fi

echo "[site] starting on :${PORT}"
nohup npm run start -- --port "$PORT" -H 0.0.0.0 >>"$LOG" 2>&1 &

for _ in $(seq 1 30); do
  sleep 2
  if curl -fsS -o /dev/null --max-time 4 "http://127.0.0.1:${PORT}/en"; then
    echo "[site] ready on :${PORT}"
    exit 0
  fi
done

echo "[site] failed to come up; see $LOG"
exit 1
