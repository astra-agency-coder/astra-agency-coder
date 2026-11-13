"""Astra Trading — setup backtester.

Replays the engine's *own* setup logic over historical candles and reports what
would actually have happened. This exists so performance claims can be measured
instead of asserted: nothing here invents a result, it only replays real bars.

Method (deliberately conservative):
  * Walk the series bar by bar. At each bar, ask the engine for a setup using
    only the candles available up to that point (no look-ahead).
  * When a setup appears, enter at its entry price on the next bar. If the next
    bar never reaches the entry, the setup is skipped, not counted.
  * A trade closes when price touches the stop or TP1. Ties resolve against the
    trade (worst case), so the result can only be pessimistic.
  * One position at a time, so overlapping setups are not double-counted.

Usage:
    python3 engine/backtest.py [symbol] [timeframe] [bars]
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analysis import build_setup, _clean  # noqa: E402
from market import Candle, fetch_candles  # noqa: E402

WARMUP = 60          # bars needed before the engine can form a view
LOOKBACK = 200       # bars the engine is allowed to see at each step


@dataclass
class Trade:
    direction: str
    entry: float
    stop: float
    tp1: float
    outcome: str        # "tp1" | "stop" | "open"
    r_multiple: float   # realised R, negative on a stop
    entry_bar: int
    exit_bar: int | None


def _r_multiple(direction: str, entry: float, stop: float, exit_price: float) -> float:
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    reward = (exit_price - entry) if direction == "long" else (entry - exit_price)
    return round(reward / risk, 3)


def run(candles: list[Candle], step: int = 4, min_rr: float = 1.5) -> dict:
    """Replay the engine over `candles` (newest first, as the source returns)."""
    series = _clean(candles)
    if len(series) < WARMUP + 10:
        return {"error": "not enough history", "bars": len(series)}

    # Engine reads newest-first; replay oldest-first.
    chrono = list(reversed(series))
    trades: list[Trade] = []
    i = WARMUP
    while i < len(chrono) - 1:
        window = list(reversed(chrono[max(0, i - LOOKBACK): i]))
        setup = build_setup(window, "replay", min_rr=min_rr)
        if setup is None:
            i += step
            continue

        nxt = chrono[i + 1]
        entry, stop = setup.entry, setup.stop_loss
        direction = setup.direction  # "long" | "short"

        # Enter only if the next bar actually trades through the entry.
        if not (nxt.l <= entry <= nxt.h):
            i += step
            continue

        exit_price = None
        exit_bar = None
        for j in range(i + 1, min(i + 1 + LOOKBACK, len(chrono))):
            bar = chrono[j]
            hit_stop = bar.l <= stop if direction == "long" else bar.h >= stop
            hit_tp = bar.h >= setup.tp1 if direction == "long" else bar.l <= setup.tp1
            if hit_stop:                      # worst case wins on a tie
                exit_price, exit_bar = stop, j
                break
            if hit_tp:
                exit_price, exit_bar = setup.tp1, j
                break

        if exit_price is None:
            trades.append(Trade(direction, entry, stop, setup.tp1, "open",
                                _r_multiple(direction, entry, stop, chrono[-1].c), i, None))
            break
        outcome = "stop" if exit_price == stop else "tp1"
        trades.append(Trade(direction, entry, stop, setup.tp1, outcome,
                            _r_multiple(direction, entry, stop, exit_price), i, exit_bar))
        i = (exit_bar or i) + 1

    closed = [t for t in trades if t.outcome != "open"]
    wins = [t for t in closed if t.r_multiple > 0]
    losses = [t for t in closed if t.r_multiple <= 0]
    total_r = round(sum(t.r_multiple for t in closed), 3)
    # A handful of trades says nothing about edge. Below the threshold we report
    # the numbers but mark them as not yet meaningful, so they are never quoted
    # as performance.
    adequate = len(closed) >= 30
    return {
        "symbol": "XAUUSD",
        "bars_replayed": len(chrono),
        "trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(closed), 3) if closed else None,
        "total_r": total_r,
        "avg_r": round(total_r / len(closed), 3) if closed else None,
        "max_drawdown_r": _max_drawdown(closed),
        "open_positions": len(trades) - len(closed),
        "sample_adequate": adequate,
        "note": (
            "sample is large enough to read"
            if adequate
            else f"only {len(closed)} closed trades — below the 30 needed to "
                 "say anything about edge; the data source caps history at 101 "
                 "bars per timeframe, so a real sample needs a longer-history feed"
        ),
        "trades_detail": [asdict(t) for t in trades],
    }


def _max_drawdown(closed: list[Trade]) -> float:
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for t in closed:
        equity += t.r_multiple
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return round(worst, 3)


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    tf = sys.argv[2] if len(sys.argv) > 2 else "1h"
    bars = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    data = fetch_candles(symbol, tf, bars, ttl=0)
    result = run(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
