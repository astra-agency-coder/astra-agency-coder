#!/usr/bin/env python3
"""Evaluator tests — prove the lifecycle actually moves, on real data.

Creates throwaway setups in Supabase, runs one evaluation pass, checks the
resulting state, then deletes everything it created.

Run: python3 test_evaluator.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import evaluator as E  # noqa: E402
from market import fetch_candles  # noqa: E402

PASS, FAIL, FAILURES = 0, 0, []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}  {detail}")


print("== r_multiple ==")
check("long win at 2R", E.r_multiple("long", 100, 90, 120) == 2.0)
check("long loss at -1R", E.r_multiple("long", 100, 90, 90) == -1.0)
check("short win at 3R", E.r_multiple("short", 100, 110, 70) == 3.0)
check("short loss at -1R", E.r_multiple("short", 100, 110, 110) == -1.0)
check("zero risk does not divide by zero", E.r_multiple("long", 100, 100, 150) == 0.0)

print("== live lifecycle ==")
candles = fetch_candles("XAUUSD", "1h", 120, ttl=0)
price = candles[0].c
newest_high = candles[0].h
print(f"   live XAUUSD price {price} (newest bar high {newest_high})")

created_ids: list[str] = []

# A short whose entry sits just inside the live bar's range: it must trigger.
entry1 = round((price + newest_high) / 2, 2)
s1 = {
    "symbol": "XAUUSD", "direction": "short", "entry_type": "limit",
    "entry": entry1, "stop_loss": round(entry1 + 70, 2),
    "tp1": round(price - 30, 2), "tp2": round(price - 100, 2), "tp3": None,
    "timeframe": "1h", "status": "proposed", "confidence": 0.5, "factors": [],
    "idempotency_key": f"eval-test-{uuid.uuid4().hex[:10]}",
}
# A long whose entry is far below: it must NOT trigger.
s2 = dict(s1, direction="long", entry=round(price - 400, 2),
          stop_loss=round(price - 500, 2), tp1=round(price - 300, 2),
          tp2=round(price - 200, 2),
          idempotency_key=f"eval-test-{uuid.uuid4().hex[:10]}")

for s in (s1, s2):
    row = E.sb("POST", "setups", s)
    created_ids.append(row[0]["id"])
    E.log_event(row[0]["id"], None, "proposed", s["entry"], "test")

try:
    rows = E.sb("GET", "setups",
                query=f"id=in.({','.join(created_ids)})&select=*")
    by_id = {r["id"]: r for r in rows}
    # s1 entry is 50 above price → within the newest candle's range → triggers
    after1 = E.evaluate_one(by_id[created_ids[0]], candles)
    check("short with entry above price triggers", after1 == "triggered", f"got {after1}")
    # s2 entry is 400 below price → untouched → stays proposed
    after2 = E.evaluate_one(by_id[created_ids[1]], candles)
    check("far long stays proposed", after2 == "proposed", f"got {after2}")

    events = E.sb("GET", "setup_events",
                  query=f"setup_id=eq.{created_ids[0]}&select=to_status,reason&order=at")
    states = [e["to_status"] for e in events]
    check("lifecycle events were written", "proposed" in states and "triggered" in states, f"{states}")
    check("triggered event carries a reason",
          any(e["to_status"] == "triggered" and e["reason"] for e in events), f"{events}")

    persisted = E.sb("GET", "setups", query=f"id=eq.{created_ids[0]}&select=status,triggered_at")
    check("triggered state persisted to the store",
          persisted and persisted[0]["status"] == "triggered", f"{persisted}")
finally:
    for sid in created_ids:
        try:
            E.sb("DELETE", "setups", query=f"id=eq.{sid}")
        except Exception as e:  # noqa: BLE001
            print("   cleanup failed for", sid[:8], e)

print(f"\nRESULT {PASS}/{PASS+FAIL} passed" + (f"  FAILURES={FAILURES}" if FAILURES else ""))
sys.exit(1 if FAIL else 0)
