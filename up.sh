#!/usr/bin/env bash
# Bring up every public service in one command. The runtime is idle-recycled,
# so after any recycle run this and everything is back.
#
#   ./up.sh
#
# Ports are fixed by convention (see AGENTS.md):
#   12000 company site   (ops/heal.py assumes this; Next.js in astra-site-v2)
#   12001 Astra Trading  (deck + API on one origin)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[up] company site -> :12000"
( cd "$ROOT/deliveries/astra-site-v2" && ASTRA_SITE_PORT=12000 bash serve.sh )

echo "[up] astra trading -> :12001"
cd "$ROOT/deliveries/astra-trading"
python3 -m pip install -q -r requirements.txt 2>/dev/null || true
( cd api && ASTRA_TRADING_PORT=12001 nohup python3 -m uvicorn app:app \
    --host 0.0.0.0 --port 12001 > /tmp/astra12001.log 2>&1 & )

for _ in $(seq 1 20); do
  sleep 2
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 http://127.0.0.1:12001/ 2>/dev/null || true)"
  [ "$code" = "200" ] && break
done
printf '[up] trading healthcheck -> HTTP %s\n' "${code:-000}"
[ "${code:-000}" = "200" ]
