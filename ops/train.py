#!/usr/bin/env python3
"""Run an intensive training module for a department manager.

Spawns the manager in its own child conversation with a curriculum attached, so
the manager decomposes the work, may hire specialists, executes the modules with
real tools, and returns an evidence-backed summary. Training is a run, not a
document: a module counts only when it produced a real artifact.

    python3 ops/train.py <agent> <curriculum> [--dry-run] [--max-iter N]
    python3 ops/train.py --list
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
import astra  # noqa: E402

CURRICULA = ROOT / "company" / "training" / "curricula"
LOGDIR = ROOT / "company" / "training" / "runs"


def list_curricula() -> list[str]:
    return sorted(p.stem for p in CURRICULA.glob("*.md"))


def build_brief(agent: str, name: str, text: str) -> str:
    dept = astra.load_roster()["agents"].get(agent, {}).get("department", "?")
    return f"""INTENSIVE TRAINING RUN — department: {dept} — manager: {agent}

You are running a training curriculum, NOT commercial work. No customer contact,
no outreach, no sales, no external commitments. Build real skills and real
artifacts the department will reuse.

## Curriculum: {name}
{text}

## How to execute
1. Plan the modules with the task_tracker tool.
2. For each module: do the work with real tools, then produce the required
   artifact. A module is DONE only when its artifact exists and its check passed.
3. You may hire up to 3 specialists for this run with
   `python3 ops/astra.py hire <name> --dept {dept} --reports-to {agent} --tools <a,b>`
   and delegate with the **task** tool. Retire them afterwards with `fire`.
4. Save durable department knowledge to your scoped repo:
   `python3 ops/deptrepo.py clone {agent}` then write under `knowledge/`, then
   `python3 ops/deptrepo.py save {agent} "training: <curriculum>"`.
   Never print or commit your key.
5. Keep a run log at `company/training/runs/{agent}-{name}.md` with: modules,
   commands, real output, artifacts, and anything that FAILED.

## Hard rules
- Never fabricate results, sources, clients or capabilities. Show real output.
- Bound retries to 3; if blocked, record the blocker and stop that module.
- Use real tools (terminal, ffmpeg, python, browser). Cite study sources by URL.

## Final report (be concise)
For each module: name | artifact path | check result (PASS/FAIL). Then: what is
now reusable, open items, and blockers. State plainly if something failed.
"""


def run(agent: str, curriculum: str, max_iter: int = 80, dry_run: bool = False) -> dict:
    path = CURRICULA / f"{curriculum}.md"
    if not path.exists():
        raise SystemExit(f"no curriculum '{curriculum}'. have: {list_curricula()}")
    if agent not in astra.load_roster()["agents"]:
        raise SystemExit(f"unknown agent '{agent}'")
    brief = build_brief(agent, curriculum, path.read_text())
    LOGDIR.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(brief[:1200])
        return {"dry_run": True, "agent": agent, "curriculum": curriculum}
    out = astra.spawn(agent, brief, max_iterations=max_iter, timeout_s=2400)
    (LOGDIR / f"{agent}-{curriculum}.md").write_text(
        f"# Training run — {agent} — {curriculum}\n\n"
        f"- conversation: {out['conversation_id']}\n"
        f"- status: {out['status']}\n"
        f"- elapsed_s: {out['elapsed_s']}\n\n## Result\n{out['result']}\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", nargs="?")
    ap.add_argument("curriculum", nargs="?")
    ap.add_argument("--max-iter", type=int, default=80)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(list_curricula()))
        return
    if not a.agent or not a.curriculum:
        raise SystemExit("usage: train.py <agent> <curriculum>")
    out = run(a.agent, a.curriculum, a.max_iter, a.dry_run)
    if not a.dry_run:
        out = dict(out, curriculum=a.curriculum)
        print(f"[{out['status']}] {out['agent']} <- {a.curriculum} "
              f"in {out['elapsed_s']}s")
        print(out["result"][:2000])


if __name__ == "__main__":
    main()
