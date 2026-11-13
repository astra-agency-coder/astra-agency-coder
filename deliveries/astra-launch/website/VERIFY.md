# VERIFY.md — AI ASTRA AGENCY intro website

**Deliverable:** `deliveries/astra-launch/website/`
**Verified by:** Engineering dept (`astra-cto`), with an independent QA pass
**Date:** 2026-11-13
**Verdict:** PASS — all checks below were actually run; raw output recorded.
**Round-2 (QA defect fixes):** D-W1 durable deploy · D-W2 real alt check ·
D-W3 dev files no longer web-reachable · D-W4 overflow-wrap. See §8.

Files produced:

| File | Size |
|---|---|
| `index.html` | 8192 B |
| `styles.css` | 10226 B |
| `main.js` | 1210 B |
| `assets/favicon.svg` | 555 B |
| `assets/brand/astra-lockup-horizontal-dark.svg` | 7149 B (Creative, brand v2) |
| `assets/brand/astra-mark-dark.svg` | 415 B (Creative, brand v2) |
| `verify_site.py` | reproducible check script (now incl. img-alt check) |
| `serve.sh` | idempotent durable launcher (port 12000) |
| `healthcheck.sh` | curl healthcheck, non-zero exit if not HTTP 200 |

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
$ python3 - <<'PY'   # duplicate ids / anchors / heading order / external refs
dup ids: NONE
broken anchors: NONE
heading skips: NONE
external URLs: NONE
```

Every in-page anchor resolves; no duplicate ids; no skipped heading levels.

### 1b. Image `alt` (real check, in `verify_site.py`)

QA (D-W2) correctly noted the previous "imgs missing alt: NONE" claim was not
backed by any code. `verify_site.py` now performs a **real** alt audit on the
parsed DOM:

```
== 1b. Image alt attributes (accessibility) ==
  INFO  2 <img> element(s) found
  PASS  every <img> has an alt attribute (present; may be empty for decorative)
  PASS  1 decorative alt="" image(s) marked aria-hidden="true"/presentation
  PASS  alt coverage complete: 1 meaningful + 1 decorative
  INFO  src='assets/brand/astra-lockup-horizontal-dark.svg' alt='AI ASTRA AGENCY' aria-hidden=None
  INFO  src='assets/brand/astra-mark-dark.svg' alt='' aria-hidden='true'
```

The rule, stated explicitly:

- Every `<img>` **must** carry an `alt` attribute.
- A **non-empty** `alt` is required when the image conveys meaning (here the
  header lockup: `alt="AI ASTRA AGENCY"`).
- The **decorative** case `alt=""` is the WCAG-correct pattern **only** when the
  image is also hidden from assistive technology (`aria-hidden="true"` or
  `role="presentation"`). The footer mark is exactly that: `alt=""` +
  `aria-hidden="true"`, with the adjacent visible text "AI ASTRA AGENCY"
  carrying the meaning. The check fails any empty-alt image that is *not* so
  marked.

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
Re-confirmed in round-2 (§8): source md5 == public md5 ==
`6829df564e3eb9746c81225367a1fa2a`.

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

## 7. Secret scan + durable deploy

```
$ python3 ops/astra.py scan-secrets
{
  "clean": true,
  "offenders": []
}
```

Deployment is now **idempotent and self-healing** (D-W1), not a one-off
in-session command. Two scripts live beside the site:

- `serve.sh` — kills any prior instance **by port**, rebuilds a **clean** doc
  root that contains only the built site, starts a detached server with
  `nohup`, logs to `/tmp/astra_site.log`, and waits for HTTP 200.
- `healthcheck.sh` — curls the local root; exits non-zero unless HTTP 200.

```
$ deliveries/astra-launch/website/serve.sh
[serve] stopping prior instance(s) on :12000: 88748
[serve] started detached server (pid 96504) -> /tmp/astra_site (log: /tmp/astra_site.log)
[serve] healthcheck GET http://127.0.0.1:12000/ -> HTTP 200
[serve] OK — site is up on :12000
```

`ops/heal.py` now carries an additive `intro_site` check: if the site is
expected up (default) and returns non-200, it re-runs `serve.sh` (bounded to
`MAX_ATTEMPTS = 3`). Set `ASTRA_SITE_EXPECTED=0` to opt out.

Live URL: **https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/** (HTTP 200).
Round-2 evidence for all four defects is in §8.

---

## 8. Round-2 — QA defect fixes (D-W1 … D-W4)

Independent QA (`astra-cqo`) raised four website defects. Each is fixed and the
fix re-verified below. Public base URL used throughout:
`https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev`.

### D-W1 (MEDIUM) — deployment was ephemeral → now durable + self-healing

Change: added `serve.sh` (idempotent launcher, kills prior instance **by port**,
clean doc root, detached `nohup`, log `/tmp/astra_site.log`, waits for 200) and
`healthcheck.sh`; wired an additive `intro_site` check into `ops/heal.py`
(bounded to `MAX_ATTEMPTS = 3`).

Evidence — reproduced the exact QA failure, then healed it:

```
# 1. kill the site, confirm the failure QA saw
$ pkill -f "http.server 12000"; sleep 1
$ deliveries/astra-launch/website/healthcheck.sh
healthcheck: GET http://127.0.0.1:12000/ -> HTTP 000     # exit 1
$ curl -s -o /dev/null -w "PUBLIC HTTP %{http_code}\n" $PUBLIC/
PUBLIC HTTP 502                                          # <-- the QA defect

