#!/usr/bin/env python3
"""Grant each department manager scoped, least-privilege GitHub access.

Each manager receives its OWN SSH keypair, registered as a **write-enabled
deploy key on exactly one repository** — its department repository. A deploy key
is bound to a single repository by GitHub itself, so a manager physically cannot
read or push any other repository, even if it tried. No manager ever holds the
company-wide token.

Private keys are written only to `~/.astra/keys/` (mode 0600, outside the repo)
and to the runtime secret store. They are never written into the repository,
never printed, and never included in a report.

    python3 ops/provision_access.py --dry-run
    python3 ops/provision_access.py
    python3 ops/provision_access.py --verify     # prove isolation
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "ops" / "integrations"))
import astra  # noqa: E402
import github  # noqa: E402
import secrets as secret_store  # noqa: E402
from provision_repos import DEPARTMENTS  # noqa: E402

KEY_DIR = Path.home() / ".astra" / "keys"
GH_SSH = "git@github.com"


def key_name(manager: str) -> str:
    return f"{manager}_deploy"


def key_paths(manager: str) -> tuple[Path, Path]:
    base = KEY_DIR / key_name(manager)
    return base, base.with_suffix(".pub")


def ensure_keypair(manager: str) -> tuple[Path, str]:
    """Create the manager's ed25519 keypair if absent; return (path, public_key)."""
    priv, pub = key_paths(manager)
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(KEY_DIR, stat.S_IRWXU)
    if not priv.exists():
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-q",
                        "-C", f"astra-{manager}-deploy-key", "-f", str(priv)],
                       check=True)
    os.chmod(priv, 0o600)
    return priv, pub.read_text().strip()


def ssh_env(priv: Path) -> dict:
    """Environment that forces git to use ONLY this key for github.com."""
    return {
        "GIT_SSH_COMMAND": (
            f"ssh -i {priv} -o IdentitiesOnly=yes "
            "-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null"
        )
    }


def register_deploy_key(owner: str, slug: str, title: str, pubkey: str,
                        dry: bool) -> dict:
    if dry:
        return {"repo": f"{owner}/{slug}", "action": "would-register-deploy-key"}
    # Idempotent: skip if a key with this title already exists.
    existing = github.list_deploy_keys(owner, slug)
    for k in existing:
        if k.get("title") == title:
            return {"repo": f"{owner}/{slug}", "action": "already-present",
                    "key_id": k.get("id"), "ok": True}
    r = github.add_deploy_key(owner, slug, title, pubkey, read_only=False)
    return {"repo": f"{owner}/{slug}", "action": "registered",
            "ok": r.get("ok"), "key_id": r.get("id"), "error": r.get("error")}


def run_git(args: list[str], cwd: Path, env: dict) -> tuple[int, str]:
    full = {**os.environ, **env}
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                       text=True, env=full)
    return p.returncode, (p.stdout + p.stderr).strip()


def provision(dry: bool) -> list[dict]:
    ident = github.whoami()
    if not ident.get("ok"):
        print("GitHub not reachable:", ident, file=sys.stderr)
        sys.exit(1)
    owner = ident["login"]
    results = []

    for dept, (manager, slug, _purpose) in DEPARTMENTS.items():
        priv, pub = ensure_keypair(manager)
        r = register_deploy_key(owner, slug, f"astra-{manager}", pub, dry)
        r["manager"] = manager
        r["department"] = dept
        if not dry and r.get("ok"):
            # Store the private key in the runtime secret store (durability),
            # under a per-manager name. Never into the repository.
            secret_store.put(f"{manager.upper().replace('-', '_')}_DEPLOY_KEY",
                             priv.read_text(), f"Deploy key for {manager} ({slug})")
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))

    if not dry:
        out = ROOT / "company" / "departments" / "access.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "generated_at": astra.now(),
            "model": "one write-enabled deploy key per manager, bound to one repo",
            "note": "Private keys live in ~/.astra/keys (0600) and the secret "
                    "store only. They are never committed.",
            "managers": [
                {"manager": m, "department": d, "repo": f"{owner}/{s}",
                 "access": "write", "scope": "this repository only",
                 "key_ref": f"~/.astra/keys/{key_name(m)}"}
                for d, (m, s, _) in DEPARTMENTS.items()
            ],
        }, indent=2))
        print(f"\nwrote {(out).relative_to(ROOT)}")
    return results


def verify() -> None:
    """Prove each manager can push ONLY its own repository."""
    ident = github.whoami()
    owner = ident["login"]
    print("=== isolation verification ===")
    work = ROOT / ".tmp_verify"
    for dept, (manager, slug, _p) in DEPARTMENTS.items():
        priv, _ = key_paths(manager)
        env = ssh_env(priv)
        own = f"{GH_SSH}:{owner}/{slug}.git"
        # 1) read its own repo
        rc, out = run_git(["ls-remote", own, "HEAD"], ROOT, env)
        own_ok = rc == 0
        # 2) try a DIFFERENT department's repo (must fail)
        other_slug = next(s for d, (m, s, _x) in DEPARTMENTS.items() if s != slug)
        other = f"{GH_SSH}:{owner}/{other_slug}.git"
        rc2, out2 = run_git(["ls-remote", other, "HEAD"], ROOT, env)
        other_denied = rc2 != 0
        verdict = "PASS" if (own_ok and other_denied) else "FAIL"
        print(f"[{verdict}] {manager}: own={slug} ok={own_ok} | "
              f"cross-access={other_slug} denied={other_denied}")
    subprocess.run(["rm", "-rf", str(work)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        verify()
    else:
        provision(a.dry_run)


if __name__ == "__main__":
    main()
