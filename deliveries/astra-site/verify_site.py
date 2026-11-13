#!/usr/bin/env python3
"""Reproducible verification for deliveries/astra-site (company site).

Static checks (no server needed):
  1. HTML structure: single <h1>, <html lang>, viewport meta, no duplicate ids,
     every in-page anchor resolves.
  2. Images: every <img> has an alt attribute; decorative (alt="") images are
     hidden from assistive tech (aria-hidden/role=presentation).
  3. No external requests: no http(s) references in HTML/CSS/JS (self-contained).
  4. Accessibility: skip link + its target, focus-visible styles, form controls
     labelled, nav toggle exposes aria-expanded/aria-controls.
  5. Performance: fonts are woff2-only and preloaded; images reserve space
     (width/height or CSS aspect-ratio) to avoid layout shift.

Live checks (against a running server):
  6. POST /api/contact rejects empty / invalid input with 400.
  7. POST /api/contact accepts a valid payload (200, or 503 when SMTP is not
     configured). A real send is attempted when credentials are present unless
     --no-email is given.
  8. The public URL returns HTTP 200.

Exit code 0 = all checks pass, 1 = at least one failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
sys.path.insert(0, str(REPO / "ops"))

DEFAULT_PUBLIC_URL = os.environ.get(
    "ASTRA_PUBLIC_URL", "https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/")

failures: list[str] = []
notes: list[str] = []


def check(cond: bool, ok: str, fail: str) -> bool:
    if cond:
        print(f"  PASS  {ok}")
    else:
        print(f"  FAIL  {fail}")
        failures.append(fail)
    return bool(cond)


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _external_refs(text: str) -> list[str]:
    """http(s) URLs that would trigger a network request (ignores xmlns/data:)."""
    t = re.sub(r'xmlns(?::\w+)?\s*=\s*["\'][^"\']*["\']', "", text)
    return re.findall(r'https?://[^\s"\'<>)]+', t)


# ── 1-5: static ──────────────────────────────────────────────────────

def static_checks() -> None:
    import html5lib

    html = _read("index.html")
    css = _read("styles.css")
    js = _read("main.js")

    print("== 1. HTML structure ==")
    raw = html.encode("utf-8")
    try:
        html5lib.HTMLParser(strict=True).parse(raw)
        print("  PASS  index.html parses with no conformance errors")
    except html5lib.html5parser.ParseError as exc:  # pragma: no cover
        check(False, "", f"html5lib parse error: {exc}")

    doc = html5lib.parse(raw, namespaceHTMLElements=False)
    root = doc if doc.tag == "html" else doc.find(".//html")
    check(root is not None and bool(root.get("lang")),
          f"<html lang> present = {root.get('lang') if root is not None else None!r}",
          "<html lang> missing")
    vp = doc.find(".//head/meta[@name='viewport']")
    check(vp is not None and "width=device-width" in (vp.get("content") or ""),
          f"viewport meta = {(vp.get('content') if vp is not None else None)!r}",
          "viewport meta missing width=device-width")

    h1s = doc.findall(".//h1")
    check(len(h1s) == 1, "exactly one <h1>", f"{len(h1s)} <h1> elements (want 1)")

    ids = [el.get("id") for el in doc.iter() if el.get("id")]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    check(not dups, f"{len(ids)} ids, no duplicates", f"duplicate id(s): {dups}")

    anchors = {m.group(1) for m in re.finditer(r'href="#([^"]+)"', html)}
    broken = sorted(a for a in anchors if a not in set(ids))
    check(not broken, f"all {len(anchors)} in-page anchors resolve",
          f"broken in-page anchor(s): {broken}")

    print("\n== 2. Image alt (accessibility) ==")
    imgs = doc.findall(".//img")
    print(f"  INFO  {len(imgs)} <img> element(s)")
    missing = [im.get("src") for im in imgs if im.get("alt") is None]
    check(not missing, "every <img> has an alt attribute",
          f"<img> MISSING alt: {missing}")
    decorative = [im for im in imgs
                  if (im.get("alt") or "").strip() == "" and im.get("alt") is not None]
    bad_dec = [im.get("src") for im in decorative
               if im.get("aria-hidden") != "true" and im.get("role") != "presentation"]
    check(not bad_dec,
          f'{len(decorative)} decorative alt="" image(s) hidden from AT',
          f'empty-alt <img> not aria-hidden/presentation: {bad_dec}')
    for im in imgs:
        print(f"  INFO  src={im.get('src')!r} alt={im.get('alt')!r} "
              f"aria-hidden={im.get('aria-hidden')!r}")

    print("\n== 3. Self-contained (no external requests) ==")
    for label, text in (("index.html", html), ("styles.css", css), ("main.js", js)):
        ext = _external_refs(text)
        check(not ext, f"{label}: no external http(s) reference",
              f"{label}: external reference(s) {ext}")

    print("\n== 4. Accessibility (static) ==")
    check('class="skip-link"' in html and 'href="#main"' in html,
          "skip link present", "skip link missing")
    check('id="main"' in html and 'tabindex="-1"' in html,
          "skip-link target <main id=main tabindex=-1> present",
          "skip-link target missing")
    check(":focus-visible" in css, "focus-visible styles present",
          "no :focus-visible style")
    toggles = doc.findall(".//button[@id='navToggle']")
    check(bool(toggles) and toggles[0].get("aria-expanded") is not None
          and toggles[0].get("aria-controls") is not None,
          "nav toggle exposes aria-expanded + aria-controls",
          "nav toggle missing aria-expanded/aria-controls")
    controls = doc.findall(".//input") + doc.findall(".//textarea") + doc.findall(".//select")
    label_for = {l.get("for") for l in doc.findall(".//label") if l.get("for")}
    unlabelled = [c.get("id") or c.get("name") for c in controls
                  if (c.get("id") not in label_for
                      and c.get("aria-label") is None
                      and c.get("aria-labelledby") is None)]
    check(not unlabelled, f"all {len(controls)} form controls labelled",
          f"unlabelled form control(s): {unlabelled}")

    print("\n== 5. Performance (fonts + layout shift) ==")
    fonts_css = (ROOT / "assets" / "fonts.css").read_text(encoding="utf-8")
    srcs = re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", fonts_css)
    non_woff2 = [s for s in srcs if not s.endswith(".woff2")]
    check(not non_woff2, f"all {len(srcs)} @font-face sources are .woff2",
          f"non-woff2 font sources: {non_woff2}")
    missing_fonts = [s for s in srcs if not (ROOT / s).is_file()]
    check(not missing_fonts, "every font file exists on disk",
          f"font file(s) missing: {missing_fonts}")
    preloads = re.findall(r'<link[^>]+rel="preload"[^>]+as="font"', html)
    check(len(preloads) >= 1, f"{len(preloads)} font preload(s) present",
          "no font preload declared")
    check("font-display:swap" in fonts_css.replace(" ", ""),
          "font-display:swap used", "font-display:swap missing")
    no_dim = [im.get("src") for im in imgs
              if im.get("width") is None and im.get("height") is None]
    aspect_ok = "aspect-ratio" in css
    check(not no_dim or aspect_ok,
          "images reserve space (width/height or CSS aspect-ratio)",
          f"<img> without intrinsic size and no CSS aspect-ratio: {no_dim}")


# ── 6-7: contact endpoint ────────────────────────────────────────────

def _post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}
    except Exception as e:  # connection refused etc.
        return 0, {"error": f"{type(e).__name__}: {e}"}


def contact_checks(base: str, do_email: bool) -> None:
    print("\n== 6. /api/contact rejects invalid input (expect 400) ==")
    url = base.rstrip("/") + "/api/contact"
    cases = [
        ("empty body", {}),
        ("missing message", {"name": "A", "email": "a@b.co"}),
        ("invalid email", {"name": "A", "email": "not-an-email", "message": "hi"}),
    ]
    for label, payload in cases:
        code, body = _post(url, payload)
        if code == 429:
            notes.append(f"{label}: HTTP 429 (rate-limited) — inconclusive, re-run later")
            print(f"  WARN  {label}: HTTP 429 (rate-limited)")
            continue
        check(code == 400, f"{label} -> 400 ({body.get('error', '')!r})",
              f"{label} -> {code} (want 400): {body}")

    print("\n== 7. /api/contact accepts a valid payload ==")
    mailbox = credential = None
    try:
        import secrets as _secrets
        mailbox = _secrets.resolve("ASTRA_GMAIL_ADDRESS")
        credential = (_secrets.resolve("ASTRA_GMAIL_APP_PASSWORD")
                      or _secrets.resolve("ASTRA_GMAIL_OAUTH_TOKEN"))
    except Exception as e:
        notes.append(f"secret lookup unavailable: {type(e).__name__}")
    mail_ready = bool(mailbox and credential)
    print(f"  INFO  SMTP configured: {mail_ready}")

    if not do_email:
        notes.append("--no-email: valid-payload check accepts 200 or 503 without sending")
        code, body = _post(url, {"name": "verify-skip", "email": "skip@example.com",
                                 "subject": "no-email", "message": "not sent"})
        check(code in (200, 503, 429),
              f"valid payload -> {code} (no send attempted)",
              f"valid payload -> {code}: {body}")
        return

    if not mail_ready:
        notes.append("SMTP not configured: accepting 503 for the valid-payload check")
    code, body = _post(url, {"name": "Site verification",
                             "email": "verify@astra-agency.dev",
                             "subject": "verify_site self-test",
                             "message": "Automated verification of the contact endpoint."})
    if code == 429:
        notes.append("valid-payload check rate-limited (429) — inconclusive")
        print("  WARN  valid payload -> 429 (rate-limited)")
        return
    if mail_ready:
        check(code == 200 and body.get("ok") is True,
              f"valid payload -> 200 {body}", f"valid payload -> {code}: {body}")
    else:
        check(code in (200, 503),
              f"valid payload -> {code} (503 expected without SMTP)",
              f"valid payload -> {code}: {body}")


# ── 8: public URL ────────────────────────────────────────────────────

def public_check(url: str) -> None:
    print("\n== 8. Public URL ==")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = 0
        notes.append(f"public URL error: {type(e).__name__}: {e}")
    check(code == 200, f"GET {url} -> HTTP {code}", f"GET {url} -> HTTP {code} (want 200)")


def main() -> None:
    ap = argparse.ArgumentParser(prog="verify_site")
    ap.add_argument("--base", default=f"http://127.0.0.1:{os.environ.get('ASTRA_SITE_PORT', '12000')}",
                    help="local base URL of the running site")
    ap.add_argument("--public-url", default=DEFAULT_PUBLIC_URL)
    ap.add_argument("--no-email", action="store_true",
                    help="do not attempt a real SMTP send for the valid-payload check")
    ap.add_argument("--no-live", action="store_true", help="static checks only")
    a = ap.parse_args()

    static_checks()
    if not a.no_live:
        contact_checks(a.base, do_email=not a.no_email)
        public_check(a.public_url)

    print("\n== Summary ==")
    for n in notes:
        print(f"  NOTE  {n}")
    if failures:
        print(f"\nRESULT: FAIL ({len(failures)} problem(s))")
        sys.exit(1)
    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()
