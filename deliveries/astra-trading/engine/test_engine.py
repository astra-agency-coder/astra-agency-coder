"""Astra Trading — engine tests.

Deterministic tests on synthetic candles with known answers, so we can prove the
analysis is correct rather than just plausible.

Run: python3 test_engine.py
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timezone

from analysis import (atr, bias, build_setup, cluster_zones, ema,
                      find_liquidity, find_zones, session_context, swing_points)
from market import Candle

PASS, FAIL = 0, 0
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}  {detail}")


def candle(i: int, o: float, h: float, l: float, c: float, v: float = 100) -> Candle:  # noqa: E741
    # newest-first ordering is produced by callers; build ascending then reverse
    t = f"2026-11-13T{(i // 60) % 24:02d}:{i % 60:02d}:00Z"
    return Candle(t=t, o=o, h=h, l=l, c=c, v=v)  # noqa: E741


# --------------------------------------------------------------------------- #
print("== ATR ==")
# 20 candles, every true range exactly 2.0 → ATR must be 2.0
flat = [Candle(t=f"2026-11-13T00:{i:02d}:00Z", o=100, h=101, l=99, c=100) for i in range(20)]
check("ATR of uniform 2.0 ranges == 2.0", abs(atr(flat, 14) - 2.0) < 1e-9, f"got {atr(flat,14)}")

# widening ranges raise ATR
wide = flat[:10] + [Candle(t=f"2026-11-13T01:{i:02d}:00Z", o=100, h=110, l=90, c=100) for i in range(10)]
check("ATR rises with wider ranges", atr(wide, 14) > atr(flat, 14), f"{atr(wide,14)} vs {atr(flat,14)}")
check("ATR of empty/short input is 0", atr([flat[0]]) == 0.0)

print("== EMA ==")
e = ema([1, 2, 3, 4, 5], 3)
check("EMA length preserved", len(e) == 5)
check("EMA is monotonic on a rising series", all(e[i] <= e[i + 1] for i in range(4)))
check("EMA of a constant series is that constant", abs(ema([7] * 6, 3)[-1] - 7) < 1e-9)

print("== pivots ==")
# a clean mountain: rises then falls; the peak must be a swing high
seq = []
px = 100.0
for i in range(9):
    px += 1 if i < 4 else -1
    seq.append(Candle(t=f"2026-11-13T0{i}:00:00Z", o=px, h=px + 0.5, l=px - 0.5, c=px))
highs, lows = swing_points(list(reversed(seq)), 2, 2)
peak = max(c.h for c in seq)
check("single clear swing high found at the peak",
      len(highs) == 1 and abs(highs[0][1] - peak) < 0.6, f"highs={highs}")

print("== zone clustering ==")
pts = [(0, 100.0, "t0"), (1, 100.2, "t1"), (2, 100.4, "t2"), (3, 130.0, "t3")]
zs = cluster_zones(pts, "resistance", tol=1.0)
check("nearby pivots collapse into one zone", len(zs) == 2, f"got {len(zs)}")
strong = [z for z in zs if z.touches == 3]
check("the 3-touch zone is strongest", strong and strong[0].strength >= zs[0].strength)

print("== zone filtering by distance ==")
# build a series with a far-away pivot that must be filtered out
cands = []
for i in range(60):
    base = 2000 + math.sin(i / 3) * 5
    cands.append(Candle(t=f"2026-11-1{i%9}T{(i//6)%24:02d}:{i%60:02d}:00Z",
                        o=base, h=base + 1, l=base - 1, c=base))  # noqa: E741
cands.append(Candle(t="2026-11-13T23:59:00Z", o=3000, h=3010, l=2990, c=3000))  # far spike
newest_first = list(reversed(cands))
z = find_zones(newest_first, span=12.0)
far = [r for r in z["resistances"] if r["mid"] > 2900]
check("far-away zone is filtered out", len(far) == 0, f"far={far}")

print("== liquidity ==")
# two equal lows ~ same price → equal_lows must appear
base = 1500.0
series = []
for i in range(30):
    l = base - (0.1 if i in (5, 17) else 0)  # noqa: E741
    series.append(Candle(t=f"2026-11-13T{i//60:02d}:{i%60:02d}:00Z",
                         o=base, h=base + 2, l=l, c=base))
lq = find_liquidity(list(reversed(series)), atr_value=1.0)
kinds = {x.kind for x in lq}
check("equal lows detected", "equal_lows" in kinds, f"kinds={kinds}")
check("round numbers present", "round_number" in kinds, f"kinds={kinds}")
check("liquidity ranked by distance to price",
      all(abs(lq[i].price - series[-1].c) <= abs(lq[i + 1].price - series[-1].c)
          for i in range(len(lq) - 1)))

print("== sessions ==")
check("00:00 UTC is asia", session_context(datetime(2026, 11, 13, 0, tzinfo=timezone.utc))["name"] == "asia")
check("09:00 UTC is london", session_context(datetime(2026, 11, 13, 9, tzinfo=timezone.utc))["name"] == "london")
check("13:00 UTC is london_ny_overlap",
      session_context(datetime(2026, 11, 13, 13, tzinfo=timezone.utc))["name"] == "london_ny_overlap")
check("18:00 UTC is new_york", session_context(datetime(2026, 11, 13, 18, tzinfo=timezone.utc))["name"] == "new_york")
check("22:00 UTC is late", session_context(datetime(2026, 11, 13, 22, tzinfo=timezone.utc))["name"] == "late")

print("== bias ==")
# zig-zag series so real swing pivots exist (a monotonic line has none, and the
# engine correctly refuses to invent structure that is not there)
def wave(n: int, drift: float, amp: float, start: float = 2000.0) -> list[Candle]:
    out = []
    for i in range(n):
        mid = start + drift * i + amp * math.sin(i / 2.0)
        out.append(Candle(t=f"2026-11-13T{(i//60)%24:02d}:{i%60:02d}:00Z",
                          o=mid, h=mid + amp * 0.4, l=mid - amp * 0.4, c=mid))
    return out


up = wave(90, drift=+0.8, amp=6.0)
down = wave(90, drift=-0.8, amp=6.0)
check("uptrend reads bullish", bias(list(reversed(up)))["direction"].startswith("bullish"))
check("downtrend reads bearish", bias(list(reversed(down)))["direction"].startswith("bearish"))

print("== setup integrity ==")
# downtrend with a clear resistance above → short setup with a valid stop
s = build_setup(list(reversed(down)), "1h")
if s:
    check("short setup has stop ABOVE entry", s.stop_loss > s.entry, f"{s.stop_loss} vs {s.entry}")
    check("short setup targets are BELOW entry", s.tp1 < s.entry and s.tp3 < s.entry)
    check("R:R at least 1.5", s.risk_reward >= 1.5, f"rr={s.risk_reward}")
    check("stop respects 0.5xATR padding",
          (s.stop_loss - s.entry) >= 0.5 * atr(list(reversed(down))) - 1e-6)
else:
    check("setup built on a clean trend", False, "no setup returned")

s_up = build_setup(list(reversed(up)), "1h")
if s_up:
    check("long setup has stop BELOW entry", s_up.stop_loss < s_up.entry)
    check("long setup targets are ABOVE entry", s_up.tp1 > s_up.entry and s_up.tp3 > s_up.entry)
else:
    check("long setup built on an uptrend", False, "no setup returned")

check("no setup on insufficient data", build_setup([flat[0]], "1h") is None)

print(f"\nRESULT {PASS}/{PASS+FAIL} passed" + (f"  FAILURES={FAILURES}" if FAILURES else ""))
sys.exit(1 if FAIL else 0)
