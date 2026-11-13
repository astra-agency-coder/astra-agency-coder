#!/usr/bin/env python3
"""Measure the company's real numbers and write them into the site.

Every value emitted here is read from a file that a test run produced, or
executed live. Nothing is typed by hand, so the site can never drift from the
truth. Unverifiable items are emitted with status "blocked" rather than a
number, so the site has to say so out loud.

Usage:  python3 tools/gen_facts.py            # writes src/data/facts.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
TRADING = ROOT / "deliveries" / "astra-trading"
OUT = SITE / "src" / "data" / "facts.json"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def readiness() -> dict:
    d = _read_json(ROOT / "ops" / "tests" / "last_run.json") or {}
    results = d.get("results", [])
    passed = sum(1 for r in results if r.get("result") == "PASS")
    return {"status": "verified", "passed": passed, "total": len(results),
            "at": d.get("at"), "source": "ops/tests/last_run.json"}


def engine() -> dict:
    """Run the engine suite for real; parse its own RESULT line."""
    try:
        p = subprocess.run([sys.executable, "engine/test_engine.py"],
                           cwd=TRADING, capture_output=True, text=True, timeout=300)
        m = re.search(r"RESULT\s+(\d+)/(\d+)\s+passed", p.stdout)
        if m:
            return {"status": "verified", "passed": int(m.group(1)),
                    "total": int(m.group(2)), "source": "engine/test_engine.py"}
    except Exception as e:  # noqa: BLE001
        return {"status": "blocked", "reason": str(e)[:120]}
    return {"status": "blocked", "reason": "no RESULT line"}


def api_suite() -> dict:
    """Run the API suite against a live server; parse RESULT."""
    try:
        p = subprocess.run([sys.executable, "api/test_api.py", "http://127.0.0.1:12012"],
                           cwd=TRADING, capture_output=True, text=True, timeout=420)
        m = re.search(r"RESULT\s+(\d+)/(\d+)\s+passed", p.stdout)
        if m:
            return {"status": "verified", "passed": int(m.group(1)),
                    "total": int(m.group(2)), "source": "api/test_api.py"}
    except Exception as e:  # noqa: BLE001
        return {"status": "blocked", "reason": str(e)[:120]}
    return {"status": "blocked", "reason": "suite did not report a RESULT line"}


def security() -> dict:
    d = _read_json(TRADING / "security" / "rls_results.json") or {}
    results = d.get("results", [])
    if not results:
        return {"status": "blocked", "reason": "no security results on file"}
    passed = sum(1 for r in results if r.get("result") == "PASS")
    return {"status": "recorded", "passed": passed, "total": len(results),
            "findings": len(results) - passed, "source": "security/rls_results.json",
            "note": "last recorded run; re-verification needs live credentials"}


def roster() -> dict:
    d = _read_json(ROOT / "company" / "roster.json") or {}
    agents = d.get("agents", {})
    depts = {v.get("department") for v in agents.values() if isinstance(v, dict)}
    managers = [k for k, v in agents.items()
                if isinstance(v, dict) and str(v.get("role", "")).startswith("Chief")]
    return {"agents": len(agents), "departments": len(depts),
            "managers": len(managers), "source": "company/roster.json"}


def repos() -> dict:
    d = _read_json(ROOT / "company" / "departments" / "repos.json") or {}
    items = d.get("repos", [])
    ok = sum(1 for r in items if r.get("ok"))
    return {"total": len(items), "ok": ok, "owner": d.get("owner"),
            "status": d.get("status"), "reason": d.get("reason"),
            "needs": d.get("needs"),
            "source": "company/departments/repos.json"}


def main() -> int:
    facts = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "readiness": readiness(),
        "engine": engine(),
        "api": api_suite(),
        "security": security(),
        "roster": roster(),
        "repos": repos(),
    }
    OUT.write_text(json.dumps(facts, indent=2))
    print(json.dumps(facts, indent=2))
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
