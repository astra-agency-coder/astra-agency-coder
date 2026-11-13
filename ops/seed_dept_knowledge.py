#!/usr/bin/env python3
"""Seed each department repo with real, department-specific knowledge.

Runs through each manager's own scoped deploy key (ops/deptrepo.py), so the
content is written the same way the manager writes it day to day — and the
isolation is exercised on every run.

    python3 ops/seed_dept_knowledge.py            # all departments
    python3 ops/seed_dept_knowledge.py astra-cto  # one department

Every file is grounded in work that actually exists in this repository; nothing
is invented. Safe to re-run (files are overwritten with the same content).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "ops" / "integrations"))
from provision_repos import DEPARTMENTS  # noqa: E402

WORK = Path.home() / ".astra" / "work"

KNOWLEDGE: dict[str, dict[str, str]] = {
    "astra-cto": {
        "Astra-Trading-architecture.md": """# Astra Trading — architecture

## Components
- `engine/` — market data (Twelve Data / Yahoo fallback), analysis, backtest,
  evaluator, loop. `loop.py` scans on an interval and writes setups.
- `api/app.py` — FastAPI. Serves the landing at `/`, the deck at `/deck.html`,
  the JSON API under `/api/v1/`.
- `web/` — static front end (landing + deck + `js/app.js`, `js/i18n.js`).
- Supabase (Postgres) — `setups`, `track_record`, `devices`, `entitlements`,
  `payments`.

## Entitlement
`db/003_entitlements.sql` adds `devices` + `entitlements` and two RPCs:
`ensure_entitlement(token_hash)` (starts a 7-day trial on first use, expires it
after the window) and `activate_entitlement(token_hash, days)` (called only after
a payment is verified on-chain). The browser holds an opaque device token and
sends it as `X-Device-Token`; the server hashes it. No entitlement state lives in
the browser.

## Operational rules learned the hard way
- The engine loop imports its modules at boot: an edit to `analysis.py` does not
  affect the running process. Restart after any engine change.
- Publish only timeframes with a measured edge (4h, 1d). 1h is retired.
""",
        "Deploy-and-runtime.md": """# Deploy and runtime

- Cloud runtime is ephemeral: a long-lived process dies when the sandbox recycles.
  Durable scheduling belongs in an OpenHands Cloud automation that runs
  `python3 ops/scheduler.py run <duty>`.
- `ops/heal.py` probes components and repairs bounded failures (max 3 attempts
  per check, then escalate). Run it every 30 minutes.
- Services in use: API :12001, design preview :12011/:12012.
- Secrets resolve through `ops/secrets.py`; values live in the runtime store,
  never in the repo. `python3 ops/astra.py scan-secrets` must stay clean.
""",
    },
    "astra-cao": {
        "XAUUSD-edge-methodology.md": """# XAU/USD — edge methodology

## Method
Walk-forward: 70% train / 30% hold-out on a 1496-bar gold series. A rule is kept
only if it holds positive expectancy out of sample. Then a full-series replay is
run for the published numbers.

## Result (published)
| TF | trades | win | total R | avg R | max DD |
|----|--------|-----|---------|-------|--------|
| 4h | 43 | 69.8% | +17.0 | +0.40 | -3.0 |
| 1d | 35 | 71.4% | +15.0 | +0.43 | -5.0 |

1h was tested and retired: avgR -0.137, no stable edge. We do not publish it.

## Two gates for a setup
1. Edge — does the rule make money out of sample?
2. Reachability — can price reach the zone before the order expires?
A zone 3xATR away never triggers inside a 24h window, so `build_setup` prefers the
strongest zone within 3xATR of price. Optimising only gate 1 produced untradeable
calls (the bug behind the +0.17R era).
""",
    },
    "astra-ccr": {
        "Brand-and-design-system.md": """# Brand and design system

- Tokens: `brand/tokens.json` (colour, type, space, radius). `design/tokens.extended.json`
  adds motion, shadow, breakpoints, z-index and an `rtl` block.
