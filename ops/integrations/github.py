#!/usr/bin/env python3
"""GitHub integration. Live-testable now with the runtime GITHUB_TOKEN."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"


def token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("OH_GIT_CREDENTIAL_ACCESS_TOKEN_GITHUB")


def _req(path: str, method: str = "GET", payload: dict | None = None):
    t = token()
    if not t:
        raise RuntimeError("GITHUB_TOKEN not set")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Authorization": f"Bearer {t}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "astra-agency"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def whoami() -> dict:
    code, d = _req("/user")
    return {"ok": code == 200, "login": d.get("login"), "type": d.get("type"),
            "name": d.get("name"), "status": code}


def create_private_repo(name: str, description: str = "") -> dict:
    code, d = _req("/user/repos", "POST", {
        "name": name, "description": description, "private": True,
        "auto_init": True, "has_issues": True, "has_wiki": False,
    })
    return {"ok": code in (201, 422), "status": code,
            "full_name": d.get("full_name"), "private": d.get("private"),
            "created": code == 201, "error": d.get("message") if code not in (201, 422) else None}


def repo_exists(full_name: str) -> bool:
    code, _ = _req(f"/repos/{full_name}")
    return code == 200


def list_repos() -> list[dict]:
    code, d = _req("/user/repos?per_page=100&affiliation=owner")
    if code != 200 or not isinstance(d, list):
        return []
    return [{"full_name": r["full_name"], "private": r["private"],
             "default_branch": r["default_branch"]} for r in d]


if __name__ == "__main__":
    print(json.dumps({"identity": whoami(), "repos": list_repos()}, indent=2))
