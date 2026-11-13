#!/usr/bin/env python3
"""Reporting system for AI ASTRA AGENCY.

Generates the periodic Owner report and the internal status board from live
state: roster, task log, health, revenue ledger, risk register.

    python3 ops/report.py owner     # Owner-facing report (Markdown)
    python3 ops/report.py board     # internal status board
    python3 ops/report.py --write   # also save to ops/reports/
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
import astra  # noqa: E402

REPORTS = ROOT / "ops" / "reports"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tasks() -> list[dict]:
    if not astra.TASKS_LOG.exists():
        return []
    return [json.loads(l) for l in astra.TASKS_LOG.read_text().splitlines() if l.strip()]


def revenue_summary() -> dict:
    """Parse the revenue ledger's summary table; never invent numbers."""
    p = ROOT / "ops" / "memory" / "revenue.md"
    out = {"verified_received": "0.00", "pending": "0.00", "invoiced": "0.00",
           "expenses": "0.00", "net_realised": "0.00"}
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            key = cells[0].lower()
            if "verified received" in key:
                out["verified_received"] = cells[1]
            elif "pending" in key:
                out["pending"] = cells[1]
            elif "invoiced" in key:
                out["invoiced"] = cells[1]
            elif "expenses" in key:
                out["expenses"] = cells[1]
            elif "net realised" in key:
                out["net_realised"] = cells[1]
    return out


def risks_open() -> list[str]:
    p = ROOT / "ops" / "memory" / "risks.md"
    out = []
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("| R-") and "Open" in line:
                out.append(line)
    return out


def owner_report() -> str:
    r = astra.load_roster()
    agents = r.get("agents", {})
    t = tasks()
    ok = sum(1 for x in t if x.get("status") == "finished")
    bad = sum(1 for x in t if x.get("status") in ("error", "stopped"))
    h = astra.health()
    rev = revenue_summary()

    by_dept: dict[str, list[str]] = {}
    for a in agents.values():
        by_dept.setdefault(a["department"], []).append(a["name"])

    lines = [
        "# AI ASTRA AGENCY — Owner Report",
        f"_Generated {now()}_",
        "",
        "## Company status",
        f"- Operational status: **FOUNDATION PHASE COMPLETE**",
        f"- Commercial activity: **NOT STARTED** (awaiting Owner's first operational task)",
        f"- Agents on payroll: **{len(agents)}** ({sum(1 for a in agents.values() if a['status']=='active')} active)",
        f"- Departments: **{len(by_dept)}**",
        "",
        "## System health",
        f"- Overall: **{'HEALTHY' if h['ok'] else 'ATTENTION REQUIRED'}**",
    ]
    for c in h["checks"]:
        lines.append(f"  - {'OK' if c['ok'] else 'FAIL'} — {c['check']}: {c['detail']}")

    lines += [
        "",
        "## Work performed (foundation)",
        f"- Delegated tasks logged: **{len(t)}** ({ok} finished, {bad} failed)",
    ]
    for x in t[-5:]:
        lines.append(f"  - {x['at']} `{x['agent']}` {x['status']} ({x['elapsed_s']}s): {x['task'][:80]}")
    if not t:
        lines.append("  - (no delegated tasks logged yet)")

    lines += [
        "",
        "## Departments & headcount",
    ]
    for d in sorted(by_dept):
        lines.append(f"- **{d}**: {', '.join(sorted(by_dept[d]))}")

    lines += [
        "",
        "## Financials (USDT) — nothing here is realised until verified",
        "| Line | Amount |",
        "|---|---|",
        f"| Projected | not tracked as money |",
        f"| Invoiced, not yet due | {rev['invoiced']} |",
        f"| Pending / awaiting confirmation | {rev['pending']} |",
        f"| Verified received | {rev['verified_received']} |",
        f"| Expenses paid | {rev['expenses']} |",
        f"| Net realised | {rev['net_realised']} |",
        "",
        "## Open risks",
    ]
    rk = risks_open()
    if rk:
        for line in rk:
            cells = [c.strip() for c in line.strip("|").split("|")]
            lines.append(f"- {cells[0]}: {cells[1]} — mitigation: {cells[4]}")
    else:
        lines.append("- none registered")

    lines += [
        "",
        "## Needs Owner action",
    ]
    needs = needs_owner_action()
    if needs:
        for n in needs:
            lines.append(f"- {n}")
    else:
        lines.append("- nothing outstanding")

    lines += [
        "",
        "## Next step",
        "- Awaiting the Owner's first operational task. No commercial activity has begun.",
    ]
    return "\n".join(lines) + "\n"


def needs_owner_action() -> list[str]:
    out = []
    for name, path in [
        ("Gmail account for the company", "integration-gmail"),
        ("Telegram bot token + Owner User ID", "integration-telegram"),
    ]:
        out.append(f"{name} — see `ops/integrations/README.md#{path}`")
    return out


def board() -> str:
    r = astra.load_roster()
    t = tasks()
    lines = [
        "# AI ASTRA AGENCY — Internal Status Board",
        f"_Generated {now()}_",
        "",
        "## Agents",
        "| Agent | Department | Reports to | Status | Tools |",
        "|---|---|---|---|---|",
    ]
    for a in sorted(r.get("agents", {}).values(), key=lambda x: (x["department"], x["name"])):
        lines.append(f"| {a['name']} | {a['department']} | {a['reports_to']} | "
                     f"{a['status']} | {','.join(a['tools'])} |")
    lines += ["", "## Recent tasks", "| When | Agent | Status | Seconds | Task |",
              "|---|---|---|---|---|"]
    for x in t[-15:]:
        lines.append(f"| {x['at']} | {x['agent']} | {x['status']} | {x['elapsed_s']} | {x['task'][:70]} |")
    if not t:
        lines.append("| — | — | — | — | — |")
    return "\n".join(lines) + "\n"


def write(text: str, name: str) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = now().replace(":", "").replace("-", "")
    p = REPORTS / f"{name}-{stamp}.md"
    p.write_text(text)
    latest = REPORTS / f"{name}-latest.md"
    latest.write_text(text)
    return p


def main() -> None:
    ap = argparse.ArgumentParser(prog="report")
    ap.add_argument("kind", choices=["owner", "board"])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = owner_report() if a.kind == "owner" else board()
    print(text)
    if a.write:
        p = write(text, a.kind)
        print(f"\n[saved] {p.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
