"""Astra Trading — setup outcome evaluator (the honest scoreboard).

A setup is published to users only after it has been scored. This module walks
each open setup against real candles and moves it through its lifecycle:

    proposed → triggered → tp1_hit / tp2_hit / tp3_hit / stopped / breakeven
                        ↘ expired / invalidated

Every transition is written to setup_events, so the record cannot be quietly
edited afterwards. outcome_r is the realised R multiple at the closing event.

Run: python3 evaluator.py            (evaluate every open setup once)
     python3 evaluator.py --loop 60  (keep evaluating every 60s)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from market import fetch_candles  # noqa: E402

OPEN_STATES = ("proposed", "triggered")
WIN_STATES = ("tp1_hit", "tp2_hit", "tp3_hit")


def _sec():
    p = ROOT.parents[1] / "ops" / "secrets.py"
    spec = importlib.util.spec_from_file_location("astra_secrets", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SEC = _sec()
SB_URL = SEC.resolve("ASTRA_SUPABASE_URL")
SB_KEY = SEC.resolve("ASTRA_SUPABASE_SECRET_KEY")


def sb(method: str, table: str, body=None, query: str = ""):
    url = f"{SB_URL}/rest/v1/{table}" + (f"?{query}" if query else "")
    req = urllib.request.Request(
        url, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json",
                 "Prefer": "return=representation"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw.strip() else []


def log_event(setup_id: str, frm: str | None, to: str, price: float | None, reason: str):
    sb("POST", "setup_events", {"setup_id": setup_id, "from_status": frm,
                                "to_status": to, "price": price, "reason": reason})


def r_multiple(direction: str, entry: float, stop: float, price: float) -> float:
    risk = abs(entry - stop)
    if not risk:
        return 0.0
    move = (price - entry) if direction == "long" else (entry - price)
    return round(move / risk, 2)


def evaluate_one(setup: dict, candles) -> str:
    """Return the new status (unchanged if nothing happened)."""
    status = setup["status"]
    direction = setup["direction"]
    entry, stop = float(setup["entry"]), float(setup["stop_loss"])
    tps = [float(setup[k]) for k in ("tp1", "tp2", "tp3") if setup.get(k) is not None]
    created = setup.get("created_at")
    now = datetime.now(timezone.utc)

    # candles arrive newest-first. The newest bar is the one still forming, so it
    # always counts (its high/low already contain the live price). Older bars only
    # count if they formed after the setup was created.
    rev = list(reversed(candles))
    seq = [c for i, c in enumerate(rev)
           if i == len(rev) - 1 or not created or c.t >= created]

    if status == "proposed":
        if setup.get("validity_until") and now.isoformat() > setup["validity_until"]:
            log_event(setup["id"], "proposed", "expired", None, "validity window elapsed")
            return "expired"
        for c in seq:
            touched = (c.l <= entry) if direction == "long" else (c.h >= entry)
            if touched:
                # did it invalidate on the same candle before triggering?
                sb("PATCH", "setups", {"status": "triggered", "triggered_at": c.t}, f"id=eq.{setup['id']}")
                log_event(setup["id"], "proposed", "triggered", entry, f"entry touched at {c.t}")
                status = "triggered"
                break
        else:
            return status

    if status == "triggered":
        for c in seq:
            # stop first: assume the worse fill inside a candle
            if direction == "long" and c.l <= stop:
                r = r_multiple(direction, entry, stop, stop)
                sb("PATCH", "setups", {"status": "stopped", "closed_at": c.t,
                                       "outcome_price": stop, "outcome_r": r}, f"id=eq.{setup['id']}")
                log_event(setup["id"], "triggered", "stopped", stop, "stop hit")
                return "stopped"
            if direction == "short" and c.h >= stop:
                r = r_multiple(direction, entry, stop, stop)
                sb("PATCH", "setups", {"status": "stopped", "closed_at": c.t,
                                       "outcome_price": stop, "outcome_r": r}, f"id=eq.{setup['id']}")
                log_event(setup["id"], "triggered", "stopped", stop, "stop hit")
                return "stopped"
            hit = None
            for i, tp in enumerate(tps, start=1):
                if (direction == "long" and c.h >= tp) or (direction == "short" and c.l <= tp):
                    hit = (i, tp)
            if hit:
                idx, tp = hit
                new = f"tp{idx}_hit"
                r = r_multiple(direction, entry, stop, tp)
                sb("PATCH", "setups", {"status": new, "outcome_price": tp, "outcome_r": r,
                                       **({"closed_at": c.t} if idx == len(tps) else {})},
                   f"id=eq.{setup['id']}")
                log_event(setup["id"], "triggered", new, tp, f"target {idx} reached")
                if idx == len(tps):
                    return new
                status = new
        return status

    return status


def evaluate_all(interval: int | None = None):
    while True:
        try:
            rows = sb("GET", "setups",
                      query=f"status=in.({','.join(OPEN_STATES)})&select=*&limit=200")
        except Exception as e:  # noqa: BLE001
            print("store unavailable:", e)
            rows = []
        moved = 0
        cache: dict[tuple[str, str], list] = {}
        for s in rows:
            tf = s.get("timeframe") or "1h"
            key = (s.get("symbol", "XAUUSD"), tf)
            if key not in cache:
                try:
                    cache[key] = fetch_candles(key[0], tf, 300, ttl=45)
                except Exception:  # noqa: BLE001
                    cache[key] = []
            if not cache[key]:
                continue
            before = s["status"]
            after = evaluate_one(s, cache[key])
            if after != before:
                moved += 1
                print(f"  {s['id'][:8]} {before} -> {after}")
        print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] "
              f"evaluated {len(rows)} open, {moved} moved")
        if not interval:
            return
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0, help="seconds between passes")
    a = ap.parse_args()
    evaluate_all(a.loop or None)
