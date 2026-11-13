#!/usr/bin/env python3
"""Report live status of every integration. Run before any Owner report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github  # noqa: E402
import gmail  # noqa: E402
import telegram  # noqa: E402
import wallet  # noqa: E402


def status() -> dict:
    out = {}

    try:
        ident = github.whoami()
        ident.pop("status", None)
        out["github"] = {"status": "CONNECTED" if ident.get("ok") else "FAIL",
                         **ident, "repos": github.list_repos()}
    except Exception as e:
        out["github"] = {"status": "FAIL", "reason": str(e)}

    tc = telegram.configured()
    out["telegram"] = {"status": "PREPARED" if not tc["bot_token_set"] else "CONNECTED",
                       "bot_token_set": tc["bot_token_set"],
                       "owner_id_set": tc["owner_id_set"]}
    if tc["bot_token_set"]:
        out["telegram"]["get_me"] = telegram.get_me()

    out["gmail"] = {"status": "CONNECTED" if gmail.configured() else "NEEDS OWNER ACTION",
                    "configured": gmail.configured()}
    out["wallet"] = {"status": "CONNECTED" if wallet.configured() else "NEEDS OWNER ACTION",
                     "networks": wallet.networks(),
                     "primary": wallet.primary()}
    return out


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
