#!/usr/bin/env python3
"""End-to-end API tests against a running Astra Trading API.

Usage: python3 test_api.py [base_url]      (default http://127.0.0.1:8100)

Covers the paths that matter: health, market data, the write-only agent
ingestion contract (auth, validation, idempotency, caps) and payments.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import secrets as pysecrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8100"
ROOT = Path(__file__).resolve().parents[1]


def _sec():
    p = ROOT.parents[1] / "ops" / "secrets.py"
    spec = importlib.util.spec_from_file_location("astra_secrets", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SEC = _sec()
SB_URL = SEC.resolve("ASTRA_SUPABASE_URL")
SB_SECRET = SEC.resolve("ASTRA_SUPABASE_SECRET_KEY")

PASS, FAIL, FAILURES = 0, 0, []


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}  {detail}")


def call(method: str, path: str, body=None, headers=None, timeout=30):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw or "{}")
            except json.JSONDecodeError:
                return r.status, {"raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}
    except Exception as e:  # noqa: BLE001
        return "ERR", {"err": str(e)}


def sb(method: str, table: str, body=None, query: str = ""):
    url = f"{SB_URL}/rest/v1/{table}" + (f"?{query}" if query else "")
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"apikey": SB_SECRET, "Authorization": f"Bearer {SB_SECRET}",
                                          "Content-Type": "application/json",
                                          "Prefer": "return=representation"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw.strip() else []


# --------------------------------------------------------------------------- #
print("== health ==")
st, b = call("GET", "/healthz")
check("healthz 200", st == 200, f"{st} {b}")
st, b = call("GET", "/api/version")
check("version names the service", st == 200 and "Astra" in json.dumps(b), f"{st}")

print("== market ==")
st, b = call("GET", "/api/quote")
check("quote returns a live mid", st == 200 and isinstance(b.get("mid"), (int, float)), f"{st} {b}")
st, b = call("GET", "/api/analysis?tf=1h&count=120")
check("analysis returns candles", st == 200 and len(b.get("candles", [])) > 50, f"{st}")
check("analysis has zones", st == 200 and "zones" in b)
check("analysis has bias", st == 200 and "direction" in b.get("bias", {}))
check("bad timeframe rejected", call("GET", "/api/analysis?tf=99x")[0] == 400)

print("== agent ingestion: auth ==")
st, b = call("POST", "/api/v1/setups", {"direction": "long"})
check("no key -> 401", st == 401, f"{st} {b}")
st, b = call("POST", "/api/v1/setups", {"direction": "long"}, {"X-Agent-Key": "not-a-real-key"})
check("bad key -> 401", st == 401, f"{st} {b}")

# mint a real agent key
raw_key = "astra_test_" + pysecrets.token_urlsafe(24)
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
try:
    sb("POST", "agent_keys", {"name": "api-test", "key_hash": key_hash, "scopes": ["setups:write"]})
    minted = True
except Exception as e:  # noqa: BLE001
    minted = False
    print("   (could not mint key:", str(e)[:120], ")")
check("agent key minted", minted)

AH = {"X-Agent-Key": raw_key}

print("== agent ingestion: validation ==")
st, b = call("POST", "/api/v1/setups", {
    "direction": "long", "entry": 3000, "stop_loss": 3010, "tp1": 3030, "tp2": 3060,
    "idempotency_key": "geom-test-1"}, AH)
check("long with stop above entry rejected", st == 422, f"{st} {b}")

st, b = call("POST", "/api/v1/setups", {
    "direction": "short", "entry": 3000, "stop_loss": 2990, "tp1": 2970,
    "idempotency_key": "geom-test-2"}, AH)
check("short with stop below entry rejected", st == 422, f"{st} {b}")

st, b = call("POST", "/api/v1/setups", {
    "direction": "long", "entry": 3000, "stop_loss": 2999, "tp1": 3000.5,
    "idempotency_key": "rr-test-3"}, AH)
check("R:R below 1.0 rejected", st == 422, f"{st} {b}")

st, b = call("POST", "/api/v1/setups", {
    "direction": "long", "entry": 3000, "stop_loss": 2990, "tp1": 3030,
    "idempotency_key": "mismatch-test-1"}, {**AH, "X-Idempotency-Key": "k-DIFFERENT"})
check("header/body idempotency mismatch rejected", st == 400, f"{st} {b}")

print("== agent ingestion: happy path + idempotency ==")
good = {"symbol": "XAUUSD", "direction": "short", "entry": 3000, "stop_loss": 3010,
        "tp1": 2985, "tp2": 2970, "tp3": 2955, "timeframe": "1h", "confidence": 0.7,
        "factors": ["test"], "idempotency_key": "happy-path-1"}
st, b = call("POST", "/api/v1/setups", good, AH)
ok1 = st == 201 and b.get("id")
check("valid setup accepted (201)", bool(ok1), f"{st} {b}")
check("new setup starts unpublished (shadow mode)", b.get("published") is False, f"{b}")
check("R:R computed", b.get("risk_reward") == 3.0, f"{b}")

st2, b2 = call("POST", "/api/v1/setups", good, AH)
check("replay returns 200, same id", st2 == 200 and b2.get("id") == b.get("id") and b2.get("replay"),
      f"{st2} {b2}")

print("== agent ingestion: open-setup cap ==")
created = []
for i in range(4):
    st, bb = call("POST", "/api/v1/setups", {
        "direction": "short", "entry": 3000 + i, "stop_loss": 3010 + i,
        "tp1": 2980 + i, "tp2": 2960 + i, "idempotency_key": f"cap-test-{i}"}, AH)
    created.append(st)
check("cap enforced (409 once MAX_OPEN reached)", 409 in created, f"statuses={created}")

print("== lifecycle ==")
if ok1:
    st, b = call("POST", f"/api/v1/setups/{b['id']}/cancel", {}, AH)
    check("cancel works", st == 200 and b.get("status") == "cancelled", f"{st} {b}")

print("== payments ==")
st, b = call("GET", "/api/v1/payments/wallet")
check("wallet endpoint answers", st == 200 and "network" in b, f"{st} {b}")
st, b = call("POST", "/api/v1/payments/verify", {"tx_hash": "0" * 64})
check("fake tx hash is NOT verified", b.get("verified") is False, f"{st} {b}")

print("== track record ==")
st, b = call("GET", "/api/track-record")
check("track record endpoint answers", st == 200, f"{st} {b}")

# cleanup
try:
    sb("DELETE", "setups", query="idempotency_key=like.*test*")
    sb("DELETE", "setups", query="idempotency_key=like.happy-path*")
    sb("DELETE", "agent_keys", query=f"key_hash=eq.{key_hash}")
except Exception:
    pass

print(f"\nRESULT {PASS}/{PASS+FAIL} passed" + (f"  FAILURES={FAILURES}" if FAILURES else ""))
sys.exit(1 if FAIL else 0)
