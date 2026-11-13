"""Astra Trading — market data layer.

Primary source: BiQuote (https://biquote.io) — free, no API key, MetaTrader 5
aggregated OHLCV. Endpoint: GET /api/{symbol}/ohlc?interval={tf}&count={n}

A local on-disk cache keeps us polite to the free endpoint and lets the engine
run offline in tests.
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable  # noqa: F401

BASE = os.environ.get("BIQUOTE_BASE", "https://biquote.io").rstrip("/")
CACHE = Path(os.environ.get("ASTRA_CACHE_DIR", "/tmp/astra-cache"))
CACHE.mkdir(parents=True, exist_ok=True)

# BiQuote interval tokens we use
TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")


@dataclass(frozen=True)
class Candle:
    t: str          # ISO8601 open time (UTC)
    o: float
    h: float
    l: float        # noqa: E741
    c: float
    v: float = 0.0  # tick volume

    @property
    def bullish(self) -> bool:
        return self.c >= self.o


def _cache_path(symbol: str, tf: str, count: int) -> Path:
    # Symbol comes from callers, so keep it filesystem-safe: a bad value must
    # never produce a path outside CACHE (or an over-long filename).
    safe = "".join(ch for ch in symbol.upper() if ch.isalnum())[:16] or "UNKNOWN"
    return CACHE / f"{safe}_{tf}_{int(count)}.json"


def fetch_candles(symbol: str = "XAUUSD", timeframe: str = "1h",
                  count: int = 300, ttl: int = 60, retries: int = 3) -> list[Candle]:
    """Return `count` candles, newest first, as returned by the source."""
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unsupported timeframe {timeframe!r}; use one of {TIMEFRAMES}")

    cp = _cache_path(symbol, timeframe, count)
    if cp.exists() and (time.time() - cp.stat().st_mtime) < ttl:
        return _parse(json.loads(cp.read_text()))

    url = f"{BASE}/api/{symbol}/ohlc?interval={timeframe}&count={count}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "astra-trading/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                payload = json.loads(r.read().decode())
            cp.write_text(json.dumps(payload))
            return _parse(payload)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    if cp.exists():                       # stale cache beats no data
        return _parse(json.loads(cp.read_text()))
    raise RuntimeError(f"market data unavailable for {symbol} {timeframe}: {last}")


def _parse(payload) -> list[Candle]:
    if not isinstance(payload, dict):
        return []
    bars = payload.get("bars")
    if not isinstance(bars, list):
        return []
    out: list[Candle] = []
    for b in bars:
        if not isinstance(b, dict):
            continue
        try:
            o, h, l, c = (float(b["open"]), float(b["high"]),  # noqa: E741
                          float(b["low"]), float(b["close"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(v) and v > 0 for v in (o, h, l, c)) or h < l:  # noqa: E741
            continue
        try:
            v = float(b.get("tickVolume") or b.get("volume") or 0)
        except (TypeError, ValueError):
            v = 0.0
        out.append(Candle(
            t=str(b.get("openTime") or b.get("time") or ""),
            o=o, h=h, l=l, c=c,  # noqa: E741
            v=v if math.isfinite(v) else 0.0,
        ))
    out.sort(key=lambda c: c.t, reverse=True)
    return out


def fetch_tick(symbol: str = "XAUUSD") -> dict:
    req = urllib.request.Request(f"{BASE}/api/{symbol}",
                                 headers={"Accept": "application/json",
                                          "User-Agent": "astra-trading/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


if __name__ == "__main__":
    cs = fetch_candles("XAUUSD", "1h", 5, ttl=0)
    print(f"{len(cs)} candles, newest={cs[0].t} close={cs[0].c}")
    print("tick:", fetch_tick()["mid"], "spread", fetch_tick()["spread"])
