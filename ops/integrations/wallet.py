#!/usr/bin/env python3
"""Wallet integration — multi-network, receive-only payment verification.

Never holds keys, never signs, never transfers, never spends. It only reads
public blockchains to confirm incoming payments. A payment is confirmed on-chain
evidence only — a screenshot or chat link is never proof.

Supported networks (one registry entry per chain, see company/finance/wallets.json):
  usdt-trc20  Tron (TRC20)      TronGrid
  usdt-bep20  BNB Smart Chain   public BSC RPC
  ethereum    Ethereum (ERC20)  public ETH RPC
  solana      Solana            public Solana RPC
  bitcoin     Bitcoin           mempool.space

Addresses are PUBLIC data and live in company/finance/wallets.json. They are not
secrets. The module still refuses to store or expose any key material.
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

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = ROOT / "company" / "finance" / "wallets.json"

TRONGRID = "https://api.trongrid.io"
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
REQUIRED_CONFIRMATIONS = 19  # TRON solidity (irreversible) block depth

BSC_RPC = "https://bsc-dataseed.binance.org/"
ETH_RPC = "https://ethereum-rpc.publicnode.com"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
MEMPOOL = "https://mempool.space/api"

# USDT contract address + decimals per EVM chain
EVM_USDT = {
    "usdt-bep20": ("0x55d398326f99059ff775485246999027b3197955", 18),
    "ethereum": ("0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
}
SOLANA_USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"


# ── registry ─────────────────────────────────────────────────────────
def registry() -> dict:
    if not REGISTRY.exists():
        return {}
    return json.loads(REGISTRY.read_text()).get("wallets", {})


def networks() -> list[str]:
    return sorted(registry().keys())


def address_for(network: str) -> str | None:
    """Resolve an address from the registry, or the TRC20 secret override."""
    if network == "usdt-trc20":
        override = _secrets.resolve("ASTRA_WALLET_USDT_TRC20")
        if override and override.strip():
            return override.strip()
    return (registry().get(network) or {}).get("address")


def primary() -> tuple[str, str] | None:
    reg = registry()
    for name, w in reg.items():
        if w.get("primary"):
            return name, w["address"]
    if reg:
        name = next(iter(reg))
        return name, reg[name]["address"]
    return None


def configured() -> bool:
    return bool(primary())


# ── low-level requests ───────────────────────────────────────────────
def _http(url: str, data: bytes | None = None, headers: dict | None = None):
    req = urllib.request.Request(url, data=data,
                                 headers={"Accept": "application/json",
                                          "User-Agent": "astra-agency",
                                          **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            try:
                return r.status, json.loads(body)
            except json.JSONDecodeError:
                return r.status, {"raw": body.decode(errors="replace")[:300]}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:300]}
    except Exception as e:  # noqa: BLE001
        return None, {"error": str(e)[:300]}


def _rpc(url: str, method: str, params: list):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    code, d = _http(url, data=body, headers={"Content-Type": "application/json"})
    if code is None or ("error" in d and "result" not in d):
        return None
    return d.get("result")


# ── address validation ───────────────────────────────────────────────
def validate_address(network: str, addr: str) -> bool:
    """Format check plus a live read where the chain allows it."""
    addr = (addr or "").strip()
    if network == "usdt-trc20":
        if len(addr) != 34 or not addr.startswith("T"):
            return False
        code, _ = _http(f"{TRONGRID}/v1/accounts/{addr}")
        return code == 200
    if network in EVM_USDT:
        if len(addr) != 42 or not addr.startswith("0x"):
            return False
        rpc = BSC_RPC if network == "usdt-bep20" else ETH_RPC
        return _rpc(rpc, "eth_getBalance", [addr, "latest"]) is not None
    if network == "solana":
        if not (32 <= len(addr) <= 44):
            return False
        res = _rpc(SOLANA_RPC, "getBalance",
                   [addr, {"commitment": "confirmed"}])
        # Newer RPC returns {"context":…, "value":…}; older returns an int.
        if isinstance(res, dict):
            return isinstance(res.get("value"), int)
        return isinstance(res, int)
    if network == "bitcoin":
        if not (addr.startswith("bc1") and 42 <= len(addr) <= 62):
            return False
        code, d = _http(f"{MEMPOOL}/address/{addr}")
        return code == 200 and isinstance(d, dict) and "chain_stats" in d
    return False


def validate_all() -> dict:
    """Validate every registered network and return per-network results."""
    out = {}
    for name, w in registry().items():
        out[name] = {"address": w["address"],
                     "valid": validate_address(name, w["address"])}
    return out


# ── payment verification ─────────────────────────────────────────────
def verify_payment(txid: str, expected_amount: float,
                   network: str = "usdt-trc20",
                   min_confirmations: int = REQUIRED_CONFIRMATIONS) -> dict:
    """Verify an incoming payment on `network`. Returns a verdict with evidence."""
    addr = address_for(network)
    if not addr:
        return {"verified": False, "network": network,
                "reason": f"no address registered for {network}"}
    if network == "usdt-trc20":
        return _verify_trc20(txid, expected_amount, addr, min_confirmations)
    if network in EVM_USDT:
        return _verify_evm(txid, expected_amount, network, addr, min_confirmations)
    if network == "solana":
        return _verify_solana(txid, expected_amount, addr)
    if network == "bitcoin":
        return _verify_bitcoin(txid, expected_amount, addr, min_confirmations)
    return {"verified": False, "reason": f"unsupported network {network}"}


def _verify_trc20(txid, expected, addr, min_conf) -> dict:
    if not txid or len(txid) != 64:
        return {"verified": False, "reason": "malformed txid", "network": "TRC20"}
    code, d = _http(f"{TRONGRID}/v1/transactions/{txid}")
    if code != 200:
        return {"verified": False, "network": "TRC20",
                "reason": f"trongrid http {code}"}
    transfers = [t for item in (d.get("data") or [])
                 for t in (item.get("trc20TransferInfo") or [])]
    match = next((t for t in transfers if t.get("to_address") == addr
                  and t.get("contract_address") == USDT_TRC20_CONTRACT), None)
    if not match:
        return {"verified": False, "network": "TRC20",
                "reason": "no USDT transfer to our address in this txid",
                "transfers_seen": len(transfers)}
    amount = int(match.get("amount", "0")) / 10**6
    block = d.get("blockNumber") or (d.get("data") or [{}])[0].get("blockNumber")
    now = _latest_tron_block()
    confs = max(0, now - int(block)) if block and now else 0
    return _verdict("USDT", "TRC20", addr, amount, expected, confs, min_conf, txid)


def _verify_evm(txid, expected, network, addr, min_conf) -> dict:
    contract, decimals = EVM_USDT[network]
    if not txid or len(txid) != 66 or not txid.startswith("0x"):
        return {"verified": False, "reason": "malformed txid", "network": network}
    rpc = BSC_RPC if network == "usdt-bep20" else ETH_RPC
    transfer_topic = ("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f"
                      "55a4df523b3ef")
    rec = _rpc(rpc, "eth_getTransactionReceipt", [txid])
    if not rec:
        return {"verified": False, "reason": "tx not found", "network": network}
    target = "0x" + addr[2:].lower().rjust(64, "0")
    amount = None
    for log in rec.get("logs", []):
        topics = log.get("topics", [])
        if (log.get("address", "").lower() == contract
                and topics and topics[0] == transfer_topic
                and len(topics) >= 3 and topics[2].lower() == target):
            amount = int(log["data"], 16) / 10**decimals
            break
    if amount is None:
        return {"verified": False, "network": network,
                "reason": "no USDT transfer to our address in this txid"}
    latest = _rpc(rpc, "eth_blockNumber", [])
    confs = max(0, int(latest, 16) - int(rec["blockNumber"], 16)) if latest else 0
    return _verdict("USDT", network, addr, amount, expected, confs, min_conf, txid)


def _verify_solana(txid, expected, addr) -> dict:
    if not txid or len(txid) < 40:
        return {"verified": False, "network": "solana",
                "reason": "malformed signature"}
    tx = _rpc(SOLANA_RPC, "getTransaction",
              [txid, {"encoding": "jsonParsed",
                      "maxSupportedTransactionVersion": 0}])
    if not tx or "meta" not in tx:
        return {"verified": False, "reason": "tx not found", "network": "solana"}
    if tx["meta"].get("err"):
        return {"verified": False, "network": "solana",
                "reason": "tx failed on-chain"}
    amount = None
    for bal in tx["meta"].get("postTokenBalances", []):
        if bal.get("mint") == SOLANA_USDT_MINT and bal.get("owner") == addr:
            amount = bal["uiTokenAmount"]["uiAmount"]
    if amount is None:
        return {"verified": False, "network": "solana",
                "reason": "no USDT balance for our address in this tx"}
    return _verdict("USDT", "solana", addr, float(amount), expected, 1, 1, txid)


def _verify_bitcoin(txid, expected, addr, min_conf) -> dict:
    code, tx = _http(f"{MEMPOOL}/tx/{txid}")
    if code != 200 or "vout" not in tx:
        return {"verified": False, "reason": "tx not found", "network": "bitcoin"}
    got = sum(v["value"] for v in tx["vout"]
              if v.get("scriptpubkey_address") == addr)
    if not got:
        return {"verified": False, "network": "bitcoin",
                "reason": "no output to our address in this txid"}
    amount = got / 10**8  # sats -> BTC
    confs = 0
    if tx.get("status", {}).get("confirmed"):
        code, tip = _http(f"{MEMPOOL}/blocks/tip/height")
        confs = (max(0, int(tip) - tx["status"]["block_height"])
                 if code == 200 else 0)
    return _verdict("BTC", "bitcoin", addr, amount, expected, confs, min_conf, txid)


def _verdict(currency, network, addr, amount, expected, confs, min_conf, txid):
    amt_ok = abs(amount - expected) < 1e-6
    conf_ok = confs >= min_conf
    return {"verified": bool(amt_ok and conf_ok), "address_match": True,
            "currency": currency, "network": network, "address": addr,
            "amount": amount, "expected_amount": expected, "amount_ok": amt_ok,
            "confirmations": confs, "required_confirmations": min_conf,
            "confirmations_ok": conf_ok, "txid": txid}


def _latest_tron_block() -> int | None:
    code, d = _http(f"{TRONGRID}/wallet/getnowblock")
    if code != 200:
        return None
    return (d.get("block_header") or {}).get("raw_data", {}).get("number")


if __name__ == "__main__":
    print(json.dumps({"networks": networks(), "primary": primary(),
                      "configured": configured()}, indent=2))
