"""Astra Trading API — FastAPI service.

Responsibilities
  * serve market analysis to the web app and the Android apps
  * accept AI-proposed setups from the analysis agent (write-only, keyed)
  * verify on-chain USDT (TRC20) payments
  * keep the setup lifecycle honest (state machine + immutable event log)

Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import analysis as A  # noqa: E402


def _load_astra_secrets():
    """Load ops/secrets.py under a private name.

    `secrets` is a stdlib module that uvicorn already imports, so a plain
    `import secrets` here would silently bind to the stdlib one.
    """
    import importlib.util

    path = ROOT.parents[1] / "ops" / "secrets.py"
    spec = importlib.util.spec_from_file_location("astra_secrets", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SEC = _load_astra_secrets()

SUPABASE_URL = os.environ.get("ASTRA_SUPABASE_URL") or (SEC.resolve("ASTRA_SUPABASE_URL") or "")
SUPABASE_ANON = os.environ.get("ASTRA_SUPABASE_ANON_KEY") or (SEC.resolve("ASTRA_SUPABASE_ANON_KEY") or "")
SUPABASE_SECRET = os.environ.get("ASTRA_SUPABASE_SECRET_KEY") or (SEC.resolve("ASTRA_SUPABASE_SECRET_KEY") or "")
WALLET_TRC20 = SEC.resolve("ASTRA_WALLET_USDT_TRC20") or ""
TRIAL_DAYS = int(os.environ.get("ASTRA_TRIAL_DAYS", "7"))
MAX_OPEN_SETUPS = int(os.environ.get("ASTRA_MAX_OPEN_SETUPS", "3"))

# --------------------------------------------------------------------------- #
# Supabase helpers (REST; no extra SDK dependency)
# --------------------------------------------------------------------------- #
def sb_headers(secret: bool = False, extra: dict | None = None) -> dict:
    key = SUPABASE_SECRET if secret else SUPABASE_ANON
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def sb_get(table: str, query: str = "", secret: bool = True) -> Any:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if query:
        url += "?" + query
    req = urllib.request.Request(url, headers=sb_headers(secret))
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else []


def sb_post(table: str, rows: Any, secret: bool = True, on_conflict: str = "") -> Any:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if on_conflict:
        url += f"?on_conflict={on_conflict}"
    h = sb_headers(secret, {"Prefer": "return=representation,resolution=merge-duplicates"})
    req = urllib.request.Request(url, data=json.dumps(rows).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else []


def sb_patch(table: str, query: str, patch: dict, secret: bool = True) -> Any:
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    h = sb_headers(secret, {"Prefer": "return=representation"})
    req = urllib.request.Request(url, data=json.dumps(patch).encode(), headers=h, method="PATCH")
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else []


def sb_rpc(fn: str, args: dict) -> Any:
    url = f"{SUPABASE_URL}/rest/v1/rpc/{fn}"
    h = sb_headers(True)
    req = urllib.request.Request(url, data=json.dumps(args).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else None


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #
class SetupIn(BaseModel):
    symbol: str = "XAUUSD"
    direction: str
    entry_type: str = "limit"
    entry: float = Field(gt=0, lt=1e7)
    stop_loss: float = Field(gt=0, lt=1e7)
    tp1: float | None = Field(default=None, gt=0, lt=1e7)
    tp2: float | None = Field(default=None, gt=0, lt=1e7)
    tp3: float | None = Field(default=None, gt=0, lt=1e7)
    timeframe: str = "1h"
    session: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    rationale_ar: str | None = None
    rationale_en: str | None = None
    rationale_tr: str | None = None
    factors: list[str] = Field(default_factory=list)
    validity_hours: int = Field(default=24, ge=1, le=168)
    invalidation: str | None = None
    source_agent: str = "astra-analysis"
    idempotency_key: str = Field(min_length=8, max_length=128)

    @field_validator("direction")
    @classmethod
    def _dir(cls, v: str) -> str:
        if v not in ("long", "short"):
            raise ValueError("direction must be long or short")
        return v

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, v: str) -> str:
        if v not in ("1m", "5m", "15m", "30m", "1h", "4h", "1d"):
            raise ValueError("unsupported timeframe")
        return v

    def validate_geometry(self) -> list[str]:
        errs: list[str] = []
        if self.direction == "long" and self.stop_loss >= self.entry:
            errs.append("long stop_loss must be below entry")
        if self.direction == "short" and self.stop_loss <= self.entry:
            errs.append("short stop_loss must be above entry")
        for name, tp in (("tp1", self.tp1), ("tp2", self.tp2), ("tp3", self.tp3)):
            if tp is None:
                continue
            if self.direction == "long" and tp <= self.entry:
                errs.append(f"long {name} must be above entry")
            if self.direction == "short" and tp >= self.entry:
                errs.append(f"short {name} must be below entry")
        risk = abs(self.entry - self.stop_loss)
        if risk <= 0:
            errs.append("entry and stop_loss cannot be equal")
        return errs

    def risk_reward(self) -> float:
        risk = abs(self.entry - self.stop_loss)
        tp = self.tp2 or self.tp1 or self.tp3
        if not risk or tp is None:
            return 0.0
        return round(abs(tp - self.entry) / risk, 2)


class PaymentIn(BaseModel):
    tx_hash: str = Field(min_length=20, max_length=120)
    plan: str = "pro_monthly"


class ContactIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    locale: str = "ar"


# --------------------------------------------------------------------------- #
# app
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started = datetime.now(timezone.utc)
    app.state.rate = {}
    yield


app = FastAPI(title="Astra Trading API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

AGENT_PATHS = ("/api/v1/setups",)


@app.middleware("http")
async def agent_auth_gate(request: Request, call_next):
    """Authenticate the agent BEFORE the body is parsed.

    Returning 401 here keeps an unauthenticated caller from learning anything
    about the payload schema from validation errors.
    """
    if request.method in ("POST", "PATCH", "DELETE") and request.url.path.startswith(AGENT_PATHS):
        if request.url.path.endswith("/cancel"):
            pass
        key = request.headers.get("x-agent-key")
        if not key:
            return JSONResponse({"detail": "missing agent key"}, status_code=401)
        try:
            require_agent_key(key)
        except HTTPException as e:
            return JSONResponse({"detail": e.detail}, status_code=e.status_code)
    return await call_next(request)


def rate_limit(key: str, limit: int, window: int = 60) -> None:
    now = time.time()
    bucket = app.state.rate.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        raise HTTPException(429, "rate limit exceeded")
    bucket.append(now)


def require_agent_key(x_agent_key: str | None) -> str:
    if not x_agent_key:
        raise HTTPException(401, "missing agent key")
    h = hashlib.sha256(x_agent_key.encode()).hexdigest()
    try:
        rows = sb_get("agent_keys", f"key_hash=eq.{h}&revoked_at=is.null&select=id,name,scopes", secret=True)
    except Exception:
        raise HTTPException(503, "key store unavailable")
    if not rows:
        raise HTTPException(401, "invalid agent key")
    try:
        sb_patch("agent_keys", f"id=eq.{rows[0]['id']}", {"last_used_at": datetime.now(timezone.utc).isoformat()})
    except Exception:
        pass
    return rows[0]["name"]


# ---------------------------- health --------------------------------------- #
@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/api/version")
def version():
    return {"name": "Astra Trading API", "version": app.version,
            "started": app.state.started.isoformat()}


# ---------------------------- market data ---------------------------------- #
@app.get("/api/analysis")
def get_analysis(tf: str = Query("1h"), symbol: str = Query("XAUUSD"), count: int = Query(300, ge=60, le=1000)):
    rate_limit("analysis", 120)
    if tf not in ("1m", "5m", "15m", "30m", "1h", "4h", "1d"):
        raise HTTPException(400, "unsupported timeframe")
    try:
        payload = A.analyse(symbol, tf, count)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"analysis unavailable: {e}")
    # the deck reads bid/ask + provenance from the same payload
    try:
        from market import fetch_tick
        t = fetch_tick(symbol)
        payload["tick"] = {"bid": t.get("bid"), "ask": t.get("ask"),
                           "mid": t.get("mid"), "spread": t.get("spread"),
                           "source": t.get("source"), "ts": t.get("timestamp")}
        payload["source"] = "live"
    except Exception:  # noqa: BLE001
        payload["tick"] = None
        payload["source"] = "engine"
    return payload


@app.get("/api/quote")
def get_quote(symbol: str = Query("XAUUSD")):
    rate_limit("quote", 240)
    from market import fetch_tick
    try:
        t = fetch_tick(symbol)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"quote unavailable: {e}")
    return {"symbol": t.get("symbol"), "bid": t.get("bid"), "ask": t.get("ask"),
            "mid": t.get("mid"), "spread": t.get("spread"),
            "high": t.get("high"), "low": t.get("low"),
            "direction": t.get("direction"), "dayDiffPercent": t.get("dayDiffPercent"),
            "marketState": t.get("marketState"), "quoteAgeSeconds": t.get("quoteAgeSeconds"),
            "source": t.get("source"), "timestamp": t.get("timestamp")}


@app.get("/api/track-record")
def track_record():
    rate_limit("tr", 120)
    try:
        rows = sb_get("track_record", "select=*", secret=True)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"track record unavailable: {e}")
    return rows[0] if rows else {"wins": 0, "losses": 0, "breakevens": 0, "open": 0, "total": 0, "avg_r": None}


# ---------------------------- setups -------------------------------------- #
@app.get("/api/setups")
def list_setups(status: str = Query(""), limit: int = Query(50, ge=1, le=200)):
    rate_limit("setups_list", 120)
    q = f"published=eq.true&select=*&order=created_at.desc&limit={limit}"
    if status:
        q = f"status=eq.{status}&" + q
    try:
        return sb_get("setups", q, secret=True)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"setups unavailable: {e}")


@app.post("/api/v1/setups", status_code=201)
def create_setup(body: SetupIn, x_agent_key: str | None = Header(default=None),
                 x_idempotency_key: str | None = Header(default=None)):
    agent = require_agent_key(x_agent_key)
    rate_limit(f"agent:{agent}", 30)
    if x_idempotency_key and x_idempotency_key != body.idempotency_key:
        raise HTTPException(400, "idempotency key mismatch between header and body")

    errs = body.validate_geometry()
    if errs:
        raise HTTPException(422, "; ".join(errs))
    rr = body.risk_reward()
    if rr < 1.0:
        raise HTTPException(422, f"risk/reward {rr} below the 1.0 minimum")

    # idempotent replay
    try:
        existing = sb_get("setups", f"idempotency_key=eq.{body.idempotency_key}&select=id,status", secret=True)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"store unavailable: {e}")
    if existing:
        return JSONResponse({"id": existing[0]["id"], "status": existing[0]["status"],
                             "replay": True}, status_code=200)

    # cap concurrently open proposals
    try:
        open_rows = sb_get("setups", "status=in.(proposed,triggered)&select=id", secret=True)
    except Exception:
        open_rows = []
    if len(open_rows) >= MAX_OPEN_SETUPS:
        raise HTTPException(409, f"{len(open_rows)} setups already open; cap is {MAX_OPEN_SETUPS}")

    row = body.model_dump()
    row.pop("validity_hours", None)
    row.update({
        "risk_reward": rr,
        "status": "proposed",
        "validity_until": (datetime.now(timezone.utc) + timedelta(hours=body.validity_hours)).isoformat(),
        "published": False,          # shadow mode: not shown to users until promoted
    })
    try:
        created = sb_post("setups", row, secret=True)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        raise HTTPException(422, f"rejected by store: {detail}")
    sid = created[0]["id"] if created else None
    try:
        sb_post("setup_events", {"setup_id": sid, "to_status": "proposed",
                                 "price": body.entry, "reason": f"created by {agent}"}, secret=True)
    except Exception:
        pass
    return {"id": sid, "status": "proposed", "risk_reward": rr, "published": False, "replay": False}


@app.post("/api/v1/setups/{setup_id}/cancel")
def cancel_setup(setup_id: str, x_agent_key: str | None = Header(default=None)):
    agent = require_agent_key(x_agent_key)
    try:
        sb_patch("setups", f"id=eq.{setup_id}", {"status": "cancelled"}, secret=True)
        sb_post("setup_events", {"setup_id": setup_id, "from_status": "proposed",
                                 "to_status": "cancelled", "reason": f"cancelled by {agent}"}, secret=True)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"cancel failed: {e}")
    return {"id": setup_id, "status": "cancelled"}


# ---------------------------- payments ------------------------------------ #
TRON_API = "https://api.trongrid.io"


def verify_trc20(tx_hash: str, to_address: str, min_amount: float = 0.0) -> dict:
    """Verify a USDT TRC20 transfer on-chain via TronGrid (public, no key needed)."""
    req = urllib.request.Request(f"{TRON_API}/v1/transactions/{tx_hash}",
                                 headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"ok": False, "reason": "transaction not found on chain"}
        raise
    if not data or not data.get("data"):
        return {"ok": False, "reason": "transaction not found"}
    tx = data["data"][0]
    if not tx.get("ret") or tx["ret"][0].get("contractRet") != "SUCCESS":
        return {"ok": False, "reason": "transaction not successful"}
    contract = (tx.get("raw_data", {}).get("contract") or [{}])[0]
    if contract.get("type") != "TransferContract":
        # TRC20 transfers arrive as TriggerSmartContract
        if contract.get("type") != "TriggerSmartContract":
            return {"ok": False, "reason": f"unsupported contract {contract.get('type')}"}
    return {"ok": True, "raw": tx}


@app.post("/api/v1/payments/verify")
def verify_payment(body: PaymentIn):
    rate_limit("pay_verify", 30)
    if not WALLET_TRC20:
        raise HTTPException(503, "collection wallet not configured")
    try:
        res = verify_trc20(body.tx_hash, WALLET_TRC20)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"chain lookup failed: {e}")
    if not res["ok"]:
        # record the attempt, never as confirmed
        try:
            sb_post("payments", {"provider": "usdt_trc20", "network": "TRON", "tx_hash": body.tx_hash,
                                 "to_address": WALLET_TRC20, "status": "pending",
                                 "raw": {"reason": res["reason"]}}, secret=True, on_conflict="provider,tx_hash")
        except Exception:
            pass
        return {"verified": False, "reason": res["reason"]}
    return {"verified": True, "reason": "found on chain", "note": "manual confirmation required before crediting"}


@app.get("/api/v1/payments/wallet")
def wallet_info():
    return {"network": "TRON (TRC20)", "currency": "USDT",
            "address": WALLET_TRC20 or None, "configured": bool(WALLET_TRC20)}


# ---------------------------- entitlements ------------------------------- #
# Trial and subscription state is a server fact keyed by an anonymous device
# token, not browser localStorage. The client sends the token it was issued in
# the `X-Device-Token` header; the server hashes it and resolves the entitlement.
import hashlib as _hashlib  # noqa: E402


class DeviceIn(BaseModel):
    locale: str | None = None


def _device_token(request: Request) -> str:
    tok = request.headers.get("x-device-token", "")
    if not tok or len(tok) < 16:
        raise HTTPException(401, "missing device token")
    return tok


def _token_hash(tok: str) -> str:
    return _hashlib.sha256(tok.encode()).hexdigest()


@app.get("/api/v1/entitlement")
def get_entitlement(request: Request):
    """Resolve (and on first use, start) the caller's trial. Server-side truth."""
    tok = _device_token(request)
    rows = sb_rpc("ensure_entitlement", {"p_token_hash": _token_hash(tok)})
    row = rows[0] if isinstance(rows, list) and rows else (rows or {})
    if not row:
        raise HTTPException(503, "entitlement unavailable")
    return {
        "status": row.get("status"),
        "plan": row.get("plan"),
        "trial_started_at": row.get("trial_started_at"),
        "trial_ends_at": row.get("trial_ends_at"),
        "paid_until": row.get("paid_until"),
        "days_left": row.get("days_left"),
        "active": bool(row.get("active")),
        "trial_days": TRIAL_DAYS,
    }


@app.post("/api/v1/devices")
def register_device(body: DeviceIn, request: Request):
    """Idempotently register a device token and return its entitlement."""
    _device_token(request)  # validates presence
    return get_entitlement(request)


# ---------------------------- contact ------------------------------------ #
@app.post("/api/v1/contact")
def contact(body: ContactIn):
    rate_limit("contact", 10)
    try:
        sb_post("audit_log", {"actor": body.email, "action": "contact",
                              "meta": {"locale": body.locale, "message": body.message[:1000]}}, secret=True)
    except Exception:
        pass
    return {"ok": True}


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse({"error": "internal error"}, status_code=500)


# --------------------------------------------------------------------------- #
# serve the Command Deck (single origin: no CORS, no second deployment)
# --------------------------------------------------------------------------- #
WEB_DIR = ROOT / "web"
if WEB_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="deck")
