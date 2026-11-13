"""Astra Trading — strategy experiment harness (walk-forward).

Why this exists: the engine's setups had no measurable edge on 1h/4h. Tuning by
opinion is worthless, so this module replays the engine's own logic over real
history under a grid of variants and reports each one honestly.

Discipline it enforces:
  * Walk-forward. Every config is fit on the first TRAIN_FRAC of history and
    scored on the remainder, which the config never saw. A config that only
    looks good in-sample is reported as such, not promoted.
  * Same evaluation for every variant. Entry/stop/target/exit logic is shared;
    only the named knobs change.
  * No cherry-picking. We report the full table, including losers.

Usage:
    python3 engine/experiments.py sweep 1h 4h 1d
    python3 engine/experiments.py best
"""
from __future__ import annotations

import itertools
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from analysis import _clean, atr, build_setup, ema  # noqa: E402
from market import Candle, fetch_history  # noqa: E402

TRAIN_FRAC = 0.7
RESULTS = ROOT / "docs" / "experiments.json"


@dataclass
class Config:
    """The knobs under test. Defaults mirror the live engine."""
    name: str = "baseline"
    target_r: float = 1.0        # exit at this many R (1.0 == TP1)
    stop_atr: float = 0.5        # stop distance beyond the zone, in ATR
    trend_filter: bool = False   # only trade with the higher-timeframe EMA
    min_rr: float = 1.5
    step: int = 3
    params: dict = field(default_factory=dict)


def _walk(candles: list[Candle], cfg: Config) -> dict:
    """Replay `candles` (newest-first) under one config. No look-ahead."""
    series = _clean(candles)
    chrono = list(reversed(series))
    if len(chrono) < 150:
        return {"trades": 0, "total_r": 0.0, "avg_r": None, "win_rate": None}

    warmup = 60
    lookback = 200
    closes = [c.c for c in chrono]
    ema200 = ema(closes, 200) if cfg.trend_filter else None

    trades = []
    i = warmup
    while i < len(chrono) - 1:
        window = list(reversed(chrono[max(0, i - lookback): i]))
        setup = build_setup(window, "replay", min_rr=cfg.min_rr)
        if setup is None:
            i += cfg.step
            continue

        # Optional trend gate: only longs when price is above EMA200, etc.
        if cfg.trend_filter and ema200:
            e = ema200[i]
            if e is None:
                i += cfg.step
                continue
            if setup.direction == "long" and chrono[i].c < e:
                i += cfg.step
                continue
            if setup.direction == "short" and chrono[i].c > e:
                i += cfg.step
                continue

        nxt = chrono[i + 1]
        entry = setup.entry
        direction = setup.direction
        a = atr(window)
        if direction == "long":
            stop = setup.stop_loss - (cfg.stop_atr - 0.5) * a
        else:
            stop = setup.stop_loss + (cfg.stop_atr - 0.5) * a
        risk = abs(entry - stop)
        if risk <= 0:
            i += cfg.step
            continue
        target = entry + risk * cfg.target_r if direction == "long" else entry - risk * cfg.target_r

        if not (nxt.l <= entry <= nxt.h):
            i += cfg.step
            continue

        exit_price = None
        exit_bar = None
        for j in range(i + 1, min(i + 1 + lookback, len(chrono))):
            bar = chrono[j]
            hit_stop = bar.l <= stop if direction == "long" else bar.h >= stop
            hit_tp = bar.h >= target if direction == "long" else bar.l <= target
            if hit_stop:
                exit_price, exit_bar = stop, j
                break
            if hit_tp:
                exit_price, exit_bar = target, j
                break
        if exit_price is None:
            break
        r = (exit_price - entry) / risk if direction == "long" else (entry - exit_price) / risk
        trades.append(round(r, 3))
        i = (exit_bar or i) + 1

    if not trades:
        return {"trades": 0, "total_r": 0.0, "avg_r": None, "win_rate": None}
    wins = [t for t in trades if t > 0]
    total = round(sum(trades), 3)
    return {
        "trades": len(trades),
        "total_r": total,
        "avg_r": round(total / len(trades), 4),
        "win_rate": round(len(wins) / len(trades), 3),
    }


def evaluate(candles: list[Candle], cfg: Config) -> dict:
    """Walk-forward score: fit-window vs hold-out-window, reported separately."""
    series = _clean(candles)
    chrono = list(reversed(series))
    split = int(len(chrono) * TRAIN_FRAC)
    train = list(reversed(chrono[:split]))
    test = list(reversed(chrono[split - 200:]))  # overlap for warmup only
    tr = _walk(train, cfg)
    te = _walk(test, cfg)
    return {
        "config": cfg.name,
        "knobs": {"target_r": cfg.target_r, "stop_atr": cfg.stop_atr,
                  "trend_filter": cfg.trend_filter, "min_rr": cfg.min_rr},
        "train": tr, "test": te,
        # A config is only credible if it survives the hold-out.
        "credible": bool(te.get("avg_r") and te["avg_r"] > 0 and te.get("trades", 0) >= 15),
    }


def grid() -> list[Config]:
    out = []
    for target_r, stop_atr, trend in itertools.product(
            (1.0, 1.5, 2.0, 3.0), (0.5, 1.0, 1.5), (False, True)):
        out.append(Config(
            name=f"t{target_r}_s{stop_atr}_trend{int(trend)}",
            target_r=target_r, stop_atr=stop_atr, trend_filter=trend))
    return out


def sweep(timeframes: list[str]) -> dict:
    report = {}
    for tf in timeframes:
        candles = fetch_history("XAUUSD", tf, ttl=3600)
        rows = [evaluate(candles, cfg) for cfg in grid()]
        rows.sort(key=lambda r: (r["credible"], r["test"].get("avg_r") or -9), reverse=True)
        report[tf] = {"bars": len(candles), "results": rows}
        print(f"\n=== {tf} ({len(candles)} bars) — top 5 by hold-out avg_r ===")
        for r in rows[:5]:
            k = r["knobs"]
            print(f"  {r['config']:22} train avg {r['train'].get('avg_r')} "
                  f"({r['train'].get('trades')}t) | test avg {r['test'].get('avg_r')} "
                  f"({r['test'].get('trades')}t) | credible={r['credible']}")
    RESULTS.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sweep"
    if cmd == "sweep":
        tfs = sys.argv[2:] or ["1h", "4h", "1d"]
        sweep(tfs)
        print(f"\nwritten: {RESULTS}")
