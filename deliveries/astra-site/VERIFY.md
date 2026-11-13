# VERIFY.md — AI ASTRA AGENCY company site

**Deliverable:** `deliveries/astra-site/`
**Owner:** Engineering (`astra-cto`) · **Date:** 2026-11-13
**Verdict:** PASS — every check below was actually run; raw output summarised.

| File | Role |
|---|---|
| `index.html` | cinematic one-page site (hero, bento, process, work, numbers, contact) |
| `styles.css` | "OBSIDIAN" theme |
| `main.js` | canvas constellation, scroll reveal, count-up, cursor, form submit |
| `server.py` | stdlib HTTP server + `POST /api/contact` → Gmail SMTP |
| `serve.sh` | idempotent (re)launcher, port 12000, log `/tmp/astra_site_new.log` |
| `healthcheck.sh` | curl healthcheck, non-zero exit unless HTTP 200 |
| `verify_site.py` | reproducible verification (static + live) |
| `assets/` | reel mp4, thumbnail, brand sheet, mark.svg, self-hosted woff2 fonts |

## How to reproduce

```bash
cd deliveries/astra-site
python3 verify_site.py            # full: static + contact endpoint + public URL
python3 verify_site.py --no-email # do not attempt a real SMTP send
bash serve.sh && bash healthcheck.sh
```

## 1. HTML structure — PASS
- `index.html` parses with html5lib strict, no conformance errors.
- one `<h1>`, `<html lang="en">`, viewport `width=device-width`.
- 20 ids, **no duplicates**; all 5 in-page anchors resolve.

## 2. Images — PASS
- 1 `<img>` (brand sheet) with a non-empty `alt`; no decorative `alt=""` case is
  present, but the checker fails any empty-alt image that is not
  `aria-hidden="true"`/`role="presentation"` (the WCAG decorative pattern).

## 3. Self-contained — PASS
- No `http(s)` reference in HTML/CSS/JS (`xmlns` and the inline `data:` SVG noise
  texture are not network requests). `grep -E 'https?://'` → empty.

## 4. Accessibility — PASS
- Skip link `a.skip-link[href="#main"]` + `<main id="main" tabindex="-1">` target.
- `:focus-visible{outline:2px solid var(--cyan)}`; `main:focus{outline:none}`.
- Nav toggle: `aria-expanded`, `aria-controls="navLinks"`, label flips
  Open/Close menu, Escape closes and returns focus.
- Closed mobile menu gets `visibility:hidden` (out of the tab order).
- All 4 form controls have a `<label for>`; status line is `role="status"`.
- `<noscript>` CSS forces reveal content visible (progressive enhancement).

## 5. Performance — PASS
- 10 `@font-face` sources, **all `.woff2`**, all present on disk, `font-display:swap`.
- 2 critical faces preloaded (`fraunces-4`, `instrument-2`) with `crossorigin`.
- No layout shift: `<img>` carries `width`/`height` + `loading="lazy"` +
  `decoding="async"`; the reel has a `poster` and CSS `aspect-ratio:9/16`.

## 6. Contact endpoint — PASS
- `{}`, missing-message and invalid-email payloads → **400**.
- valid payload → **200** `{"ok": true}` (real SMTP send; mailbox configured).

## 7. Public URL — PASS
- `GET https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/` → **200**,
  serving the site (title `AI ASTRA AGENCY — Autonomous Digital Studio`).

## 8. Hardening (added this pass)
- `server.py` `send_head()` allowlists public asset suffixes and 404s dotfiles,
  source and dev files: `/server.py`, `/verify_site.py`, `/serve.sh`,
  `/healthcheck.sh`, `/.gitignore` → **404** (verified locally and on the public
  URL). No directory listing.

## 9. Self-heal — PASS
- `python3 ops/heal.py` → `[OK ] astra_site`.
- Killed the listener → `healthcheck.sh` HTTP `000` (exit 1) → `heal.py` →
  `[FIX] astra_site attempts=1 … all healthy: True`.

## 10. Secrets — PASS
- `python3 ops/astra.py scan-secrets` → `{"clean": true, "offenders": []}`.

## Known limitations
- No headless browser in this environment: keyboard-tabbing and pixel rendering
  are verified **statically** (markup/aria/CSS heuristics), not by automation.
- `serve.sh` matches its target with the anchored pattern `^python3 server\.py$`
  so it never kills an unrelated process.
