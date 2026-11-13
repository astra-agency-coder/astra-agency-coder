"""Astra Trading — market data layer.

Primary source: BiQuote (https://biquote.io) — free, no API key, MetaTrader 5
aggregated OHLCV. Endpoint: GET /api/{symbol}/ohlc?interval={tf}&count={n}

A local on-disk cache keeps us polite to the free endpoint and lets the engine
run offline in tests.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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
    return CACHE / f"{symbol}_{tf}_{count}.json"


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


def _parse(payload: dict) -> list[Candle]:
    bars: Iterable[dict] = payload.get("bars", [])
    out: list[Candle] = []
    for b in bars:
        try:
            out.append(Candle(
                t=str(b.get("openTime") or b.get("time") or ""),
                o=float(b["open"]), h=float(b["high"]),
                l=float(b["low"]), c=float(b["close"]),  # noqa: E741
                v=float(b.get("tickVolume") or b.get("volume") or 0),
            ))
        except (KeyError, TypeError, ValueError):
            continue
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