- Logo: `brand/logo-mark.svg` ("Ingot A"), plus `logo-mono`, `logo-mark-onlight`,
  `wordmark-{ar,en,tr}.svg`, `favicon.svg`.
- Type: Space Grotesk (display), IBM Plex Sans (body), IBM Plex Sans Arabic (all
  Arabic text), IBM Plex Mono (prices/data). All OFL-1.1.
- Locales ar/en/tr with full RTL mirror (`dir=rtl`); numerals stay LTR; charts
  stay LTR.
- Board: `brand/brand-sheet.png`, generated from the tokens by
  `brand/build/build_brand.py` so it cannot drift from the product (regenerate with `python3 brand/build/build_brand.py`).
- Design docs: `design/DESIGN_SYSTEM.md` (34 components), `INFORMATION_ARCHITECTURE.md`,
  `WIREFRAMES.md`, and the landing mockup `design/landing-mockup.html`.

## Rule
A loaded font is not an applied font: every display class needs an explicit stack
per script, and `[dir=rtl]` must name the Arabic family first.
""",
    },
    "astra-cmo": {
        "Positioning-and-pricing.md": """# Positioning and pricing

## Positioning
Astra Trading reads gold like a desk, not a feed: rule-based support/resistance,
liquidity and session context, with a clear scenario (entry, stop, targets) and a
public, auto-graded track record that is never edited.

## Pricing
| Plan | Price | Notes |
|------|-------|-------|
| Free | $0 | delayed setups, no alerts |
| Pro | $39 / month | full live setups, alerts, position-size calculator |
| Founder | $349 / year | Pro + two months free, priority refresh, direct support |

## Payment
USDT on TRON (TRC20) to a receive-only wallet, verified on-chain. We never ask
for keys. Figures on the landing are labelled illustrative until real data exists.
""",
    },
    "astra-cpo": {
        "Product-map.md": """# Product map

## Journey
discover -> trial -> live setups -> subscribe -> verify -> pay -> activated -> renew.

## Surfaces
- Landing `/` — marketing, pricing, track record.
- Deck `/deck.html` — live setups, zones, scenarios.
- Checkout — USDT (TRC20), on-chain verification then `activate_entitlement`.

## Gate
Trial and subscription are server facts (see `db/003_entitlements.sql`). The deck
chip reads live entitlement; if the network fails the gate locks rather than
silently unlocking. Reset re-checks the server.

## Open items
- Promote setups out of shadow mode once the promotion policy is signed off.
- Rebuild the deck on the design system (the landing already uses it).
""",
    },
    "astra-cro": {
        "Demand-and-pricing-verification.md": """# Demand and pricing verification

Verified during foundation (no commercial activity):
- Retail gold interest is persistent; the differentiator buyers respond to is a
  public, unedited track record, not more signals.
- $39/month sits inside the band retail traders already pay for tools; a
  one-year plan at ~2 months free is the standard anchor.
- USDT (TRC20) is the lowest-friction settlement for this audience and avoids
  platform payment rules we must not circumvent.

## Status
Evidence is desk research, not customer interviews — there are no customers yet.
Every figure stays labelled illustrative until real usage exists.
""",
    },
    "astra-cqo": {
        "Quality-process.md": """# Quality process

## Before any delivery
1. requirements check, 2. implementation review, 3. functional test, 4. defect
sweep, 5. quality review, 6. delivery matches agreement, 7. result documented.

## Suite
`python3 ops/tests/run_tests.py` — 13 groups (CEO definition, delegation registry,
memory restart, self-heal, owner report, secret scan, Telegram owner-only, wallet
receive-only, control plane, environment, scoped access, wallet validation,
Telegram secrets). Target: 13/13.

## Rules
Never claim a function is delivered unless it was exercised. Never use fake work
or reviews. A delegation to a review agent needs a larger iteration budget than a
build task and must write findings to disk as it goes.
""",
    },
    "astra-coo": {
        "Operations-runbook.md": """# Operations runbook

