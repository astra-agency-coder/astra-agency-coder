#!/usr/bin/env bash
# Healthcheck for the AI ASTRA AGENCY company site (deliveries/astra-site).
# Curls the site root and exits non-zero unless it returns HTTP 200.
#
#   ./healthcheck.sh
#   ASTRA_SITE_PORT=8080 ./healthcheck.sh
set -u

PORT="${ASTRA_SITE_PORT:-12000}"
URL="${ASTRA_SITE_URL:-http://127.0.0.1:${PORT}/}"

code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL" 2>/dev/null || true)"
[ -n "$code" ] || code="000"
printf 'healthcheck: GET %s -> HTTP %s\n' "$URL" "$code"

[ "$code" = "200" ]
