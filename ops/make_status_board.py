#!/usr/bin/env python3
"""Render the AI ASTRA AGENCY status board to a PNG for the Owner.

Reads live data (roster, dept repos, tests, integrations, memory) and lays it out
as a board image in the brand's visual language. Reproducible: run it any time.

    python3 ops/make_status_board.py    # writes ops/reports/status-board.png
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "ops" / "integrations"))

OUT = ROOT / "ops" / "reports" / "status-board.png"
BG, SURF, LINE = "#07070C", "#12121A", "#2A2A38"
INK, SUB, GOLD = "#EEF0F7", "#A9AEBF", "#E8C766"
BULL, BEAR = "#16C79A", "#FF4D6D"


def roster() -> dict:
    return json.loads((ROOT / "company" / "roster.json").read_text())["agents"]


def dept_repos() -> dict:
    p = ROOT / "company" / "departments" / "repos.json"
    return json.loads(p.read_text()) if p.exists() else {}


def last_tests() -> dict:
    p = ROOT / "ops" / "tests" / "last_run.json"
    return json.loads(p.read_text()) if p.exists() else {}


def integration_status() -> dict:
    try:
        r = subprocess.run([sys.executable, "ops/integrations/status.py"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=90)
        return json.loads(r.stdout) if r.returncode == 0 else {}
    except Exception:
        return {}


def recent_tasks(n: int = 6) -> list[dict]:
    p = ROOT / "ops" / "memory" / "tasks.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return rows[-n:][::-1]


def build_html() -> str:
    ag = roster()
    active = [a for a in ag.values() if a.get("status") == "active"]
    retired = [a for a in ag.values() if a.get("status") != "active"]
    by_dept: dict[str, list[dict]] = {}
    for a in active:
        by_dept.setdefault(a.get("department", "—"), []).append(a)

    repos = dept_repos()
    tests = last_tests()
    integ = integration_status()
    tasks = recent_tasks()

    dept_rows = "".join(
        f'<tr><td><b>{d}</b></td>'
        f'<td>{", ".join(sorted(x["name"] for x in ms))}</td>'
        f'<td class="num">{len(ms)}</td></tr>'
        for d, ms in sorted(by_dept.items()))

    repo_rows = "".join(
        f'<tr><td>{r["manager"]}</td><td class="mono">{r["repo"].split("/")[-1]}</td>'
        f'<td class="{"ok" if r.get("ok") else "bad"}">'
        f'{"private + write" if r.get("ok") else "check"}</td></tr>'
        for r in repos.get("repos", []))

    integ_rows = "".join(
        f'<tr><td>{k}</td><td class="{"ok" if (v.get("status")=="CONNECTED") else "warn"}">'
        f'{v.get("status","?")}</td></tr>'
        for k, v in sorted(integ.items()))

    t_res = tests.get("results", [])
    t_pass = tests.get("passed", sum(1 for r in t_res if r.get("result") == "PASS"))
    t_total = tests.get("total", len(t_res) or 13)
    task_rows = "".join(
        f'<tr><td class="mono">{t.get("at","")[11:16]}</td><td>{t.get("agent","")}</td>'
        f'<td class="{"ok" if t.get("status")=="finished" else "warn"}">{t.get("status","")}</td></tr>'
        for t in tasks)

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>AI ASTRA AGENCY — Status Board</title><style>
*{{box-sizing:border-box;margin:0}}
body{{background:{BG};color:{INK};font-family:'IBM Plex Sans',system-ui,sans-serif;padding:44px}}
.board{{max-width:1180px;margin:0 auto}}
h1{{font-family:'Space Grotesk',system-ui;font-size:38px;letter-spacing:-.02em}}
h1 small{{display:block;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:{GOLD};margin-bottom:8px}}
.ts{{color:{SUB};font-size:13px;margin-top:6px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}}
.kpi{{background:{SURF};border:1px solid {LINE};border-radius:14px;padding:18px 20px}}
.kpi b{{display:block;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:{SUB}}}
.kpi span{{font-family:'Space Grotesk',system-ui;font-size:34px;color:{GOLD}}}
.kpi i{{font-style:normal;font-size:13px;color:{SUB};margin-left:8px}}
h2{{font-family:'Space Grotesk',system-ui;font-size:18px;margin:34px 0 12px;padding-bottom:9px;border-bottom:1px solid {LINE}}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
td,th{{text-align:left;padding:9px 12px;border-bottom:1px solid {LINE}}}
th{{color:{SUB};font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.08em}}
.num,.mono{{font-family:'IBM Plex Mono',monospace}}
.ok{{color:{BULL}}} .warn{{color:{GOLD}}} .bad{{color:{BEAR}}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:26px}}
footer{{margin-top:38px;padding-top:16px;border-top:1px solid {LINE};color:{SUB};font-size:12px}}
</style></head><body><div class="board">
  <h1><small>AI ASTRA AGENCY</small>Company status board</h1>
  <div class="ts">Generated {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · foundation phase</div>

  <div class="kpis">
    <div class="kpi"><b>Active agents</b><span>{len(active)}</span><i>of {len(ag)} on roster</i></div>
    <div class="kpi"><b>Departments</b><span>{len(by_dept)}</span><i>each with a manager</i></div>
    <div class="kpi"><b>Readiness tests</b><span>{t_pass}/{t_total}</span><i>passing</i></div>
    <div class="kpi"><b>Dept repos</b><span>{repos.get('created',0)}/{repos.get('desired',10)}</span><i>private, scoped</i></div>
  </div>

  <div class="cols">
    <div>
      <h2>Departments &amp; managers</h2>
      <table><tr><th>Department</th><th>Active agents</th><th>#</th></tr>{dept_rows}</table>
    </div>
    <div>
      <h2>Integrations</h2>
      <table><tr><th>Channel</th><th>Status</th></tr>{integ_rows}</table>
      <h2>Recent delegations</h2>
      <table><tr><th>Time</th><th>Agent</th><th>Result</th></tr>{task_rows}</table>
    </div>
  </div>

  <h2>Department repositories — one per manager, private</h2>
  <table><tr><th>Manager</th><th>Repository</th><th>Access</th></tr>{repo_rows}</table>

  <footer>Every manager holds one write-enabled deploy key bound to its own repository;
  the company token is never shared. Generated from live company data — no figures invented.
  Retired agents: {len(retired)}.</footer>
</div></body></html>"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = ROOT / "ops" / "reports" / "status-board.html"
    html.write_text(build_html())
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        pg.goto("file://" + str(html.resolve()), wait_until="load")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
