#!/usr/bin/env python3
"""Gmail integration — prepared, awaiting Owner-provisioned credentials.

Credentials resolve from the OpenHands secret store (Settings > Secrets) or from
environment variables. They are read into memory only, never written to disk.
Supports IMAP/SMTP with an app password, or OAuth2 access tokens.
"""
from __future__ import annotations

import email
import imaplib
import json
import sys
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import secrets as _secrets  # noqa: E402

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"


def _addr() -> str | None:
    return _secrets.resolve("ASTRA_GMAIL_ADDRESS")


def _secret() -> str | None:
    return (_secrets.resolve("ASTRA_GMAIL_APP_PASSWORD")
            or _secrets.resolve("ASTRA_GMAIL_OAUTH_TOKEN"))


def configured() -> bool:
    return bool(_addr() and _secret())


def test_connection() -> dict:
    if not configured():
        return {"ok": False, "reason": "not configured (need ASTRA_GMAIL_ADDRESS + ASTRA_GMAIL_APP_PASSWORD)"}
    try:
        m = imaplib.IMAP4_SSL(IMAP_HOST)
        m.login(_addr(), _secret())
        status, data = m.select("INBOX")
        count = data[0].decode() if data and data[0] else "?"
        m.logout()
        return {"ok": status == "OK", "inbox_messages": count}
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}


def list_recent(limit: int = 10) -> list[dict]:
    if not configured():
        raise RuntimeError("Gmail not configured")
    m = imaplib.IMAP4_SSL(IMAP_HOST)
    m.login(_addr(), _secret())
    m.select("INBOX")
    _, data = m.search(None, "ALL")
    ids = data[0].split()[-limit:]
    out = []
    for i in reversed(ids):
        _, msg_data = m.fetch(i, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        out.append({"from": msg.get("From"), "subject": msg.get("Subject"),
                    "date": msg.get("Date")})
    m.logout()
    return out


def send(to: str, subject: str, body: str) -> dict:
    if not configured():
        raise RuntimeError("Gmail not configured")
    msg = MIMEText(body)
    msg["From"] = _addr()
    msg["To"] = to
    msg["Subject"] = subject
    with smtplib.SMTP_SSL(SMTP_HOST, 465) as s:
        s.login(_addr(), _secret())
        s.send_message(msg)
    return {"ok": True, "to": to}


if __name__ == "__main__":
    print(json.dumps({"configured": configured(), "test": test_connection()}, indent=2))
