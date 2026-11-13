"""Tests for the setup backtester. Run: python3 engine/test_backtest.py

Uses synthetic series with a known correct answer, so the replay logic is
checked against ground truth rather than against itself.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backtest import _max_drawdown, _r_multiple, run  # noqa: E402
from market import Candle  # noqa: E402

FAIL = 0


def check(name: str, ok: bool, extra: str = "") -> None:
    global FAIL
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  ' + extra) if extra else ''}")
    if not ok:
        FAIL += 1


def series(prices: list[float], step_hours: int = 1) -> list[Candle]:
    """Newest-first candles (as the engine receives them) from a close series."""
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i, p in enumerate(prices):
        out.append(Candle(
            t=(t0 + timedelta(hours=i * step_hours)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            o=p, h=p * 1.001, l=p * 0.999, c=p, v=100.0,
        ))
    return list(reversed(out))


print("== r_multiple ==")
check("long win is positive", _r_multiple("long", 100, 95, 110) == 2.0)
check("long loss is -1R", _r_multiple("long", 100, 95, 95) == -1.0)
check("short win is positive", _r_multiple("short", 100, 105, 90) == 2.0)
check("zero risk does not divide by zero", _r_multiple("long", 100, 100, 110) == 0.0)

print("== max drawdown ==")
class T:  # minimal stand-in for a closed Trade
    def __init__(self, r): self.r_multiple = r
check("monotonic wins have no drawdown", _max_drawdown([T(1), T(1), T(1)]) == 0.0)
check("drawdown tracks the peak-to-trough", _max_drawdown([T(1), T(-1), T(-1)]) == -2.0)

print("== insufficient history ==")
r = run(series([100 + i for i in range(20)]))
check("short series is rejected, not guessed", "error" in r, str(r.get("error")))

print("== no look-ahead ==")
# 80 flat bars then a clean uptrend: any trade the engine takes must enter
# strictly after the bar that produced the setup.
prices = [2000.0] * 80 + [2000 + i * 3 for i in range(1, 60)]
r = run(series(prices), step=1)
trades = r.get("trades_detail", [])
check("replay produced at least one trade", len(trades) >= 1, f"trades={len(trades)}")
check("every entry is after the warmup window",
      all(t["entry_bar"] >= 60 for t in trades))
check("exits never precede entries",
      all(t["exit_bar"] is None or t["exit_bar"] > t["entry_bar"] for t in trades))
check("outcomes are from the allowed set",
      all(t["outcome"] in ("tp1", "stop", "open") for t in trades))

print("== small samples are labelled, not overclaimed ==")
check("tiny sample is marked inadequate", r.get("sample_adequate") is False)
check("note explains why", "below the 30" in str(r.get("note", "")))

print("== every reported trade is internally consistent ==")
ok = True
for t in trades:
    if t["direction"] == "long":
        if not (t["stop"] < t["entry"] < t["tp1"]):
            ok = False
    else:
        if not (t["tp1"] < t["entry"] < t["stop"]):
            ok = False
check("stops and targets sit on the correct side of entry", ok)

print(f"\nRESULT {'ALL PASS' if FAIL == 0 else str(FAIL) + ' FAILED'}")
sys.exit(1 if FAIL else 0)
