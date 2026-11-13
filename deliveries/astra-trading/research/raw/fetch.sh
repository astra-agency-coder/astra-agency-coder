#!/usr/bin/env bash
# Bounded fetch helper: fetch.sh <name> <url>
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
name="$1"; url="$2"
out="/workspace/project/deliveries/astra-trading/research/raw/${name}.html"
code=$(curl -sS -L -A "$UA" --max-time 45 -o "$out" -w "%{http_code}" "$url" 2>/tmp/fetch_err)
echo "FETCH name=$name http=$code bytes=$(wc -c < "$out" 2>/dev/null) url=$url"
if [ -s /tmp/fetch_err ]; then echo "ERR: $(cat /tmp/fetch_err)"; fi
exit 0
