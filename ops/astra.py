#!/usr/bin/env python3
"""ASTRA control plane — agent workforce management for AI ASTRA AGENCY.

Runs inside an OpenHands Cloud runtime and drives the local agent server
(`RUNTIME_URL`) to create, brief, run and record agents. Nothing here holds
plaintext credentials: the LLM config is read live from an existing
conversation's encrypted state and passed back with `secrets_encrypted=True`.

Usage:
    python3 ops/astra.py env
    python3 ops/astra.py roster
    python3 ops/astra.py hire <name> [--dept D] [--reports-to R] [--tools a,b]
    python3 ops/astra.py fire <name>
    python3 ops/astra.py spawn <agent> "<task>" [--json]
    python3 ops/astra.py status
    python3 ops/astra.py tasks
    python3 ops/astra.py health
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / ".agents" / "agents"
ROSTER = ROOT / "company" / "roster.json"
TASKS_LOG = ROOT / "ops" / "memory" / "tasks.jsonl"
REPORTS_DIR = ROOT / "ops" / "reports"
CONV_DIR = Path(os.environ.get("OH_CONVERSATIONS_PATH", "/var/openhands/conversations"))

DEFAULT_TOOLS = ["terminal", "file_editor", "task_tracker", "grep", "glob"]
MANAGER_TOOLS = DEFAULT_TOOLS + ["task_tool_set"]


# ── runtime discovery ────────────────────────────────────────────────

def _proc_env(pid: str = "1") -> dict[str, str]:
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes().decode("utf8", "replace")
    except OSError:
        return {}
    return dict(x.split("=", 1) for x in raw.split("\0") if "=" in x)


def runtime() -> tuple[str, str]:
    env = _proc_env()
    url = os.environ.get("RUNTIME_URL") or env.get("RUNTIME_URL")
    key = os.environ.get("SESSION_API_KEY") or env.get("SESSION_API_KEY")
    if not url or not key:
        raise SystemExit("FATAL: RUNTIME_URL / SESSION_API_KEY not found")
    return url.rstrip("/"), key


def api(path: str, payload=None, method=None, timeout: int = 120):
    url, key = runtime()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url + path, data=data, method=method,
        headers={"Content-Type": "application/json", "X-Session-API-Key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:800]
        raise SystemExit(f"API {method or 'GET'} {path} -> {e.code}: {detail}")


def llm_config() -> dict:
    """Reuse the working LLM config from the most recent conversation state."""
    candidates = sorted(
        glob.glob(str(CONV_DIR / "*" / "base_state.json")),
        key=os.path.getmtime, reverse=True,
    )
    for path in candidates:
        try:
            state = json.loads(Path(path).read_text())
            llm = dict(state["agent"]["llm"])
        except Exception:
            continue
        llm.pop("fallback_strategy", None)
        if llm.get("api_key"):
            return llm
    raise SystemExit("FATAL: no usable LLM config found in conversation state")


# ── roster ───────────────────────────────────────────────────────────

def load_roster() -> dict:
    if ROSTER.exists():
        return json.loads(ROSTER.read_text())
    return {"company": "AI ASTRA AGENCY", "agents": {}}


def save_roster(r: dict) -> None:
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    ROSTER.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_task(entry: dict) -> None:
    TASKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TASKS_LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── agent definitions ────────────────────────────────────────────────

def agent_file(name: str) -> Path:
    return AGENTS_DIR / f"{name}.md"


def parse_agent(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"bad agent file: {path}")
    fm_raw, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_raw.splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("\t"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    tools = [t.strip("- ").strip() for t in re.findall(r"^\s*-\s*(\S+)", fm_raw, re.M)]
    return {"name": fm.get("name", path.stem), "description": fm.get("description", ""),
            "tools": tools, "model": fm.get("model", "inherit"), "body": body.strip(),
            "department": fm.get("department", "unassigned"),
            "reports_to": fm.get("reports_to", "astra-ceo")}


def hire(name: str, dept: str = "unassigned", reports_to: str = "astra-ceo",
         tools: list[str] | None = None, description: str = "", body: str = "") -> dict:
    tools = tools or DEFAULT_TOOLS
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    desc = description or f"{name} — {dept} specialist at AI ASTRA AGENCY."
    prompt = body or (
        f"# {name}\n\nYou are **{name}**, a specialist in the **{dept}** department of "
        f"AI ASTRA AGENCY. You report to `{reports_to}`.\n\n"
        "Operate as a senior professional: plan briefly, execute thoroughly, verify "
        "your own output, and report back concisely with what you did, the evidence, "
        "and any blocker. Never fabricate results. Never touch secrets. Never make "
        "financial commitments.\n"
    )
    front = ["---", f"name: {name}", "description: >", f"  {desc}",
             f"department: {dept}", f"reports_to: {reports_to}"]
    front.append("tools:")
    front += [f"  - {t}" for t in tools]
    front += ["model: inherit", "---", "", prompt]
    agent_file(name).write_text("\n".join(front) + "\n")

    r = load_roster()
    r["agents"][name] = {
        "name": name, "role": f"{dept} specialist", "department": dept,
        "reports_to": reports_to,
        "tools": tools, "model": "inherit", "status": "active",
        "created_at": r["agents"].get(name, {}).get("created_at", now()),
        "updated_at": now(),
        "notes": "definition at .agents/agents/%s.md" % name,
    }
    save_roster(r)
    return r["agents"][name]


def purge(name: str) -> None:
    """Remove a retired agent from the roster entirely (history stays in git)."""
    r = load_roster()
    a = r["agents"].get(name)
    if not a:
        raise SystemExit(f"no such agent: {name}")
    if a.get("status") != "retired":
        raise SystemExit(f"refusing to purge active agent: {name}")
    del r["agents"][name]
    save_roster(r)
    f = agent_file(name)
    f.with_suffix(".md.retired").unlink(missing_ok=True)


def fire(name: str, reason: str = "retired by CEO") -> None:
    r = load_roster()
    if name not in r["agents"]:
        raise SystemExit(f"no such agent: {name}")
    r["agents"][name]["status"] = "retired"
    r["agents"][name]["retired_at"] = now()
    r["agents"][name]["notes"] = reason
    save_roster(r)
    f = agent_file(name)
    if f.exists():
        f.rename(f.with_suffix(".md.retired"))


# ── execution ────────────────────────────────────────────────────────

def spawn(agent: str, task: str, max_iterations: int = 40,
          tools: list[str] | None = None, system_suffix: str = "",
          timeout_s: int = 900) -> dict:
    """Run `agent` on `task` in its own child conversation; return the result."""
    defn = parse_agent(agent_file(agent)) if agent_file(agent).exists() else None
    if defn is None:
        raise SystemExit(f"no definition for agent '{agent}' — run `hire {agent}` first")

    use_tools = tools or defn["tools"] or DEFAULT_TOOLS
    suffix = defn["body"]
    if system_suffix:
        suffix += "\n\n" + system_suffix

    payload = {
        "workspace": {"working_dir": str(ROOT), "kind": "LocalWorkspace"},
        "agent_settings": {
            "schema_version": 10, "agent_kind": "openhands", "agent": "CodeActAgent",
            "llm": llm_config(),
            "tools": [{"name": t, "params": {}} for t in use_tools],
            "agent_context": {"system_message_suffix": suffix},
        },
        "secrets_encrypted": True,
        "initial_message": {"role": "user",
                            "content": [{"type": "text", "text": task}], "run": True},
        "max_iterations": max_iterations,
        "autotitle": False,
        "title": f"{agent}: {task[:60]}",
    }
    created = api("/api/conversations", payload, method="POST", timeout=60)
    cid = created["id"]

    started = time.time()
    status = "unknown"
    while time.time() - started < timeout_s:
        info = api(f"/api/conversations/{cid}", timeout=30)
        status = info.get("execution_status")
        if status in ("finished", "error", "stopped", "idle"):
            break
        time.sleep(4)

    result = api(f"/api/conversations/{cid}/agent_final_response", timeout=60)
    out = {"agent": agent, "conversation_id": cid, "status": status,
           "elapsed_s": round(time.time() - started, 1),
           "result": result.get("response", "")}
    log_task({**out, "task": task, "at": now()})
    return out


# ── reporting ────────────────────────────────────────────────────────

def status() -> dict:
    r = load_roster()
    agents = r["agents"]
    subs = api("/api/sub-agents", {"project_dir": str(ROOT)}, method="POST", timeout=30)
    tasks = []
    if TASKS_LOG.exists():
        tasks = [json.loads(l) for l in TASKS_LOG.read_text().splitlines() if l.strip()]
    by_status: dict[str, int] = {}
    for t in tasks:
        by_status[t.get("status", "?")] = by_status.get(t.get("status", "?"), 0) + 1
    return {
        "company": r.get("company"),
        "agents_total": len(agents),
        "agents_active": sum(1 for a in agents.values() if a["status"] == "active"),
        "departments": sorted({a["department"] for a in agents.values()}),
        "registered_sub_agents": [a["name"] for a in subs.get("agents", [])],
        "tasks_logged": len(tasks),
        "tasks_by_status": by_status,
        "last_task": tasks[-1] if tasks else None,
    }


def health() -> dict:
    checks = []
    try:
        info = api("/server_info", timeout=20)
        checks.append({"check": "agent_server", "ok": True,
                       "detail": f"v{info.get('version')} sdk {info.get('sdk_version')}"})
    except SystemExit as e:
        checks.append({"check": "agent_server", "ok": False, "detail": str(e)[:200]})
    try:
        api("/api/conversations/count", timeout=20)
        checks.append({"check": "api_auth", "ok": True, "detail": "authenticated"})
    except SystemExit as e:
        checks.append({"check": "api_auth", "ok": False, "detail": str(e)[:200]})
    try:
        llm_config()
        checks.append({"check": "llm_config", "ok": True, "detail": "resolved"})
    except SystemExit as e:
        checks.append({"check": "llm_config", "ok": False, "detail": str(e)[:200]})
    try:
        subs = api("/api/sub-agents", {"project_dir": str(ROOT)}, method="POST", timeout=20)
        checks.append({"check": "agent_discovery", "ok": True,
                       "detail": f"{len(subs.get('agents', []))} agents"})
    except SystemExit as e:
        checks.append({"check": "agent_discovery", "ok": False, "detail": str(e)[:200]})
    for p in (ROSTER, ROOT / "company" / "IDENTITY.md", ROOT / "company" / "CEO_CHARTER.md"):
        checks.append({"check": f"file:{p.name}", "ok": p.exists(),
                       "detail": "present" if p.exists() else "MISSING"})
    clean, offenders = scan_secrets()
    checks.append({"check": "no_plaintext_secrets", "ok": clean,
                   "detail": f"{len(offenders)} suspicious files"})
    return {"checks": checks, "ok": all(c["ok"] for c in checks)}


SECRET_PATTERNS = [
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), "telegram_bot_token"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "github_token"),
    (re.compile(r"\b(sk|pk)-[A-Za-z0-9]{20,}\b"), "api_key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private_key"),
    (re.compile(r"\b0x[a-fA-F0-9]{64}\b"), "evm_private_key"),
    (re.compile(r"\b([0-9a-f]{64})\b(?=.*\b(seed|mnemonic|private))\b",
                re.IGNORECASE), "hex_seed"),
]

# Public, non-secret values that must never trip the scanner.
# A TRC20/TRON *receive* address is public by design; the well-known USDT
# contract address is public and appears in the wallet module legitimately.
SCAN_ALLOWLIST = {
    "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",  # USDT TRC20 contract (public)
}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".whl",
               ".pyc", ".so", ".bin"}
# Scanners must contain the very patterns they look for; flagging them is noise.
SKIP_FILES = {
    "ops/astra.py",
    "ops/tests/run_tests.py",
    "deliveries/astra-trading/security/secret_scan.sh",
}


def scan_secrets() -> tuple[bool, list[str]]:
    """Return (clean, offenders) for tracked text files."""
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIX:
            continue
        if str(path.relative_to(ROOT)) in SKIP_FILES:
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for allowed in SCAN_ALLOWLIST:
            text = text.replace(allowed, "<allowlisted-public-value>")
        for rx, label in SECRET_PATTERNS:
            if rx.search(text):
                offenders.append(f"{path.relative_to(ROOT)}:{label}")
    return (not offenders, offenders)


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(prog="astra")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("env")
    sub.add_parser("roster")
    sub.add_parser("status")
    sub.add_parser("health")
    sub.add_parser("tasks")
    sub.add_parser("scan-secrets")

    h = sub.add_parser("hire")
    h.add_argument("name")
    h.add_argument("--dept", default="unassigned")
    h.add_argument("--reports-to", default="astra-ceo")
    h.add_argument("--tools", default="")
    h.add_argument("--description", default="")

    f = sub.add_parser("fire")
    f.add_argument("name")
    f.add_argument("--reason", default="retired by CEO")

    p = sub.add_parser("purge")
    p.add_argument("name")

    s = sub.add_parser("spawn")
    s.add_argument("agent")
    s.add_argument("task")
    s.add_argument("--max-iterations", type=int, default=40)
    s.add_argument("--timeout", type=int, default=900)

    a = ap.parse_args()

    if a.cmd == "env":
        url, key = runtime()
        info = api("/server_info")
        print(json.dumps({
            "runtime_url": url,
            "session_key_len": len(key),
            "server_version": info.get("version"),
            "sdk_version": info.get("sdk_version"),
            "conversation_runtime": info.get("conversation_runtime"),
            "capabilities": info.get("capabilities"),
            "usable_tools": info.get("usable_tools"),
            "max_foreground_terminal_timeout_seconds": info.get("max_foreground_terminal_timeout_seconds"),
        }, indent=2))
    elif a.cmd == "roster":
        print(json.dumps(load_roster(), indent=2, ensure_ascii=False))
    elif a.cmd == "hire":
        tools = [t for t in a.tools.split(",") if t] or None
        print(json.dumps(hire(a.name, a.dept, a.reports_to, tools,
                              description=a.description), indent=2, ensure_ascii=False))
    elif a.cmd == "fire":
        fire(a.name, a.reason)
        print(f"retired {a.name}")
    elif a.cmd == "purge":
        purge(a.name)
        print(f"purged {a.name} from roster")
    elif a.cmd == "spawn":
        print(json.dumps(spawn(a.agent, a.task, a.max_iterations,
                               timeout_s=a.timeout), indent=2, ensure_ascii=False))
    elif a.cmd == "status":
        print(json.dumps(status(), indent=2, ensure_ascii=False))
    elif a.cmd == "health":
        hres = health()
        print(json.dumps(hres, indent=2, ensure_ascii=False))
        sys.exit(0 if hres["ok"] else 1)
    elif a.cmd == "tasks":
        if TASKS_LOG.exists():
            for line in TASKS_LOG.read_text().splitlines():
                t = json.loads(line)
                print(f"{t['at']}  {t['agent']:22} {t['status']:9} {t['elapsed_s']:>7}s  {t['task'][:70]}")
    elif a.cmd == "scan-secrets":
        clean, offenders = scan_secrets()
        print(json.dumps({"clean": clean, "offenders": offenders}, indent=2))
        sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
