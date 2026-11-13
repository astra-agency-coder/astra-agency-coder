#!/usr/bin/env python3
"""Department repo tool — a manager's scoped access to its own repository.

Each manager authenticates with its OWN deploy key, which GitHub binds to a
single repository. A manager therefore cannot read or write any other repo.

    python3 ops/deptrepo.py whoami  astra-cto
    python3 ops/deptrepo.py clone   astra-cto            # -> ~/.astra/work/<slug>
    python3 ops/deptrepo.py pull    astra-cto
    python3 ops/deptrepo.py save    astra-cto "message"  # commit + push all changes
    python3 ops/deptrepo.py ls      astra-cto
    python3 ops/deptrepo.py access                       # the full access map
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "ops" / "integrations"))
import github  # noqa: E402
from provision_access import key_paths, ssh_env  # noqa: E402
from provision_repos import DEPARTMENTS  # noqa: E402

WORK = Path.home() / ".astra" / "work"

MANAGER_TO_SLUG = {m: s for _d, (m, s, _p) in DEPARTMENTS.items()}


def slug_for(manager: str) -> str:
    if manager not in MANAGER_TO_SLUG:
        sys.exit(f"unknown manager: {manager!r}. Known: {', '.join(MANAGER_TO_SLUG)}")
    return MANAGER_TO_SLUG[manager]


def workdir(manager: str) -> Path:
    return WORK / slug_for(manager)


def _run(args: list[str], cwd: Path | None, env: dict) -> tuple[int, str]:
    p = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True,
                       text=True, env={**os.environ, **env})
    return p.returncode, (p.stdout + p.stderr).strip()


def remote(manager: str) -> str:
    owner = github.whoami()["login"]
    return f"git@github.com:{owner}/{slug_for(manager)}.git"


def cmd_clone(manager: str) -> None:
    priv, _ = key_paths(manager)
    env = ssh_env(priv)
    d = workdir(manager)
    if d.exists():
        rc, out = _run(["git", "pull", "--ff-only"], d, env)
        print(f"updated {d}" if rc == 0 else out)
        return
    d.parent.mkdir(parents=True, exist_ok=True)
    rc, out = _run(["git", "clone", remote(manager), str(d)], None, env)
    if rc != 0:
        sys.exit(f"clone failed: {out}")
    _run(["git", "config", "user.email", f"{manager}@astra-agency.dev"], d, env)
    _run(["git", "config", "user.name", manager], d, env)
    print(f"cloned {slug_for(manager)} -> {d}")


def cmd_pull(manager: str) -> None:
    priv, _ = key_paths(manager)
    rc, out = _run(["git", "pull", "--ff-only"], workdir(manager), ssh_env(priv))
    print(out or "up to date")


def cmd_save(manager: str, message: str) -> None:
    priv, _ = key_paths(manager)
    env = ssh_env(priv)
    d = workdir(manager)
    _run(["git", "add", "-A"], d, env)
    rc, out = _run(["git", "commit", "-m", message], d, env)
    if "nothing to commit" in out:
        print("nothing to commit")
        return
    rc, out = _run(["git", "push", "origin", "HEAD"], d, env)
    print(out.splitlines()[-1] if out else "pushed")


def cmd_ls(manager: str) -> None:
    priv, _ = key_paths(manager)
    rc, out = _run(["git", "ls-files"], workdir(manager), ssh_env(priv))
    print(out)


def cmd_whoami(manager: str) -> None:
    priv, _ = key_paths(manager)
    rc, out = _run(["ssh", "-i", str(priv), "-o", "IdentitiesOnly=yes",
                    "-o", "StrictHostKeyChecking=accept-new",
                    "-o", "UserKnownHostsFile=/dev/null", "-T", "git@github.com"],
                   None, {})
    print(f"manager={manager} repo={slug_for(manager)}")
    print(out)


def cmd_access() -> None:
    p = ROOT / "company" / "departments" / "access.json"
    if p.exists():
        print(p.read_text())
    else:
        print("access.json not written yet; run ops/provision_access.py")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("whoami", "clone", "pull", "ls"):
        s = sub.add_parser(name)
        s.add_argument("manager")
    s = sub.add_parser("save")
    s.add_argument("manager")
    s.add_argument("message")
    sub.add_parser("access")
    a = ap.parse_args()

    if a.cmd == "access":
        cmd_access()
    elif a.cmd == "whoami":
        cmd_whoami(a.manager)
    elif a.cmd == "clone":
        cmd_clone(a.manager)
    elif a.cmd == "pull":
        cmd_pull(a.manager)
    elif a.cmd == "ls":
        cmd_ls(a.manager)
    elif a.cmd == "save":
        cmd_save(a.manager, a.message)


if __name__ == "__main__":
    main()
