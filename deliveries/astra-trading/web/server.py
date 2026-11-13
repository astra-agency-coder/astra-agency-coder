#!/usr/bin/env python3
"""Astra Trading — Command Deck server.

Serves the static web app (vanilla HTML/CSS/JS, no build step) and exactly one
JSON endpoint:

    GET /api/analysis?tf=1h   -> engine.analysis.analyse() payload (+ tick)

`tf` is one of 5m, 15m, 1h, 4h, 1d (case-insensitive). The response is the
engine's own analyse() dict, extended with two additive fields:

    tick    : {bid, ask, spread, mid, source, ts}  (bid/ask + spread)
    source  : "live" | "fixture"                   (data provenance, for honesty)

Live market data comes from the engine (BiQuote). If upstream is unreachable the
server falls back to the bundled fixtures in data/fixtures/<tf>.json so the deck
always renders — and says so via `source`.

Run:  python3 server.py            (listens on 0.0.0.0:8090)
      ASTRA_TRADING_PORT=9000 python3 server.py
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT.parent / "engine"
FIXTURES = ROOT / "data" / "fixtures"
sys.path.insert(0, str(ENGINE))

PORT = int(os.environ.get("ASTRA_TRADING_PORT", "8090"))

# Only these are ever web-reachable; everything else (server.py, dotfiles,
# directory listings) is a hard 404 so internals never leak.
PUBLIC_SUFFIXES = {
    ".html", ".css", ".js", ".mjs", ".json", ".svg", ".png", ".jpg", ".jpeg",
    ".webp", ".gif", ".ico", ".woff2", ".woff", ".ttf", ".txt", ".webmanifest",
}

TF_ALIASES = {"5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h",
              "1d": "1d", "1D": "1d", "1D".lower(): "1d", "day": "1d"}

# analyse() is CPU-light but the upstream fetch blocks on the network; serialise
# per-timeframe so a burst of requests cannot stampede the free endpoint.
_locks: dict[str, threading.Lock] = {tf: threading.Lock() for tf in ("5m", "15m", "1h", "4h", "1d")}
_cache: dict[str, tuple[float, dict]] = {}
import time  # noqa: E402

CACHE_TTL = 20.0


def _norm_tf(raw: str | None) -> str:
    tf = (raw or "1h").strip()
    key = tf.lower()
    if key not in _locks:
        raise ValueError(f"unsupported timeframe {raw!r}; use one of 5m, 15m, 1h, 4h, 1d")
    return key


def _derive_tick(candles: list[dict], spread: float = 0.17) -> dict:
    """Synthetic bid/ask from the newest candle when the live tick is unavailable."""
    c = float(candles[0]["c"]) if candles else 0.0
    half = spread / 2
    return {"bid": round(c - half, 3), "ask": round(c + half, 3),
            "spread": round(spread, 3), "mid": round(c, 3),
            "source": "derived from last candle", "ts": candles[0]["t"] if candles else None}


def _fixture(tf: str) -> dict:
    p = FIXTURES / f"{tf}.json"
    if not p.exists():
        raise RuntimeError(f"no live data and no fixture for {tf}")
    return json.loads(p.read_text())


def build_payload(tf: str) -> dict:
    """Live engine analysis, falling back to a bundled fixture. Never raises."""
    from analysis import analyse  # noqa: E402  (engine on sys.path)
    from market import fetch_tick  # noqa: E402

    source = "live"
    try:
        with _locks[tf]:
            payload = analyse("XAUUSD", tf, 300)
    except Exception:
        payload = _fixture(tf)
        source = "fixture"

    tick = None
    if source == "live":
        try:
            t = fetch_tick("XAUUSD")
            tick = {"bid": round(float(t["bid"]), 3), "ask": round(float(t["ask"]), 3),
                    "spread": round(float(t.get("spread", t["ask"] - t["bid"])), 3),
                    "mid": round(float(t.get("mid", (t["bid"] + t["ask"]) / 2)), 3),
                    "source": t.get("source", "BiQuote"), "ts": t.get("timestamp")}
        except Exception:
            tick = None
    if tick is None:
        tick = _derive_tick(payload.get("candles", []))

    payload["tick"] = tick
    payload["source"] = source
    payload["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return payload


def cached_payload(tf: str) -> dict:
    now = time.time()
    hit = _cache.get(tf)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    payload = build_payload(tf)
    _cache[tf] = (now, payload)
    return payload


class Handler(SimpleHTTPRequestHandler):
    server_version = "AstraTrading/1.0"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):  # quieter logs
        sys.stderr.write("[astra-trading] %s\n" % (fmt % args))

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self._json(200, {"ok": True, "service": "astra-trading-command-deck"})
        if parsed.path == "/api/analysis":
            qs = parse_qs(parsed.query)
            try:
                tf = _norm_tf(qs.get("tf", ["1h"])[0])
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            try:
                return self._json(200, cached_payload(tf))
            except Exception as e:  # never 500 the deck
                return self._json(503, {"error": f"analysis unavailable: {e}", "timeframe": tf})

        path = parsed.path
        if path in ("/", ""):
            path = "/index.html"
        target = (ROOT / path.lstrip("/")).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            return self.send_error(404)
        if not target.is_file() or target.suffix.lower() not in PUBLIC_SUFFIXES:
            return self.send_error(404)
        return super().do_GET()

    def do_HEAD(self):
        self.do_GET()

    def end_headers(self):
        # belt-and-braces: no directory listings, no sniffing
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404, "No directory listing")
        return None


def main() -> None:
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[astra-trading] command deck on http://0.0.0.0:{PORT}  (root: {ROOT})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