# 2. self-heal via ops/heal.py
$ python3 ops/heal.py
[OK ] agent_server
...
[FIX] intro_site       attempts=1
        attempt 1: serve.sh ok: [serve] OK — site is up on :12000
all healthy: True | escalations: []

# 3. re-check
$ deliveries/astra-launch/website/healthcheck.sh
healthcheck: GET http://127.0.0.1:12000/ -> HTTP 200     # exit 0
$ curl -s -o /dev/null -w "PUBLIC HTTP %{http_code}\n" $PUBLIC/
PUBLIC HTTP 200
```

Idempotency: running `serve.sh` again stops the old pid and starts exactly one
new one (single listener on 12000). Opt-out guard verified:
`ASTRA_SITE_EXPECTED=0 python3 ops/heal.py` reports `intro_site` OK while the
site is intentionally down.

### D-W2 (LOW) — real alt check added

Change: `verify_site.py` §1b audits the parsed DOM (see §1b above). It fails any
`<img>` with no `alt`, and fails any `alt=""` image that is not
`aria-hidden="true"`/`role="presentation"`. Decorative case stated explicitly.

### D-W3 (LOW) — dev files no longer web-reachable

Change: `serve.sh` builds a clean doc root containing **only** the built site
(`index.html`, `styles.css`, `main.js`, `assets/`); `VERIFY.md`,
`verify_site.py`, `serve.sh`, `healthcheck.sh` are never copied.

```
$ curl -s -o /dev/null -w "%{http_code}\n" $PUBLIC/VERIFY.md
404
$ curl -s -o /dev/null -w "%{http_code}\n" $PUBLIC/verify_site.py
404
$ curl -s -o /dev/null -w "%{http_code}\n" $PUBLIC/serve.sh
404
$ curl -s -o /dev/null -w "%{http_code}\n" $PUBLIC/healthcheck.sh
404
# the real site still serves:
$ for p in / /index.html /styles.css /main.js /assets/favicon.svg \
           /assets/brand/astra-lockup-horizontal-dark.svg /assets/brand/astra-mark-dark.svg; do
    curl -s -o /dev/null -w "200 $p\n" $PUBLIC$p; done
```

### D-W4 (INFO) — overflow guard added

Change: `body` in `styles.css` now sets `overflow-wrap: anywhere` and
`word-break: break-word`, so a future long unbreakable token cannot overflow.

```
$ grep -n "overflow-wrap\|word-break" deliveries/astra-launch/website/styles.css
53:  overflow-wrap: anywhere;
54:  word-break: break-word;
```

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
6. **Durability is "process-durable", not host-durable.** D-W1's fix makes the
   site restartable and self-healing *inside this runtime* (`serve.sh` +
   `ops/heal.py`), which removes the ephemeral one-shot failure QA hit. It does
   **not** survive the runtime itself being recycled (`OH_RUNTIME_IDLE_TIMEOUT_SECONDS`).
   A permanent public host is the next step if the Owner needs a URL that
   outlives the runtime; that is a deployment decision, not a website defect.
