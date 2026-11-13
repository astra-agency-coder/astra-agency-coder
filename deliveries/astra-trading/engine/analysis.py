"""Astra Trading — analysis engine.

Pure functions over candles. No network, no DB — everything here is testable.

Implements:
  * ATR (volatility)
  * Swing pivots → support / resistance zones (clustered)
  * Liquidity: equal highs/lows, session extremes, round numbers
  * Session context (Asia / London / New York) in UTC
  * Structure bias (higher-highs/higher-lows vs the reverse)
  * Setup construction with entry / stop / targets / R:R
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Sequence

from market import Candle


# --------------------------------------------------------------------------- #
# volatility
# --------------------------------------------------------------------------- #
def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _clean(candles: Sequence[Candle]) -> list[Candle]:
    """Drop candles whose OHLC is not a finite, positive, ordered number set.

    Market feeds occasionally emit gaps, NaNs or sentinel values; a single bad
    bar must not take the whole analysis down.
    """
    out = []
    for c in candles or []:
        if not all(_finite(v) for v in (c.o, c.h, c.l, c.c)):
            continue
        if min(c.o, c.h, c.l, c.c) <= 0:
            continue
        if c.h < c.l:
            continue
        out.append(c)
    return out


def atr(candles: Sequence[Candle], period: int = 14) -> float:
    """Average true range over the most recent `period` candles."""
    seq = list(reversed(_clean(candles)))     # oldest → newest
    if len(seq) < 2:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(seq)):
        prev, cur = seq[i - 1], seq[i]
        trs.append(max(cur.h - cur.l, abs(cur.h - prev.c), abs(cur.l - prev.c)))
    if not trs:
        return 0.0
    window = trs[-period:]
    return sum(window) / len(window)


def ema(values: Sequence[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def sma(values: Sequence[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


# --------------------------------------------------------------------------- #
# pivots and zones
# --------------------------------------------------------------------------- #
@dataclass
class Zone:
    kind: str                 # "resistance" | "support"
    low: float
    high: float
    touches: int
    strength: float           # 0..1
    last_touch: str

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


def swing_points(candles: Sequence[Candle], left: int = 2, right: int = 2):
    """Return (highs, lows) lists of (index, price, time) using fractal pivots.

    `candles` is newest-first; we work oldest-first internally.
    """
    seq = list(reversed(_clean(candles)))
    highs, lows = [], []
    n = len(seq)
    if n < left + right + 1:
        return highs, lows
    for i in range(left, n - right):
        window = seq[i - left:i + right + 1]
        cur = seq[i]
        if cur.h >= max(w.h for w in window):
            highs.append((i, cur.h, cur.t))
        if cur.l <= min(w.l for w in window):
            lows.append((i, cur.l, cur.t))
    return highs, lows


def cluster_zones(points: list[tuple[int, float, str]], kind: str,
                  tol: float) -> list[Zone]:
    """Group nearby pivot prices into zones. `tol` is an absolute price band."""
    if not points:
        return []
    pts = sorted(points, key=lambda p: p[1])
    groups: list[list[tuple[int, float, str]]] = [[pts[0]]]
    for p in pts[1:]:
        if p[1] - groups[-1][-1][1] <= tol:
            groups[-1].append(p)
        else:
            groups.append([p])
    zones: list[Zone] = []
    for g in groups:
        prices = [p[1] for p in g]
        lo, hi = min(prices), max(prices)
        touches = len(g)
        # strength: more touches and a tighter band is stronger
        tightness = 1.0 if hi == lo else max(0.0, 1 - (hi - lo) / (tol * 2))
        strength = min(1.0, 0.35 * touches + 0.4 * tightness + 0.25 * min(touches, 3) / 3)
        zones.append(Zone(kind=kind, low=lo, high=hi, touches=touches,
                          strength=round(strength, 3),
                          last_touch=max(p[2] for p in g)))
    zones.sort(key=lambda z: z.strength, reverse=True)
    return zones


def relevant(zones: list[Zone], price: float, atr_value: float,
             span: float = 12.0) -> list[Zone]:
    """Keep only zones within `span` × ATR of the current price, nearest first."""
    band = max(atr_value * span, price * 0.01)
    keep = [z for z in zones if abs(z.mid - price) <= band]
    keep.sort(key=lambda z: abs(z.mid - price))
    return keep


def find_zones(candles: Sequence[Candle], atr_value: float | None = None,
               left: int = 2, right: int = 2, span: float = 12.0) -> dict:
    candles = _clean(candles)
    if not candles:
        return {"atr": 0.0, "tolerance": 0.0, "resistances": [], "supports": []}
    a = atr_value or atr(candles)
    tol = max(a * 0.35, 0.4)                  # band width scales with volatility
    price = candles[0].c
    highs, lows = swing_points(candles, left, right)
    resistances = relevant(cluster_zones(highs, "resistance", tol), price, a, span)
    supports = relevant(cluster_zones(lows, "support", tol), price, a, span)
    return {"atr": round(a, 3), "tolerance": round(tol, 3),
            "resistances": [asdict(z) for z in resistances],
            "supports": [asdict(z) for z in supports]}


# --------------------------------------------------------------------------- #
# liquidity
# --------------------------------------------------------------------------- #
@dataclass
class Liquidity:
    kind: str        # "equal_highs" | "equal_lows" | "session_high" | "session_low" | "round_number"
    price: float
    note: str
    strength: float


def find_liquidity(candles: Sequence[Candle], atr_value: float) -> list[Liquidity]:
    """Liquidity pools where stops are likely to rest."""
    out: list[Liquidity] = []
    candles = _clean(candles)
    if not candles:
        return out
    seq = list(reversed(candles))
    tol = max((atr_value if _finite(atr_value) else 0.0) * 0.25, 0.3)

    # equal highs / lows (double tops/bottoms within tolerance)
    highs = [(c.t, c.h) for c in seq]
    lows = [(c.t, c.l) for c in seq]
    for i in range(len(highs) - 1):
        for j in range(i + 1, min(i + 12, len(highs))):
            if abs(highs[i][1] - highs[j][1]) <= tol:
                out.append(Liquidity("equal_highs", round((highs[i][1] + highs[j][1]) / 2, 3),
                                     "equal highs — buy-side liquidity", 0.7))
                break
        for j in range(i + 1, min(i + 12, len(lows))):
            if abs(lows[i][1] - lows[j][1]) <= tol:
                out.append(Liquidity("equal_lows", round((lows[i][1] + lows[j][1]) / 2, 3),
                                     "equal lows — sell-side liquidity", 0.7))
                break

    # session extremes for the current UTC day
    day = datetime.now(timezone.utc).date().isoformat()
    today = [c for c in seq if c.t.startswith(day)]
    if today:
        out.append(Liquidity("session_high", round(max(c.h for c in today), 3),
                             "session high — stops above", 0.6))
        out.append(Liquidity("session_low", round(min(c.l for c in today), 3),
                             "session low — stops below", 0.6))

    # round numbers (psychological levels)
    if candles:
        ref = candles[0].c
        step = 25.0 if ref > 1000 else 1.0
        base = round(ref / step) * step
        for k in (-2, -1, 0, 1, 2):
            lvl = base + k * step
            out.append(Liquidity("round_number", round(lvl, 2),
                                 f"round level {lvl:.0f}", 0.45))

    # dedupe by (kind, price), then rank by proximity to price
    ref = candles[0].c
    seen: set[tuple[str, float]] = set()
    uniq: list[Liquidity] = []
    for lq in sorted(out, key=lambda x: (-x.strength, abs(x.price - ref))):
        key = (lq.kind, round(lq.price, 2))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(lq)
    uniq.sort(key=lambda x: abs(x.price - ref))
    return uniq


# --------------------------------------------------------------------------- #
# sessions
# --------------------------------------------------------------------------- #
def session_context(now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    h = now.hour
    if 0 <= h < 7:
        name = "asia"
    elif 7 <= h < 12:
        name = "london"
    elif 12 <= h < 16:
        name = "london_ny_overlap"
    elif 16 <= h < 21:
        name = "new_york"
    else:
        name = "late"
    return {"name": name, "utc_hour": h,
            "note": {
                "asia": "low volatility, range-building",
                "london": "high volatility, trend ignition",
                "london_ny_overlap": "highest liquidity of the day",
                "new_york": "US data driven moves",
                "late": "thin liquidity, avoid new entries",
            }[name]}


# --------------------------------------------------------------------------- #
# structure bias
# --------------------------------------------------------------------------- #
def bias(candles: Sequence[Candle]) -> dict:
    candles = _clean(candles)
    if len(candles) < 2:
        return {"direction": "neutral", "score": 0.0, "ema21": None,
                "ema50": None, "last_close": None}
    closes = [c.c for c in reversed(candles)]
    e21 = ema(closes, 21)
    e50 = ema(closes, 50)
    last = closes[-1]
    fast, slow = e21[-1], e50[-1]
    if fast > slow and last > fast:
        direction, score = "bullish", 0.7
    elif fast < slow and last < fast:
        direction, score = "bearish", 0.7
    elif fast > slow:
        direction, score = "bullish_weak", 0.4
    elif fast < slow:
        direction, score = "bearish_weak", 0.4
    else:
        direction, score = "neutral", 0.2
    return {"direction": direction, "score": score,
            "ema21": round(fast, 3), "ema50": round(slow, 3),
            "last_close": round(last, 3)}


# --------------------------------------------------------------------------- #
# setup construction
# --------------------------------------------------------------------------- #
@dataclass
class Setup:
    symbol: str
    direction: str
    entry_type: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    risk_reward: float
    timeframe: str
    session: str
    confidence: float
    factors: list[str] = field(default_factory=list)
    invalidation: str = ""
    rationale: str = ""


def build_setup(candles: Sequence[Candle], timeframe: str = "1h",
                min_rr: float = 1.5) -> Setup | None:
    """Build the best available setup, or None if nothing meets the bar."""
    candles = _clean(candles)
    if len(candles) < 60:
        return None
    price = candles[0].c
    a = atr(candles)
    if not _finite(a) or a <= 0:
        return None
    z = find_zones(candles, a)
    b = bias(candles)
    sess = session_context()
    liq = find_liquidity(candles, a)

    factors: list[str] = []

    # choose a direction from structure, then look for a zone to trade from
    if b["direction"].startswith("bullish"):
        supports = [s for s in z["supports"] if s["low"] < price]
        if not supports:
            return None
        zone = max(supports, key=lambda s: (s["strength"], s["high"]))
        entry = zone["high"]
        stop = zone["low"] - a * 0.5
        risk = entry - stop
        if risk <= 0:
            return None
        tp1, tp2, tp3 = entry + risk, entry + risk * 2, entry + risk * 3
        factors.append(f"support zone {zone['low']:.2f}–{zone['high']:.2f} ({zone['touches']} touches)")
        factors.append(f"EMA21 {b['ema21']:.2f} above EMA50 {b['ema50']:.2f}")
        direction, inval = "long", f"close below {stop:.2f}"
    elif b["direction"].startswith("bearish"):
        resistances = [r for r in z["resistances"] if r["high"] > price]
        if not resistances:
            return None
        zone = max(resistances, key=lambda r: (r["strength"], -r["low"]))
        entry = zone["low"]
        stop = zone["high"] + a * 0.5
        risk = stop - entry
        if risk <= 0:
            return None
        tp1, tp2, tp3 = entry - risk, entry - risk * 2, entry - risk * 3
        factors.append(f"resistance zone {zone['low']:.2f}–{zone['high']:.2f} ({zone['touches']} touches)")
        factors.append(f"EMA21 {b['ema21']:.2f} below EMA50 {b['ema50']:.2f}")
        direction, inval = "short", f"close above {stop:.2f}"
    else:
        return None

    rr = abs((tp2 - entry) / (entry - stop)) if entry != stop else 0.0
    if rr < min_rr:
        return None

    factors.append(f"ATR(14) {a:.2f} — stop placed beyond 0.5×ATR")
    factors.append(f"session: {sess['name']} ({sess['note']})")
    near = [l for l in liq if abs(l.price - entry) < a * 2][:2]
    for l in near:
        factors.append(f"liquidity nearby: {l.note} @ {l.price:.2f}")

    confidence = round(min(0.95, 0.45 + 0.25 * b["score"] + 0.15 * (zone["strength"])), 3)

    return Setup(
        symbol="XAUUSD", direction=direction, entry_type="limit",
        entry=round(entry, 2), stop_loss=round(stop, 2),
        tp1=round(tp1, 2), tp2=round(tp2, 2), tp3=round(tp3, 2),
        risk_reward=round(rr, 2), timeframe=timeframe, session=sess["name"],
        confidence=confidence, factors=factors, invalidation=inval,
        rationale=(f"{direction.upper()} XAUUSD from {zone['kind']} at {entry:.2f}; "
                   f"stop {stop:.2f}, targets {tp1:.2f}/{tp2:.2f}/{tp3:.2f}, R:R {rr:.2f}."),
    )


def analyse(symbol: str = "XAUUSD", timeframe: str = "1h", count: int = 300) -> dict:
    """Full analysis payload for the chart + setup card."""
    from market import fetch_candles
    candles = _clean(fetch_candles(symbol, timeframe, count))
    if not candles:
        return {"symbol": symbol, "timeframe": timeframe, "price": None, "atr": 0.0,
                "bias": bias([]), "session": session_context(),
                "zones": find_zones([]), "liquidity": [], "setup": None, "candles": []}
    a = atr(candles)
    return {
        "symbol": symbol, "timeframe": timeframe,
        "price": candles[0].c,
        "atr": round(a, 3),
        "bias": bias(candles),
        "session": session_context(),
        "zones": find_zones(candles, a),
        "liquidity": [asdict(l) for l in find_liquidity(candles, a)][:12],
        "setup": (lambda s: asdict(s) if s else None)(build_setup(candles, timeframe)),
        "candles": [asdict(c) for c in candles],
    }


if __name__ == "__main__":
    import json
    d = analyse()
    print(json.dumps({k: v for k, v in d.items() if k != "candles"}, indent=2, ensure_ascii=False))
