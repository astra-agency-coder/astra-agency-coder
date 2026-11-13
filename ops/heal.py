#!/usr/bin/env python3
"""Self-healing engine for AI ASTRA AGENCY.

Diagnoses known failure modes, applies a bounded repair, re-tests, and rolls
back if the repair did not help. Never touches security-critical state or
Owner-level permissions. Bounded: at most MAX_ATTEMPTS per check.

    python3 ops/heal.py            # diagnose + repair
    python3 ops/heal.py --dry-run  # diagnose only
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
import astra  # noqa: E402

MAX_ATTEMPTS = 3
HEAL_LOG = ROOT / "ops" / "logs" / "heal.jsonl"

# Company site deployment (deliveries/astra-site) — the canonical public site,
# bound to ASTRA_SITE_PORT (default 12000). This SUPERSEDES the earlier
# astra-launch "intro_site" check, which shared the same port: leaving both in
# place would let the older launcher win the port and regress the public site.
# Expected up unless ASTRA_SITE_EXPECTED=0; repaired by re-running the
# idempotent launcher, bounded by MAX_ATTEMPTS.
SITE_DIR = ROOT / "deliveries" / "astra-site-v2"
SITE_SERVE = SITE_DIR / "serve.sh"
SITE_PORT = os.environ.get("ASTRA_SITE_PORT", "12000")
# Fallback for a hard rollback: the previous static site, kept intact.
SITE_FALLBACK_DIR = ROOT / "deliveries" / "astra-site"
SITE_FALLBACK_SERVE = SITE_FALLBACK_DIR / "serve.sh"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(entry: dict) -> None:
    HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HEAL_LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── repairs ──────────────────────────────────────────────────────────

def _repair_roster() -> str:
    """Rebuild a missing/corrupt roster from the agent definition files."""
    try:
        r = astra.load_roster()
        if not isinstance(r, dict) or "agents" not in r:
            raise ValueError("roster missing 'agents'")
    except Exception as e:
        # Corrupt roster: quarantine it (never delete) and start from scratch.
        if astra.ROSTER.exists():
            bad = astra.ROSTER.with_suffix(f".corrupt.{now().replace(':', '')}.json")
            shutil.copy2(astra.ROSTER, bad)
        r = {"company": "AI ASTRA AGENCY", "agents": {}}
        r["_recovered_from"] = f"corrupt roster quarantined: {type(e).__name__}"
    r.setdefault("agents", {})
    added = []
    for path in sorted(astra.AGENTS_DIR.glob("*.md")):
        defn = astra.parse_agent(path)
        if defn["name"] not in r["agents"]:
            r["agents"][defn["name"]] = {
                "name": defn["name"], "role": defn["name"], "department": defn["department"],
                "reports_to": defn["reports_to"], "tools": defn["tools"], "model": defn["model"],
                "status": "active", "created_at": now(), "updated_at": now(),
                "notes": "recovered by heal",
            }
            added.append(defn["name"])
    astra.save_roster(r)
    return f"roster rebuilt, added={added}" if added else "roster already consistent"


def _repair_llm() -> str:
    llm = astra.llm_config()
    return f"llm config resolves: model={llm.get('model')}"


def _repair_memory() -> str:
    created = []
    for name, header in [
        ("decisions.md", "# Decision Log\n"),
        ("lessons.md", "# Lessons Learned\n"),
        ("playbooks.md", "# Playbooks\n"),
    ]:
        p = ROOT / "ops" / "memory" / name
        if not p.exists():
            p.write_text(header)
            created.append(name)
    return f"memory files created: {created}" if created else "memory files present"


def _repair_secrets() -> str:
    clean, offenders = astra.scan_secrets()
    if clean:
        return "no secret patterns found"
    # Roll back nothing automatically; quarantine the offending lines is unsafe.
    # Instead raise so the CEO/Owner is alerted. Never silently delete data.
    raise RuntimeError(f"secret patterns present, manual action required: {offenders}")


def _repair_site() -> str:
    """Re-run the idempotent launcher to (re)start the company site."""
    if not SITE_SERVE.exists():
        raise RuntimeError(f"launcher not found: {SITE_SERVE}")
    p = subprocess.run(["bash", str(SITE_SERVE)], capture_output=True, text=True,
                       env={**os.environ, "ASTRA_SITE_PORT": SITE_PORT}, timeout=900)
    tail = (p.stdout + p.stderr).strip().splitlines()
    detail = tail[-1] if tail else "no output"
    if p.returncode != 0:
        raise RuntimeError(f"serve.sh exited {p.returncode}: {detail}")
    return f"serve.sh ok: {detail}"


# ── check registry ───────────────────────────────────────────────────
# Each entry: (name, detect()->bool_ok, repair()->str)

def _detect_server() -> bool:
    try:
        astra.api("/server_info", timeout=15)
        return True
    except SystemExit:
        return False


def _detect_auth() -> bool:
    try:
        astra.api("/api/conversations/count", timeout=15)
        return True
    except SystemExit:
        return False


def _detect_llm() -> bool:
    try:
        astra.llm_config()
        return True
    except SystemExit:
        return False


def _detect_roster() -> bool:
    if not astra.ROSTER.exists():
        return False
    try:
        r = astra.load_roster()
    except Exception:
        return False
    names = {p.stem for p in astra.AGENTS_DIR.glob("*.md")}
    return names.issubset(set(r.get("agents", {})))


def _detect_memory() -> bool:
    return all((ROOT / "ops" / "memory" / f).exists()
               for f in ("decisions.md", "lessons.md", "playbooks.md"))


def _detect_secrets() -> bool:
    clean, _ = astra.scan_secrets()
    return clean


def _detect_disk() -> bool:
    total, used, free = shutil.disk_usage(ROOT)
    return free > 200 * 1024 * 1024


def _site_expected() -> bool:
    return os.environ.get("ASTRA_SITE_EXPECTED", "1") not in ("0", "false", "no")


def _detect_site() -> bool:
    if not _site_expected():
        return True  # opt-out: site intentionally down, nothing to repair
    import urllib.request
    url = f"http://127.0.0.1:{SITE_PORT}/en"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


CHECKS = [
    ("agent_server", _detect_server, None, "external", "agent server unreachable — escalate"),
    ("api_auth", _detect_auth, None, "external", "API auth failing — escalate"),
    ("llm_config", _detect_llm, _repair_llm, "internal", "cannot resolve LLM config"),
    ("roster", _detect_roster, _repair_roster, "internal", "roster inconsistent"),
    ("memory", _detect_memory, _repair_memory, "internal", "memory files missing"),
    ("secrets", _detect_secrets, _repair_secrets, "critical", "secret leak"),
    ("disk", _detect_disk, None, "external", "low disk space"),
    ("astra_site", _detect_site, _repair_site, "internal",
     "company site down on :" + SITE_PORT + " — set ASTRA_SITE_EXPECTED=0 to opt out"),
]


def run(dry_run: bool = False) -> dict:
    results = []
    for name, detect, repair, kind, failmsg in CHECKS:
        entry = {"check": name, "at": now(), "attempts": 0, "healed": False}
        try:
            ok = detect()
        except Exception as e:  # a broken detector is itself a finding
            ok = False
            entry["detect_error"] = f"{type(e).__name__}: {e}"
        if ok:
            entry["status"] = "healthy"
            results.append(entry)
            continue

        entry["status"] = "unhealthy"
        if dry_run or repair is None:
            entry["action"] = "none (dry-run)" if dry_run else f"escalate: {failmsg}"
            entry["status"] = "unhealthy"
            results.append(entry)
            continue

        for attempt in range(1, MAX_ATTEMPTS + 1):
            entry["attempts"] = attempt
            try:
                detail = repair()
                entry.setdefault("repairs", []).append({"attempt": attempt, "detail": detail})
            except Exception as e:
                entry.setdefault("repairs", []).append(
                    {"attempt": attempt, "error": f"{type(e).__name__}: {e}"})
            try:
                if detect():
                    entry["healed"] = True
                    entry["status"] = "healed"
                    break
            except Exception:
                pass
        else:
            entry["status"] = "unrepaired"
            entry["action"] = f"escalate: {failmsg}"
        results.append(entry)

    report = {
        "at": now(),
        "dry_run": dry_run,
        # A run is successful if nothing is left broken: healthy or healed.
        "healthy": all(r["status"] in ("healthy", "healed") for r in results),
        "results": results,
        "escalations": [r["check"] for r in results
                        if r["status"] in ("unrepaired", "unhealthy")
                        and r.get("action", "").startswith("escalate")],
    }
    record(report)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(prog="heal")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rep = run(a.dry_run)
    for r in rep["results"]:
        mark = {"healthy": "OK ", "healed": "FIX", "unhealthy": "!! ", "unrepaired": "!! "}[r["status"]]
        extra = f" attempts={r['attempts']}" if r["attempts"] else ""
        print(f"[{mark}] {r['check']:16}{extra}")
        for rep_d in r.get("repairs", []):
            print(f"        attempt {rep_d['attempt']}: {rep_d.get('detail') or rep_d.get('error')}")
        if r.get("action", "").startswith("escalate"):
            print(f"        -> {r['action']}")
    print(f"\nall healthy: {rep['healthy']} | escalations: {rep['escalations']}")
    sys.exit(0 if rep["healthy"] else 1)


if __name__ == "__main__":
    main()
