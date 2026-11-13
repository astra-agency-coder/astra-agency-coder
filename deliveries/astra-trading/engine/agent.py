"""Astra Trading — the analysis agent.

This is the "AI that watches gold and proposes setups". It runs on a schedule:

  1. pull candles for several timeframes
  2. look for a setup that meets the bar (structure + zone + liquidity + session)
  3. if nothing qualifies, send NOTHING (that is the correct, disciplined outcome)
  4. otherwise submit it to the API, which validates and stores it unpublished
     (shadow mode) until its record earns publication

Tools available to the agent (each is a plain function, testable in isolation):
  fetch_candles · find_levels · find_liquidity · volatility · session_context
  build_setup · submit_setup · wait_for_opportunity

Run once:   python3 agent.py
Loop:       python3 agent.py --loop 300
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import analysis as A  # noqa: E402
from market import fetch_candles  # noqa: E402

API_BASE = os.environ.get("ASTRA_API_BASE", "http://127.0.0.1:8100")
TIMEFRAMES = ("1h", "4h", "15m")


def _sec():
    p = ROOT.parents[1] / "ops" / "secrets.py"
    spec = importlib.util.spec_from_file_location("astra_secrets", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SEC = _sec()
AGENT_NAME = "astra-analysis"


def agent_key() -> str | None:
    """The write-only key this agent uses against the API."""
    key = SEC.resolve("ASTRA_AGENT_KEY")
    if key:
        return key
    return os.environ.get("ASTRA_AGENT_KEY")


# --------------------------------------------------------------------------- #
# tools
# --------------------------------------------------------------------------- #
def tool_fetch_candles(symbol: str, tf: str, n: int = 300):
    return fetch_candles(symbol, tf, n)


def tool_find_levels(candles):
    return A.find_zones(candles, A.atr(candles))


def tool_find_liquidity(candles):
    return A.find_liquidity(candles, A.atr(candles))


def tool_volatility(candles):
    return A.atr(candles)


def tool_session_context():
    return A.session_context()


def tool_build_setup(candles, tf):
    return A.build_setup(candles, tf)


def tool_wait_for_opportunity():
    """Explicitly do nothing. A missing setup is a valid, expected result."""
    return {"submitted": False, "reason": "no setup met the quality bar"}


def tool_submit_setup(setup: dict) -> dict:
    key = agent_key()
    if not key:
        return {"ok": False, "error": "no agent key configured (ASTRA_AGENT_KEY)"}
    payload = dict(setup)
    payload["idempotency_key"] = payload.get("idempotency_key") or f"{AGENT_NAME}-{uuid.uuid4().hex}"
    payload["source_agent"] = AGENT_NAME
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/setups", method="POST",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-Agent-Key": key,
                 "X-Idempotency-Key": payload["idempotency_key"]},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"ok": True, "status": r.status, "body": json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode()[:300]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# --------------------------------------------------------------------------- #
# the agent loop
# --------------------------------------------------------------------------- #
def scan_once(verbose: bool = True) -> dict:
    """One pass over the timeframes. Returns a small report."""
    report = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "considered": [], "submitted": None}
    best = None
    for tf in TIMEFRAMES:
        try:
            candles = tool_fetch_candles("XAUUSD", tf, 300)
        except Exception as e:  # noqa: BLE001
            report["considered"].append({"tf": tf, "error": str(e)[:120]})
            continue
        s = tool_build_setup(candles, tf)
        report["considered"].append({
            "tf": tf, "price": round(candles[0].c, 2),
            "atr": round(tool_volatility(candles), 2),
            "setup": bool(s), "confidence": s.confidence if s else None,
        })
        if s and (best is None or s.confidence > best.confidence):
            best = s
    if best is None:
        report.update(tool_wait_for_opportunity())
    else:
        payload = {
            "symbol": best.symbol, "direction": best.direction, "entry_type": best.entry_type,
            "entry": best.entry, "stop_loss": best.stop_loss,
            "tp1": best.tp1, "tp2": best.tp2, "tp3": best.tp3,
            "timeframe": best.timeframe, "session": best.session,
            "confidence": best.confidence, "factors": best.factors,
            "invalidation": best.invalidation,
            "rationale_en": best.rationale,
        }
        res = tool_submit_setup(payload)
        report["submitted"] = {"tf": best.timeframe, "direction": best.direction,
                               "entry": best.entry, "confidence": best.confidence,
                               "result": res}
        if verbose:
            print(f"  submitted {best.direction} {best.entry} ({best.timeframe}) -> {res}")
    if verbose:
        for c in report["considered"]:
            print(f"   {c.get('tf')}: " + (c.get("error") or
                  f"price {c['price']} atr {c['atr']} setup={c['setup']} conf={c['confidence']}"))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0, help="seconds between scans")
    a = ap.parse_args()
    if a.loop:
        while True:
            scan_once()
            time.sleep(a.loop)
    else:
        r = scan_once()
        print(json.dumps({k: v for k, v in r.items() if k != "considered"}, indent=2)[:800])


if __name__ == "__main__":
    main()
