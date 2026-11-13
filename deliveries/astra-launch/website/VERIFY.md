# VERIFY.md — AI ASTRA AGENCY intro website

**Deliverable:** `deliveries/astra-launch/website/`
**Verified by:** Engineering dept (`astra-cto`), with an independent QA pass
**Date:** 2026-11-13
**Verdict:** PASS — all checks below were actually run; raw output recorded.

Files produced:

| File | Size |
|---|---|
| `index.html` | 8192 B |
| `styles.css` | 10095 B |
| `main.js` | 1210 B |
| `assets/favicon.svg` | 555 B |
| `assets/brand/astra-lockup-horizontal-dark.svg` | 7149 B (Creative, brand v2) |
| `assets/brand/astra-mark-dark.svg` | 415 B (Creative, brand v2) |
| `verify_site.py` | reproducible check script |

---

## 1. HTML validity / well-formedness

Tool: `html5lib` strict parser (installed with `pip install html5lib`).

```
$ cd deliveries/astra-launch/website && python3 verify_site.py
== 1. HTML well-formedness (html5lib strict) ==
  PASS  index.html parses with no conformance errors
  PASS  viewport meta present
  PASS  viewport content = 'width=device-width, initial-scale=1'
  PASS  <main> landmark present
  PASS  <h1> present
  PASS  exactly one <h1>
  PASS  <html lang> present = 'en'
```

Additional structural checks:

```
$ python3 - <<'PY'   # duplicate ids / anchors / heading order / img alt / external refs
dup ids: NONE
broken anchors: NONE
heading skips: NONE
imgs missing alt: NONE
external URLs: NONE
```

Every in-page anchor resolves; no duplicate ids; no skipped heading levels;
every `<img>` has an `alt`.

## 2. Local assets referenced exist

```
$ python3 verify_site.py
== 2. Local asset existence ==
  PASS  asset exists: assets/brand/astra-lockup-horizontal-dark.svg
  PASS  asset exists: assets/brand/astra-mark-dark.svg
  PASS  asset exists: assets/favicon.svg
  PASS  asset exists: main.js
  PASS  asset exists: styles.css
  PASS  no external (http/https) asset references
```

=> renders with **no CDN dependency** and no third-party tracker.

## 3. Serve locally + HTTP status

Deployed server (port 12000 — see §7):

```
$ curl -sI http://127.0.0.1:12000/
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.13.15
Content-type: text/html
```

Every referenced asset:

```
HTTP 200  /
HTTP 200  /index.html
HTTP 200  /styles.css
HTTP 200  /main.js
HTTP 200  /assets/favicon.svg
HTTP 200  /assets/brand/astra-lockup-horizontal-dark.svg
HTTP 200  /assets/brand/astra-mark-dark.svg
```

Public URL (runtime port-map 12000):

```
$ curl -s -o /dev/null -w "PUBLIC HTTP %{http_code}\n" \
    https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/
PUBLIC HTTP 200
```

Independent QA (`qa-repro-auditor`) additionally confirmed the public
`index.html` is **byte-identical** to the source file (`diff -q` clean).

## 4. Responsive sanity

```
$ python3 verify_site.py
== 3. Responsive sanity ==
  PASS  media queries present
  PASS  no fixed width >= 480px on layout boxes
  PASS  max-width used for container (fluid)
  PASS  box-sizing: border-box set
```

- Viewport meta: `width=device-width, initial-scale=1` (present, §1).
- Width audit: the only fixed `width` in px is `46px` (an icon box)
  — far below a 320px viewport. All layout boxes use `width:100%` +
  `max-width`, or `grid-template-columns: minmax(0, 1fr)`.
- No `100vw`, no negative margins (`grep` -> NONE).
- Breakpoints: single column → 2 columns at `40em` → 4 columns at `60em`.

## 5. Brand-token conformance (Creative `brand/tokens.json` v2.0.0)

The Creative department published brand tokens *during* this build, so the
site was re-mapped to them (dark theme, `color.sys_resolved.dark`).

```
$ python3 verify_site.py
== 4. Brand-token conformance (Creative tokens.json v2) ==
  PASS  brand token background #0B0A12 present in styles.css
  PASS  brand token on-surface #E6E1E9 present in styles.css
  PASS  brand token primary #C9B0F0 present in styles.css
  PASS  brand token secondary #8FDBE4 present in styles.css
  PASS  brand token tertiary #F5D488 present in styles.css
```

- The header uses Creative's real `astra-lockup-horizontal-dark.svg`; the
  footer uses `astra-mark-dark.svg`; the favicon is derived from the mark.
- Typography follows the token file's `typography.font`: **DejaVu Serif** for
  brand/headings, **DejaVu Sans** for body (the documented substitutes for the
  licensed faces), with system fallbacks.

## 6. JS safety / no-JS fallback

```
$ grep -nE 'eval|fetch|XMLHttpRequest|document\.write|https?://' main.js
(no matches)
```

`main.js` is progressive enhancement only: it removes the `no-js` class and
adds a reveal-on-scroll effect via `IntersectionObserver`. The `.reveal`
class is added **only by JS**, so with JS disabled every section stays fully
visible. Respects `prefers-reduced-motion`.

## 7. Secret scan + deploy

```
$ python3 ops/astra.py scan-secrets
{
  "clean": true,
  "offenders": []
}
```

```
$ rm -rf /tmp/astra_site && mkdir -p /tmp/astra_site \
  && cp -r deliveries/astra-launch/website/* /tmp/astra_site/
$ nohup python3 -m http.server 12000 --directory /tmp/astra_site \
      > /tmp/astra_site.log 2>&1 &
$ curl -sI http://127.0.0.1:12000/
HTTP/1.0 200 OK
```

Live URL: **https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/** (HTTP 200).

---

## Honest limitations (not hidden)

1. **No pixel-level rendering test.** This environment has no headless
   browser, so the responsive check is static (viewport meta + CSS
   heuristics), not a screenshot at real viewports. No horizontal-overflow
   risk was found by inspection, but it was not visually confirmed in a
   browser.
2. **Fonts are documented substitutes.** The brand specifies DejaVu Serif /
   DejaVu Sans as stand-ins for licensed faces. On machines without DejaVu
   the site falls back to Georgia / system sans; the *logo lockups carry no
   font dependency* (Creative converted the wordmark to vector outlines), so
   the brand mark itself is exact everywhere.
3. **Contact is an email CTA.** `mailto:hello@astra-agency.dev` is a
   conventional placeholder address; no mailbox is provisioned yet (Telegram
   /Gmail integration is still awaiting Owner credentials). No form is
   posted anywhere, and no data is collected — consistent with "no trackers".
4. **No fabricated proof.** There are deliberately **no** client logos, no
   testimonials and no metrics that would imply real customers.
5. **Light theme not shipped.** The brand defines a full light theme; this
   site intentionally ships the dark ("cosmic") theme only, matching the
   brand tone. A light variant is a future enhancement, not a defect.