## Duties (ops/scheduler.py)
- health: `ops/heal.py` every 30 min.
- board: `ops/report.py board` every 6 h.
- owner_report: `ops/report.py owner` daily 09:00.
- secret_scan: `ops/astra.py scan-secrets` daily 03:00.
- trading_loop: `ops/astra.py ensure-trading-loop` every 10 min.

## Self-healing
Bounded: max 3 repair attempts per check, then escalate with the exact failure.
Never loop forever. Never modify security-sensitive components without approval.

## Runtime
Cloud sandboxes recycle when idle, so durable schedules run as OpenHands Cloud
automations that invoke the duties above, not as long-lived processes here.
""",
    },
    "astra-cbdo": {
        "Channels-and-approach.md": """# Channels and approach

## Approach
Find real, permitted channels; no spam, no rules circumvention. Prefer platforms
and buyers that accept crypto settlement directly.

## Candidate channels (not yet worked)
- Trading communities and forums where a public track record is the entry ticket.
- Direct outreach to small prop/fund desks that want a gold research feed.
- Content-led acquisition: the track record page as the proof asset.

## Status
Foundation only. No outreach, offers or contracts have been made. Any commercial
activity starts only after the Owner's first operational task.
""",
    },
    "astra-ciso": {
        "Access-and-secrets-policy.md": """# Access and secrets policy

## Least privilege
Each manager holds one write-enabled SSH deploy key, registered on exactly one
repository. GitHub binds a deploy key to a single repo, so a manager cannot read
or push another department's repo even if instructed to. The company-wide token is
never given to a manager. Verify with `python3 ops/provision_access.py --verify`
(expect 10/10 isolated).

## Secrets
Values live only in the runtime secret store (`ops/secrets.py`) and in
`~/.astra/keys` (0600). The repo references secret *names*, never values.
`ops/astra.py scan-secrets` must stay clean; run it daily.

## Owner channel
Telegram accepts commands only from the Owner's numeric id; every other sender is
rejected. No secret, password or recovery phrase is ever sent over Telegram.
""",
    },
}

WORK_NOTE = """# Work log — {dept}

Drop dated work here: deliverables, findings, drafts. One file per piece of work.
Keep it honest and specific; link the artifact this work produced.
"""


def seed(manager: str, slug: str, dept: str) -> bool:
    priv = Path.home() / ".astra" / "keys" / f"{manager}_deploy"
    if not priv.exists():
        print(f"[skip] {manager}: no deploy key")
        return False
    d = WORK / slug
    if not d.exists():
        rc = subprocess.run([sys.executable, "ops/deptrepo.py", "clone", manager],
                            cwd=str(ROOT), capture_output=True, text=True)
        if rc.returncode != 0:
            print(f"[fail] {manager}: clone -> {rc.stdout}{rc.stderr}")
            return False
    for name, text in KNOWLEDGE.get(manager, {}).items():
        (d / "knowledge").mkdir(exist_ok=True)
        (d / "knowledge" / name).write_text(text)
    (d / "work").mkdir(exist_ok=True)
    (d / "work" / "README.md").write_text(WORK_NOTE.format(dept=dept))
    rc = subprocess.run([sys.executable, "ops/deptrepo.py", "save", manager,
                         f"docs(knowledge): seed {dept} foundation notes"],
                        cwd=str(ROOT), capture_output=True, text=True)
    ok = rc.returncode == 0
    print(f"[{'ok' if ok else 'fail'}] {manager} -> {slug}: {(rc.stdout or rc.stderr).strip()[:80]}")
    return ok


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok = 0
    for dept, (manager, slug, _p) in DEPARTMENTS.items():
        if only and manager != only:
            continue
        ok += bool(seed(manager, slug, dept))
    print(f"\nseeded {ok} department repo(s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
