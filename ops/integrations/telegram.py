#!/usr/bin/env python3
"""Telegram integration — CEO <-> Owner channel with a strict Owner allowlist.

Security rules (enforced in code, not just policy):
- Only `ASTRA_OWNER_TELEGRAM_ID` may issue commands. Everything else is rejected.
- Never send passwords, keys or recovery phrases.
- Messages are batched; no notification per routine step.
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

API = "https://api.telegram.org"


def _token() -> str | None:
    return _secrets.resolve("ASTRA_TELEGRAM_BOT_TOKEN")


def _owner_id() -> str | None:
    v = _secrets.resolve("ASTRA_OWNER_TELEGRAM_ID")
    return str(v).strip() if v else None


def configured() -> dict:
    return {"bot_token_set": bool(_token()), "owner_id_set": bool(_owner_id())}


def _call(method: str, payload: dict, timeout: int = 30) -> dict:
    t = _token()
    if not t:
        raise RuntimeError("ASTRA_TELEGRAM_BOT_TOKEN not set")
    req = urllib.request.Request(
        f"{API}/bot{t}/{method}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode()[:300]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def get_me() -> dict:
    return _call("getMe", {})


def get_updates(offset: int | None = None, timeout: int = 0) -> dict:
    """Long-poll updates. Used to discover the Owner's chat id from their /start."""
    payload: dict = {"timeout": timeout}
    if offset is not None:
        payload["offset"] = offset
    return _call("getUpdates", payload, timeout=max(30, timeout + 10))


def send(text: str) -> dict:
    """Send to the Owner only. Refuses if no allowlisted Owner id is configured."""
    oid = _owner_id()
    if not oid:
        raise RuntimeError("ASTRA_OWNER_TELEGRAM_ID not set — refusing to send")
    if _looks_secret(text):
        raise RuntimeError("refusing to send text that looks like a secret")
    return _call("sendMessage", {"chat_id": oid, "text": text,
                                 "disable_web_page_preview": True})


def is_authorized(sender_id: int | str) -> bool:
    oid = _owner_id()
    return oid is not None and str(sender_id).strip() == oid


def handle_update(update: dict) -> dict:
    """Route one incoming update. Non-Owner senders are rejected and logged."""
    msg = update.get("message") or update.get("edited_message") or {}
    sender = (msg.get("from") or {}).get("id")
    text = msg.get("text", "")
    if sender is None:
        return {"handled": False, "reason": "no sender"}
    if not is_authorized(sender):
        return {"handled": False, "reason": "unauthorized sender", "sender": sender}
    return {"handled": True, "authorized": True, "sender": sender, "text": text}


_SECRET_HINTS = ("password", "passwd", "private key", "seed phrase",
                 "recovery code", "mnemonic", "2fa code", "otp code",
                 "api key", "apikey", "api_key", "secret", "token",
                 "credential", "private_key")


def _looks_secret(text: str) -> bool:
    low = text.lower()
    return any(h in low for h in _SECRET_HINTS)


def _multipart(method: str, fields: dict, file_field: str, path: Path,
               timeout: int = 300) -> dict:
    """POST a file (and simple fields) to Telegram using multipart/form-data."""
    t = _token()
    if not t:
        raise RuntimeError("ASTRA_TELEGRAM_BOT_TOKEN not set")
    boundary = "----AstraBoundary" + os.urandom(16).hex()
    parts: list[bytes] = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{k}"\r\n\r\n{v}\r\n'.encode())
    data = path.read_bytes()
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                 f'name="{file_field}"; filename="{path.name}"\r\n'
                 f"Content-Type: application/octet-stream\r\n\r\n".encode())
    parts.append(data)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{API}/bot{t}/{method}", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode()[:400]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def send_document(path: str | Path, caption: str = "") -> dict:
    """Send a file to the Owner only. Refuses non-files or secret-looking captions."""
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"not a file: {p}")
    if caption and _looks_secret(caption):
        raise RuntimeError("refusing to send a caption that looks like a secret")
    oid = _owner_id()
    if not oid:
        raise RuntimeError("ASTRA_OWNER_TELEGRAM_ID not set — refusing to send")
    return _multipart("sendDocument", {"chat_id": oid, "caption": caption[:1000]},
                      "document", p)


def send_video(path: str | Path, caption: str = "") -> dict:
    """Send a video to the Owner only (falls back to document on failure)."""
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"not a file: {p}")
    if caption and _looks_secret(caption):
        raise RuntimeError("refusing to send a caption that looks like a secret")
    oid = _owner_id()
    if not oid:
        raise RuntimeError("ASTRA_OWNER_TELEGRAM_ID not set — refusing to send")
    r = _multipart("sendVideo", {"chat_id": oid, "caption": caption[:1000],
                                 "supports_streaming": "true"}, "video", p)
    if not r.get("ok"):
        r = send_document(p, caption)
    return r


def send_photo(path: str | Path, caption: str = "") -> dict:
    """Send a photo to the Owner only (falls back to document on failure)."""
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"not a file: {p}")
    if caption and _looks_secret(caption):
        raise RuntimeError("refusing to send a caption that looks like a secret")
    oid = _owner_id()
    if not oid:
        raise RuntimeError("ASTRA_OWNER_TELEGRAM_ID not set — refusing to send")
    r = _multipart("sendPhoto", {"chat_id": oid, "caption": caption[:1000]},
                   "photo", p)
    if not r.get("ok"):
        r = send_document(p, caption)
    return r


if __name__ == "__main__":
    print(json.dumps({"configured": configured(),
                      "get_me": get_me() if configured()["bot_token_set"] else "not configured"},
                     indent=2))
