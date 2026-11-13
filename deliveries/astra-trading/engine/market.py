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
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
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


# ── Long-history provider (for backtesting) ──────────────────────────
# BiQuote caps history at ~101 bars, which is far too short to say anything
# about edge. Yahoo Finance exposes real, long XAU/USD-proxy history (gold
# futures GC=F, which tracks spot within a basis of a few dollars) so the
# backtester can replay thousands of bars instead of a hundred.

YF_INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "1h", "1d": "1d",
}
YF_RANGE = {"1m": "7d", "5m": "1mo", "15m": "1mo", "30m": "1mo",
            "1h": "3mo", "4h": "1y", "1d": "5y"}


def fetch_history(symbol: str = "XAUUSD", timeframe: str = "1h",
                  ttl: int = 3600) -> list[Candle]:
    """Long historical series (thousands of bars), newest first.

    Uses the gold-futures continuous contract as the XAU/USD proxy. 4h is
    resampled from 1h. Falls back to the short BiQuote series only if Yahoo
    is unreachable, so callers always get *something* rather than an error.
    """
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    yf_sym = "GC=F" if symbol.upper() in ("XAUUSD", "GOLD", "XAU") else symbol
    interval = YF_INTERVALS[timeframe]
    rng = YF_RANGE[timeframe]

    cp = CACHE / f"HIST_{yf_sym.replace('=','_')}_{interval}_{rng}.json"
    payload = None
    if cp.exists() and (time.time() - cp.stat().st_mtime) < ttl:
        payload = json.loads(cp.read_text())
    else:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
               f"{urllib.parse.quote(yf_sym)}?interval={interval}&range={rng}")
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AstraTrading/1.0)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.loads(r.read().decode())
            cp.write_text(json.dumps(payload))
        except Exception:  # noqa: BLE001
            if cp.exists():
                payload = json.loads(cp.read_text())
            else:
                return fetch_candles(symbol, timeframe, 101, ttl=0)

    out = _parse_yahoo(payload)
    if timeframe == "4h":
        out = _resample(out, 4)
    return out


def _parse_yahoo(payload) -> list[Candle]:
    try:
        res = payload["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError):
        return []
    out: list[Candle] = []
    for i, t in enumerate(ts):
        try:
            o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]  # noqa: E741
            if None in (o, h, l, c):
                continue
            o, h, l, c = float(o), float(h), float(l), float(c)  # noqa: E741
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if not all(math.isfinite(v) and v > 0 for v in (o, h, l, c)) or h < l:  # noqa: E741
            continue
        vol = q.get("volume", [None] * len(ts))[i]
        out.append(Candle(
            t=datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="seconds"),
            o=o, h=h, l=l, c=c,  # noqa: E741
            v=float(vol) if vol else 0.0,
        ))
    out.sort(key=lambda c: c.t, reverse=True)
    return out


def _resample(candles: list[Candle], factor: int) -> list[Candle]:
    """Merge every `factor` consecutive bars (chronological) into one."""
    chrono = list(reversed(candles))
    merged: list[Candle] = []
    for i in range(0, len(chrono), factor):
        chunk = chrono[i:i + factor]
        if not chunk:
            continue
        merged.append(Candle(
            t=chunk[0].t,
            o=chunk[0].o,
            h=max(c.h for c in chunk),
            l=min(c.l for c in chunk),  # noqa: E741
            c=chunk[-1].c,
            v=sum(c.v for c in chunk),
        ))
    merged.reverse()
    return merged


if __name__ == "__main__":
    cs = fetch_candles("XAUUSD", "1h", 5, ttl=0)
    print(f"{len(cs)} candles, newest={cs[0].t} close={cs[0].c}")
    print("tick:", fetch_tick()["mid"], "spread", fetch_tick()["spread"])
