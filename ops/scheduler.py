#!/usr/bin/env python3
"""Scheduler — recurring company duties.

OpenHands Cloud runtimes are ephemeral and recycle when idle. Durable scheduling
must therefore run on OpenHands Cloud automations (a cron-triggered conversation),
not as a long-lived process in this container. This module defines the duty
schedule and provides a single entrypoint that a scheduled conversation runs.

    python3 ops/scheduler.py duties     # list the schedule
    python3 ops/scheduler.py run <duty> # execute one duty now

OpenHands Cloud automation should invoke: `python3 ops/scheduler.py run <duty>`
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DUTIES = [
    {"name": "health", "cron": "*/30 * * * *",
     "cmd": ["python3", "ops/heal.py"],
     "desc": "self-heal: probe components and repair bounded failures"},
    {"name": "board", "cron": "0 */6 * * *",
     "cmd": ["python3", "ops/report.py", "board", "--write"],
     "desc": "refresh the internal status board"},
    {"name": "owner_report", "cron": "0 9 * * *",
     "cmd": ["python3", "ops/report.py", "owner", "--write"],
     "desc": "generate the daily Owner report"},
    {"name": "secret_scan", "cron": "0 3 * * *",
     "cmd": ["python3", "ops/astra.py", "scan-secrets"],
     "desc": "scan tracked files for secret patterns"},
    {"name": "trading_loop", "cron": "*/10 * * * *",
     "cmd": ["python3", "ops/astra.py", "ensure-trading-loop"],
     "desc": "ensure the Astra Trading scan+score loop is alive (idempotent)"},
]


def run(duty: str) -> int:
    for d in DUTIES:
        if d["name"] == duty:
            print(f"[scheduler] running duty '{duty}': {d['desc']}")
            return subprocess.call(d["cmd"], cwd=str(ROOT))
    print(f"[scheduler] unknown duty: {duty}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "duties":
        print(json.dumps(DUTIES, indent=2))
    elif len(sys.argv) >= 3 and sys.argv[1] == "run":
        sys.exit(run(sys.argv[2]))
    else:
        print(__doc__)
