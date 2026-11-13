#!/usr/bin/env python3
"""Secret resolution for AI ASTRA AGENCY integrations.

Resolution order for a secret named N:
1. Environment variable N (how OpenHands injects registered secrets into a
   conversation's processes).
2. The OpenHands runtime secret store: `GET /api/settings/secrets/{N}`.

Secrets are read into memory only. They are never written to disk, never logged,
and never included in any report. Values are masked in all output.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

_CACHE: dict[str, str | None] = {}


def _runtime() -> tuple[str, str] | None:
    """Return (runtime_url, session_api_key) from the runtime environment."""
    url = os.environ.get("RUNTIME_URL")
    key = os.environ.get("SESSION_API_KEY")
    env = Path("/proc/1/environ")
    if env.exists():
        for entry in env.read_bytes().split(b"\0"):
            if not entry:
                continue
            k, _, v = entry.partition(b"=")
            k = k.decode(errors="ignore")
            v = v.decode(errors="ignore")
            if k == "RUNTIME_URL" and not url:
                url = v
            elif k == "SESSION_API_KEY" and not key:
                key = v
    if url and key:
        return url.rstrip("/"), key
    return None


def resolve(name: str) -> str | None:
    """Return the secret value, or None if it is not configured anywhere."""
    if name in _CACHE:
        return _CACHE[name]

    val = os.environ.get(name)
    if val:
        _CACHE[name] = val
        return val

    rt = _runtime()
    if not rt:
        _CACHE[name] = None
        return None
    url, key = rt
    req = urllib.request.Request(f"{url}/api/settings/secrets/{name}",
                                headers={"X-Session-API-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            val = r.read().decode().strip()
    except Exception:
        val = None
    _CACHE[name] = val or None
    return _CACHE[name]


def mask(value: str | None) -> str:
    """Safe representation of a secret for logs and reports."""
    if not value:
        return "<unset>"
    if len(value) <= 8:
        return "<set:%d chars>" % len(value)
    return f"{value[:4]}…{value[-4:]} ({len(value)} chars)"


def put(name: str, value: str, description: str = "") -> bool:
    """Store or update a secret in the runtime secret store. Never returns it."""
    rt = _runtime()
    if not rt:
        return False
    url, key = rt
    body = json.dumps({"name": name, "value": value,
                       "description": description}).encode()
    req = urllib.request.Request(f"{url}/api/settings/secrets", data=body,
                                 method="PUT",
                                 headers={"X-Session-API-Key": key,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = r.status == 200
    except Exception:
        ok = False
    if ok:
        _CACHE.pop(name, None)
    return ok


def status(names: list[str]) -> dict:
    return {n: mask(resolve(n)) for n in names}


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or ["GITHUB_TOKEN_WRITE", "ASTRA_TELEGRAM_BOT_TOKEN",
                             "ASTRA_OWNER_TELEGRAM_ID", "ASTRA_GMAIL_ADDRESS",
                             "ASTRA_GMAIL_APP_PASSWORD", "ASTRA_WALLET_USDT_TRC20"]
    print(json.dumps(status(names), indent=2))
