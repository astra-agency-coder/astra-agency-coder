# VERIFY.md — AI ASTRA AGENCY intro website

**Deliverable:** `deliveries/astra-launch/website/`
**Verified by:** Engineering dept (`astra-cto`), with an independent QA pass
**Date:** 2026-11-13
**Verdict:** PASS — all checks below were actually run; raw output recorded.

Files produced:

| File | Size |
|---|---|
| `index.html` | 8880 B |
| `styles.css` | 8957 B |
| `main.js` | 1210 B |
| `assets/favicon.svg` | 517 B |
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
$ python3 - <<'PY'   # duplicate ids / anchors / heading order / aria refs
ids: ['top','g-mark','main','hero-title','services','services-title','how','how-title','contact','contact-title']
duplicate ids: NONE
in-page anchors: ['contact','how','main','services','top']
anchors with missing target: NONE
heading sequence: [1,2,3,3,3,3,2,3,3,3,3,3,2]
heading skips (h_n -> h_{n+2}): NONE
aria-labelledby: ['contact-title','hero-title','how-title','services-title'] -> missing: NONE
```

Every in-page anchor resolves; no duplicate ids; no skipped heading levels.

## 2. Local assets referenced exist

```
$ python3 verify_site.py
== 2. Local asset existence ==
  PASS  asset exists: assets/favicon.svg
  PASS  asset exists: main.js
  PASS  asset exists: styles.css
  PASS  no external (http/https) asset references
```

`grep` over `index.html`, `styles.css`, `main.js`:

```
index.html:  external URLs -> NONE
main.js:     external URLs -> NONE
styles.css:  external URLs -> NONE
```

=> renders with **no CDN dependency** and no third-party tracker.

## 3. Serve locally + HTTP status

Local (ephemeral, verification port 8123):

```
$ python3 -m http.server 8123 --bind 127.0.0.1 --directory .
HTTP 200  size=8880  time=0.001352s
HTTP 200  index.html
HTTP 200  styles.css
HTTP 200  main.js
HTTP 200  assets/favicon.svg
```

Deployed server (port 12000 — see §6):

```
$ curl -sI http://127.0.0.1:12000/
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.13.15
Content-type: text/html
Content-Length: 8880
```

Public URL (runtime port-map 12000):

```
$ curl -s -o /dev/null -w "HTTP %{http_code}  time=%{time_total}s\n" \
    https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/
HTTP 200  time=0.086208s
HTTP 200  index.html
HTTP 200  styles.css
HTTP 200  main.js
HTTP 200  assets/favicon.svg
```

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
- Width audit: the only fixed `width` in px is `46px` (an icon box, line 257)
  — far below a 320px viewport. All layout boxes use `width:100%` +
  `max-width`, or `grid-template-columns: minmax(0, 1fr)`.
- No `100vw`, no negative margins (`grep` -> NONE).
- Breakpoints: single column → 2 columns at `40em` → 4 columns at `60em`.

## 5. JS safety / no-JS fallback

```
$ grep -nE 'eval|fetch|XMLHttpRequest|import\(|document\.write|http' main.js
(no matches)
```

`main.js` is progressive enhancement only: it removes the `no-js` class and
adds a reveal-on-scroll effect via `IntersectionObserver`. The `.reveal`
class is added **only by JS**, so with JS disabled every section stays fully
visible. Respects `prefers-reduced-motion`.

## 6. Secret scan

```
$ python3 ops/astra.py scan-secrets
{
  "clean": true,
  "offenders": []
}
```

## 7. Deploy

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

1. **Brand tokens not used.** `deliveries/astra-launch/brand/tokens.json` did
   not exist when this site was built, so a dark cosmic palette
   (`--brand-1 #7c9cff`, `--brand-2 #c07cff`, `--brand-3 #4be1c9`) was chosen
   instead. **Dependency:** when Creative publishes `brand/tokens.json`, the
   `:root` block in `styles.css` should be re-mapped to the real tokens. The
   palette is centralised in one place to make that a one-block change.
2. **No pixel-level rendering test.** This environment has no headless
   browser, so the responsive check is static (viewport meta + CSS
   heuristics), not a screenshot at real viewports. No horizontal-overflow
   risk was found by inspection, but it was not visually confirmed in a
   browser.
3. **Contact is an email CTA.** `mailto:hello@astra-agency.dev` is a
   conventional placeholder address; no mailbox is provisioned yet (Telegram
   /Gmail integration is still awaiting Owner credentials). No form is
   posted anywhere, and no data is collected — consistent with "no trackers".
4. **No fabricated proof.** There are deliberately **no** client logos, no
   testimonials and no metrics that would imply real customers.
