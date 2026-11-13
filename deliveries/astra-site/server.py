#!/usr/bin/env python3
"""AI ASTRA AGENCY — site server.

Serves the static site and a real contact endpoint that emails the company
mailbox (Gmail SMTP, credentials from the OpenHands secret store; never written
to disk or logged).

Run:  python3 server.py            (listens on 0.0.0.0:8080)
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "ops"))
import secrets as _secrets  # noqa: E402

PORT = int(os.environ.get("ASTRA_SITE_PORT", "8080"))
MAX_BODY = 16 * 1024
RATE_WINDOW = 60.0
RATE_MAX = 5
_hits: dict[str, list[float]] = {}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _mailbox() -> str | None:
    return _secrets.resolve("ASTRA_GMAIL_ADDRESS")


def _credential() -> str | None:
    return (_secrets.resolve("ASTRA_GMAIL_APP_PASSWORD")
            or _secrets.resolve("ASTRA_GMAIL_OAUTH_TOKEN"))


def _rate_ok(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    hits.append(now)
    _hits[ip] = hits
    return len(hits) <= RATE_MAX


def _send(name: str, email: str, subject: str, message: str) -> None:
    msg = EmailMessage()
    msg["From"] = _mailbox()
    msg["To"] = _mailbox()
    msg["Reply-To"] = email
    msg["Subject"] = f"[Site] {subject or 'New enquiry'}"
    msg.set_content(
        f"New enquiry from the AI ASTRA AGENCY website.\n\n"
        f"Name:    {name}\n"
        f"Email:   {email}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as s:
        s.login(_mailbox(), _credential())
        s.send_message(msg)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):  # keep logs quiet & secret-free
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.rstrip("/") != "/api/contact":
            self._json(404, {"ok": False, "error": "not found"})
            return
        ip = self.client_address[0]
        if not _rate_ok(ip):
            self._json(429, {"ok": False, "error": "too many requests"})
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BODY:
            self._json(413, {"ok": False, "error": "bad payload size"})
            return
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "invalid json"})
            return
        name = str(data.get("name", "")).strip()[:120]
        email = str(data.get("email", "")).strip()[:200]
        subject = str(data.get("subject", "")).strip()[:160]
        message = str(data.get("message", "")).strip()[:4000]
        if not name or not _EMAIL_RE.match(email) or not message:
            self._json(400, {"ok": False, "error": "name, valid email and message are required"})
            return
        if not (_mailbox() and _credential()):
            self._json(503, {"ok": False, "error": "mail not configured"})
            return
        try:
            _send(name, email, subject, message)
        except Exception as exc:  # noqa: BLE001
            print(f"contact send failed: {type(exc).__name__}", file=sys.stderr)
            self._json(502, {"ok": False, "error": "could not send, try again later"})
            return
        self._json(200, {"ok": True})


def main() -> None:
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"AI ASTRA AGENCY site on http://0.0.0.0:{PORT} "
          f"(mail configured: {bool(_mailbox() and _credential())})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
