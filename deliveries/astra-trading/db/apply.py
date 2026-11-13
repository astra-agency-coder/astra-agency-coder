#!/usr/bin/env python3
"""Apply SQL migration files to the Astra Trading Supabase project.

Usage: python3 apply.py [file.sql ...]     (default: every .sql in this folder, sorted)

Uses the Supabase Management API with the account token held in the runtime
secret store. The token and project ref never touch disk.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ops"))
import secrets as S  # noqa: E402

PROJECT_REF = "unrmzqnvfgaqrwyeqddn"
API = "https://api.supabase.com/v1"


def run_sql(token: str, sql: str):
    body = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(
        f"{API}/projects/{PROJECT_REF}/database/query",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # noqa: BLE001
        return "ERR", str(e)


def main() -> int:
    token = S.resolve("ASTRA_SUPABASE_SERVICE_KEY")
    if not token:
        print("no Supabase management token configured", file=sys.stderr)
        return 2
    here = Path(__file__).parent
    files = [Path(a) for a in sys.argv[1:]] or sorted(here.glob("*.sql"))
    rc = 0
    for f in files:
        status, out = run_sql(token, f.read_text())
        ok = status in (200, 201)
        print(f"[{'ok' if ok else 'FAIL'}] {f.name}  http={status}")
        if not ok:
            rc = 1
            print("   ", out[:600])
        elif out and out.strip() not in ("[]", ""):
            print("   ", out[:300])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
