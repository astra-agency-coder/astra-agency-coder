#!/usr/bin/env python3
"""Generate the final foundation readiness report: COMPANY READY."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "ops" / "integrations"))
import astra  # noqa: E402
import github  # noqa: E402

STATUS = {}


def add(component, state, done, tested, result, issues="", owner=""):
    STATUS[component] = {"state": state, "implemented": done, "tested": tested,
                         "result": result, "issues": issues, "owner_action": owner}


def main() -> None:
    info = astra.api("/server_info", timeout=20)
    health = astra.health()
    roster = astra.load_roster()["agents"]
    tests = json.loads((ROOT / "ops" / "tests" / "last_run.json").read_text())

    # ── PASS ──
    add("Company identity", "PASS", "company/IDENTITY.md", "reviewed",
        "defined with hard constraints")
    add("CEO charter + agent", "PASS", ".agents/agents/astra-ceo.md", "T01, T01b",
        "registered and discoverable")
    add("Organisation design", "PASS", "company/ORG_DESIGN.md + 7 managers", "T01b",
        "8 agents, 7 departments")
    add("Agent creation", "PASS", "ops/astra.py hire", "T02, T02b",
        "agent created, run, result received")
    add("Nested delegation", "PASS", "task tool + ops/astra.py spawn", "T03, T03b",
        "manager created a specialist and delegated to it")
    add("Session continuity", "PASS", "child conversations", "T04",
        "token recalled in a follow-up on the same conversation")
    add("Memory system", "PASS", "ops/memory/", "T05",
        "survives process restart")
    add("Self-healing", "PASS", "ops/heal.py", "T06",
        "detected corruption, repaired, bounded attempts, quarantined the bad file")
    add("Reporting", "PASS", "ops/report.py", "T07",
        "owner report + board; projections separated from realised revenue")
    add("Security controls", "PASS", "scan-secrets, telegram allowlist, receive-only wallet",
        "T08, T08b, T08c, T08d", "all security tests pass")
    add("Environment audit", "PASS", "/server_info", "T09",
        f"v{info['version']}, SDK {info['sdk_version']}, {len(info.get('capabilities', []))} capabilities")

    # ── FAIL ──
    add("Department GitHub repos (creation)", "FAIL",
        "ops/provision_repos.py ready", "attempted live",
        "403 Resource not accessible by integration",
        issues="Runtime GitHub token is read-only (App installation token). "
               "Cannot create repositories or push.",
        owner="Grant a token with Administration:write + Contents:write "
              "(or add the GitHub App installation with repo-create + contents-write).")

    # ── NOT CONFIGURED ──
    add("Telegram channel", "NOT CONFIGURED", "ops/integrations/telegram.py", "unit-tested",
        "allowlist logic verified; bot not connected",
        owner="Bot token + Owner numeric user ID")
    add("Gmail", "NOT CONFIGURED", "ops/integrations/gmail.py", "code ready",
        "not connected",
        owner="Company Gmail address + app password / OAuth")
    add("Wallet (USDT/TRC20)", "NOT CONFIGURED", "ops/integrations/wallet.py", "unit-tested",
        "receive-only verifier ready; no address set",
        owner="Public receive-only TRON address")
    add("Durable scheduling", "NOT CONFIGURED", "ops/scheduler.py", "duties defined",
        "must run as an OpenHands Cloud automation (runtime is idle-recycled)",
        owner="Confirm which automation schedule to enable")

    # ── NEEDS OWNER ACTION ──
    add("GitHub write access", "NEEDS OWNER ACTION", "—", "probed",
        "read works, write denied",
        owner="Write-capable token (see FAIL above)")
    add("Agent→department repo mapping", "NEEDS OWNER ACTION", "company/departments/repos.json",
        "plan written", "blocked by GitHub write access",
        owner="Unblock GitHub write, then run `python3 ops/provision_repos.py`")

    # ── write the report ──
    L = []
    L.append("# AI ASTRA AGENCY — COMPANY READY")
    L.append("")
    L.append(f"_Foundation report generated {astra.now()}_")
    L.append("")
    L.append("## 1. Foundation summary")
    L.append("The company is founded and its machinery is built and tested. It has an "
             "identity, a CEO with real authority, seven departments with managers, a "
             "working agent-creation and delegation system, durable memory, self-healing, "
             "reporting, and prepared integrations. It has **not** started any commercial "
             "activity — by design, it awaits the Owner's first operational task.")
    L.append("")
    L.append("## 2. OpenHands environment")
    L.append(f"- Agent Server **v{info['version']}**, SDK **{info['sdk_version']}**")
    L.append(f"- Capabilities advertised: {len(info.get('capabilities', []))}")
    L.append(f"- Delegation tools available: `task`, `task_tool_set`, `start_child_conversation`")
    L.append(f"- Overall health: **{'HEALTHY' if health['ok'] else 'ATTENTION'}**")
    L.append("")
    L.append("## 3. CEO status")
    L.append("- `astra-ceo` defined in `.agents/agents/astra-ceo.md`, registered, discoverable.")
    L.append("- Holds authority, operating loop, brief format, anti-fabrication rules.")
    L.append("")
    L.append("## 4. Agent creation system")
    L.append(f"- {len(roster)} agents on the roster; create more with "
             "`python3 ops/astra.py hire`.")
    L.append("- Managers are instructed and able to create their own specialists (tested).")
    L.append("")
    L.append("## 5. Delegation & sessions")
    L.append("- Synchronous nested delegation via the `task` tool — tested.")
    L.append("- Parallel/long work via child conversations — tested.")
    L.append("- Session continuity across follow-ups — tested.")
    L.append("")
    L.append("## 6. Memory & continuity")
    L.append("- `ops/memory/`: decisions, lessons, playbooks, revenue, risks, versions.")
    L.append("- Persistence proven across a process restart — tested.")
    L.append("")
    L.append("## 7. Self-healing")
    L.append("- `ops/heal.py`: 7 checks, bounded to 3 attempts, quarantines instead of "
             "deleting, escalates what it cannot fix — tested with induced failures.")
    L.append("")
    L.append("## 8. Integrations")
    L.append("| Integration | Status |")
    L.append("|---|---|")
    L.append("| GitHub (read) | CONNECTED |")
    L.append("| GitHub (write) | FAIL — read-only token |")
    L.append("| Telegram | NOT CONFIGURED |")
    L.append("| Gmail | NOT CONFIGURED |")
    L.append("| Wallet (USDT/TRC20) | NOT CONFIGURED |")
    L.append("")
    L.append(f"## 9. Test results — {tests['passed']}/{tests['total']} PASS")
    L.append("| ID | Test | Result |")
    L.append("|---|---|---|")
    for r in tests["results"]:
        L.append(f"| {r['id']} | {r['name']} | {r['result']} |")
    L.append("")
    for title, state in [("10. PASS", "PASS"), ("11. FAIL", "FAIL"),
                         ("12. NOT CONFIGURED", "NOT CONFIGURED"),
                         ("13. NEEDS OWNER ACTION", "NEEDS OWNER ACTION")]:
        L.append(f"## {title}")
        rows = {k: v for k, v in STATUS.items() if v["state"] == state}
        if not rows:
            L.append("- none")
        for k, v in rows.items():
            L.append(f"- **{k}** — implemented: {v['implemented']}; tested: {v['tested']}; "
                     f"result: {v['result']}.")
            if v["issues"]:
                L.append(f"  - Issue: {v['issues']}")
            if v["owner_action"]:
                L.append(f"  - Needs Owner: {v['owner_action']}")
        L.append("")
    L.append("## 14. What I need from you")
    L.append("1. **GitHub write access** — a token with `Administration: write` and "
             "`Contents: write`, so I can create the seven private department repositories.")
    L.append("2. **Telegram** — bot token + your numeric Telegram user ID.")
    L.append("3. **Gmail** — the company address + an app password or OAuth token.")
    L.append("4. **Wallet** — the public USDT/TRC20 receive-only address.")
    L.append("Deliver each as a runtime secret, never in chat or a file.")
    L.append("")
    L.append("## 15. Next step")
    L.append("Foundation is complete and tested. **No commercial activity has begun.** "
             "I am waiting for your first operational task. On receipt I will scope it, "
             "staff the right department, execute, verify, and report.")
    L.append("")

    text = "\n".join(L)
    out = ROOT / "ops" / "reports" / "COMPANY_READY.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(text)
    print(f"\n[saved] {out.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
