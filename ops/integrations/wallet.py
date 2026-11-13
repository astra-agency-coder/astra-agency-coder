#!/usr/bin/env python3
"""Wallet integration — USDT (TRC20) receive-only verification.

Never holds keys, never signs, never transfers. Only reads the chain to verify
incoming payments. Verification is on-chain only; screenshots and chat links are
never accepted as proof.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import secrets as _secrets  # noqa: E402

TRONGRID = "https://api.trongrid.io"
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
REQUIRED_CONFIRMATIONS = 19  # TRON solidity (irreversible) block depth


def address() -> str | None:
    v = _secrets.resolve("ASTRA_WALLET_USDT_TRC20") or os.environ.get(
        "ASTRA_WALLET_USDT_TRC20")
    return v.strip() if v else None


def configured() -> bool:
    return bool(address())


def _req(path: str):
    req = urllib.request.Request(
        TRONGRID + path,
        headers={"Accept": "application/json", "User-Agent": "astra-agency"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def validate_address(addr: str) -> bool:
    """A TRON base58 address is 34 chars and starts with 'T'."""
    if not addr or len(addr) != 34 or not addr.startswith("T"):
        return False
    code, d = _req(f"/v1/accounts/{addr}")
    if code != 200:
        return False
    data = d.get("data")
    return isinstance(data, list)


def verify_payment(txid: str, expected_amount: float,
                   min_confirmations: int = REQUIRED_CONFIRMATIONS) -> dict:
    """Verify a TRC20 USDT payment on-chain. Returns a verdict with evidence."""
    addr = address()
    if not addr:
        return {"verified": False, "reason": "wallet address not configured"}
    if not txid or len(txid) != 64:
        return {"verified": False, "reason": "malformed txid"}

    code, d = _req(f"/v1/transactions/{txid}")
    if code != 200:
        return {"verified": False, "reason": f"trongrid http {code}"}

    # TRC20 transfers appear in trc20TransferInfo for the transaction's contract.
    transfers = []
    for item in (d.get("data") or []):
        for t in (item.get("trc20TransferInfo") or []):
            transfers.append(t)

    match = None
    for t in transfers:
        to_addr = t.get("to_address")
        contract = t.get("contract_address")
        if to_addr == addr and contract == USDT_TRC20_CONTRACT:
            match = t
            break
    if not match:
        return {"verified": False,
                "reason": "no USDT transfer to our address found in this txid",
                "transfers_seen": len(transfers)}

    raw = int(match.get("amount", "0"))
    amount = raw / 10**6  # USDT has 6 decimals
    block = d.get("blockNumber") or (d.get("data") or [{}])[0].get("blockNumber")
    now_block = _latest_block()
    confs = max(0, now_block - int(block)) if block and now_block else 0

    amount_ok = abs(amount - expected_amount) < 1e-6
    confs_ok = confs >= min_confirmations
    return {
        "verified": bool(amount_ok and confs_ok),
        "address_match": True,
        "currency": "USDT",
        "network": "TRC20",
        "amount": amount,
        "expected_amount": expected_amount,
        "amount_ok": amount_ok,
        "confirmations": confs,
        "required_confirmations": min_confirmations,
        "confirmations_ok": confs_ok,
        "txid": txid,
    }


def _latest_block() -> int | None:
    code, d = _req("/wallet/getnowblock")
    if code != 200:
        return None
    return (d.get("block_header") or {}).get("raw_data", {}).get("number")


if __name__ == "__main__":
    print(json.dumps({"configured": configured(), "address_set": bool(address())}, indent=2))
