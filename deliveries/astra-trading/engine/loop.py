"""Astra Trading — the live loop.

The agent proposes setups and the evaluator scores them. Both already exist and
work; nothing ran them, so every setup sat at `proposed` forever and the public
track record stayed empty. This module is the missing heartbeat:

    scan  (agent)  →  score  (evaluator)  →  repeat

It is deliberately a single process so the two halves can never drift out of
step, and it writes a heartbeat file the self-heal probe can check.

Run once:    python3 loop.py
Run live:    python3 loop.py --interval 300
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import agent as AG  # noqa: E402
import evaluator as EV  # noqa: E402

HEARTBEAT = Path("/tmp/astra-loop-heartbeat.json")


def write_heartbeat(scan: dict, moved: int, ok: bool) -> None:
    HEARTBEAT.write_text(json.dumps({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": ok,
        "submitted": bool(scan.get("submitted")),
        "setups_moved": moved,
    }, indent=2))


def cycle(verbose: bool = True) -> dict:
    """One scan + one scoring pass. Never raises: a bad cycle must not kill the loop."""
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        scan = AG.scan_once(verbose=False)
    except Exception as e:  # noqa: BLE001
        scan = {"error": str(e)[:200], "submitted": None}
    try:
        moved = EV.evaluate_all(interval=None) or 0
    except Exception as e:  # noqa: BLE001
        moved = -1
        if verbose:
            print(f"  evaluator error: {str(e)[:160]}")
    ok = "error" not in scan
    write_heartbeat(scan, moved if moved >= 0 else 0, ok)
    if verbose:
        sub = scan.get("submitted")
        line = (f"{sub['direction']} {sub['entry']} ({sub['tf']})"
                if sub else "no qualifying setup")
        print(f"[{started}] scan: {line} | setups moved: {moved}")
    return {"at": started, "scan": scan, "moved": moved, "ok": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=0,
                    help="seconds between cycles; 0 = run once")
    a = ap.parse_args()
    if a.interval:
        while True:
            cycle()
            time.sleep(a.interval)
    else:
        print(json.dumps(cycle(), indent=2, default=str)[:1200])


if __name__ == "__main__":
    main()
