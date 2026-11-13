# evidence-website.md — independent QA verification (qa-repro-auditor)

**Verifier:** `qa-repro-auditor` (Quality dept) — independent of the author.
**Reported to:** `astra-cqo`
**Date/time:** 2026-11-13 ~14:29–14:31 UTC
**Source dir:** `/workspace/project/deliveries/astra-launch/website/`
**Public URL:** `https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/`
**Method:** every claim below was produced by a command I ran myself. I did NOT read the
author's `VERIFY.md` for values — I recomputed them (I read it only afterwards, to explain
a discrepancy). No files under `deliveries/astra-launch/website/` were modified.

Tools used: `curl`, `python3` (stdlib + `html5lib`), `grep`, `md5sum`, `cmp`.
No packages were installed.

---

## Source inventory + md5 (baseline)

```
$ cd /workspace/project/deliveries/astra-launch/website && find . -type f -print0 | xargs -0 md5sum | sort -k2
31dcbb43fad8cff455208e28389a5e63  ./VERIFY.md
cb43f56becb99efe4a191310cbc992cb  ./assets/brand/astra-lockup-horizontal-dark.svg
3e970e7a2e5e22a2e380662a859aedcf  ./assets/brand/astra-mark-dark.svg
7e2cd422ed3dea7150a5940da5d666e8  ./assets/favicon.svg
6829df564e3eb9746c81225367a1fa2a  ./index.html
91d67a59334ff15da1158080698a3c22  ./main.js
a0ad8ebaa33371b95df08e10b2ea6c72  ./styles.css
dde9efc54cab720bd41b58e552864998  ./verify_site.py
```

---

## W1 — Public URL HTTP 200 + stability + assets

### W1a — repeated fetches over ~30s (12 iterations, 2.5s apart)

```
$ URL="https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/"
$ for i in $(seq 1 12); do code=$(curl -s -o /dev/null -w "%{http_code} time=%{time_total}s size=%{size_download}" --max-time 20 "$URL"); echo "$(date +%H:%M:%S) iter=$i -> $code"; sleep 2.5; done
14:29:16 iter=1 -> 200 time=0.099906s size=8192
14:29:18 iter=2 -> 200 time=0.016255s size=8192
14:29:21 iter=3 -> 200 time=0.023187s size=8192
14:29:24 iter=4 -> 200 time=0.014802s size=8192
14:29:26 iter=5 -> 200 time=0.025138s size=8192
14:29:29 iter=6 -> 200 time=0.015273s size=8192
14:29:31 iter=7 -> 200 time=0.022677s size=8192
14:29:34 iter=8 -> 200 time=0.016276s size=8192
14:29:36 iter=9 -> 200 time=0.022582s size=8192
14:29:39 iter=10 -> 200 time=0.047354s size=8192
14:29:41 iter=11 -> 200 time=0.081152s size=8192
14:29:44 iter=12 -> 200 time=0.012977s size=8192
```

### W1a2 — additional rapid burst (40 more requests)

```
$ for i in $(seq 1 20); do curl -s -o /dev/null -w "%{http_code} " --max-time 15 "$URL"; done
200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200
$ for i in $(seq 1 20); do curl -s -o /dev/null -w "%{http_code}\n" --max-time 15 "$URL"; done | sort | uniq -c
     20 200
```

**Every status code observed across all 52 requests: `200` only. No 3xx/4xx/5xx, no timeouts.**

### W1b — every referenced asset fetched from the public host

```
$ BASE="https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev"
$ for p in "styles.css" "main.js" "assets/favicon.svg" "assets/brand/astra-lockup-horizontal-dark.svg" "assets/brand/astra-mark-dark.svg"; do fn=$(echo "$p" | tr '/' '_'); out=$(curl -s -o "/tmp/qaw/$fn" -w "%{http_code} bytes=%{size_download} ctype=%{content_type}" --max-time 20 "$BASE/$p"); echo "$p -> $out"; done
styles.css -> 200 bytes=10095 ctype=text/css
main.js -> 200 bytes=1210 ctype=text/javascript
assets/favicon.svg -> 200 bytes=555 ctype=image/svg+xml
assets/brand/astra-lockup-horizontal-dark.svg -> 200 bytes=7149 ctype=image/svg+xml
assets/brand/astra-mark-dark.svg -> 200 bytes=415 ctype=image/svg+xml
```

### W1c — response headers

```
$ curl -s -I "$BASE/"
HTTP/2 200
content-type: text/html
date: Fri, 13 Nov 2026 14:29:56 GMT
last-modified: Fri, 13 Nov 2026 14:24:24 GMT
server: SimpleHTTP/0.6 Python/3.13.15
content-length: 8192
```

**W1: PASS.** Root + `/index.html` + all 5 referenced assets return 200; all stable across 52
requests over ~30s+.

---

## W2 — byte-identity of public bytes vs source

```
$ cd /tmp/qaw && curl -s -o root.html "$BASE/" ; curl -s -o index_fetched.html "$BASE/index.html"
$ md5sum root.html index_fetched.html
6829df564e3eb9746c81225367a1fa2a  root.html
6829df564e3eb9746c81225367a1fa2a  index_fetched.html
$ md5sum /workspace/project/deliveries/astra-launch/website/index.html
6829df564e3eb9746c81225367a1fa2a  /workspace/project/deliveries/astra-launch/website/index.html
$ cmp /workspace/project/deliveries/astra-launch/website/index.html root.html        && echo IDENTICAL
CMP source-vs-root: IDENTICAL
$ cmp /workspace/project/deliveries/astra-launch/website/index.html index_fetched.html && echo IDENTICAL
CMP source-vs-index: IDENTICAL
$ cmp root.html index_fetched.html
root==index: IDENTICAL
```

`/` and `/index.html` are byte-identical to each other and to the source file.

Asset bytes also match source md5:

```
fetched: a0ad8ebaa33371b95df08e10b2ea6c72  /tmp/qaw/styles.css
source : a0ad8ebaa33371b95df08e10b2ea6c72  styles.css
fetched: 91d67a59334ff15da1158080698a3c22  /tmp/qaw/main.js
source : 91d67a59334ff15da1158080698a3c22  main.js
fetched: 7e2cd422ed3dea7150a5940da5d666e8  /tmp/qaw/assets_favicon.svg
source : 7e2cd422ed3dea7150a5940da5d666e8  assets/favicon.svg
fetched: cb43f56becb99efe4a191310cbc992cb  /tmp/qaw/assets_brand_astra-lockup-horizontal-dark.svg
source : cb43f56becb99efe4a191310cbc992cb  assets/brand/astra-lockup-horizontal-dark.svg
fetched: 3e970e7a2e5e22a2e380662a859aedcf  /tmp/qaw/assets_brand_astra-mark-dark.svg
source : 3e970e7a2e5e22a2e380662a859aedcf  assets/brand/astra-mark-dark.svg
```

**W2: PASS.** `index.html` md5 `6829df564e3eb9746c81225367a1fa2a` on source, `/`, and `/index.html`.
All served assets match source byte-for-byte.

---

## W3 — HTML validity + structure (my own parser)

Script `/tmp/qaw/w3.py` uses `html5lib.HTMLParser(strict=True, namespaceHTMLElements=False)`
plus the strict=False tree for structural queries, and `xml.etree` for an informational check.

```
$ python3 w3.py
=== W3a: html5lib STRICT parse (namespaceHTMLElements=False) ===
PASS: parsed with strict=True, no exception

=== W3a2: html5lib errors list (strict=False parse to collect errors) ===
error count: 0

=== W3b: duplicate id check (html5lib tree) ===
all ids: ['top', 'main', 'hero-title', 'services', 'services-title', 'how', 'how-title', 'contact', 'contact-title']
duplicates: NONE
DUP RESULT: PASS

=== W3c: in-page anchors resolve ===
in-page anchors: ['#main', '#top', '#services', '#how', '#contact', '#contact', '#services']
unresolved: NONE
ANCHOR RESULT: PASS

=== W3d: img alt non-empty; svg role=img aria-label ===
  img src='assets/brand/astra-lockup-horizontal-dark.svg' alt='AI ASTRA AGENCY' aria-hidden=None
  img src='assets/brand/astra-mark-dark.svg' alt='' aria-hidden='true'
imgs missing non-empty alt: ['assets/brand/astra-mark-dark.svg']
IMG ALT RESULT: FAIL

=== W3e: heading order ===
   h1 | We build digital products with an AI-agent workfor
   h2 | What we do
   h3 | Web & app build
   h3 | AI automation
   h3 | Video & design
   h3 | Digital products
   h2 | How we work
   h3 | Brief & plan
   h3 | Build
   h3 | Verify
   h3 | Deliver
   h3 | An agent workforce, not a chatbot
   h2 | Start a project
h1 count: 1
skipped-level transitions (prev->next): NONE
HEADING RESULT: PASS

=== W3f: html lang + viewport ===
html lang = 'en'
meta names: [None, 'viewport', 'description', 'theme-color', 'color-scheme', 'robots']
viewport present: True
HTML/VPort RESULT: PASS

=== W3g: xml.etree well-formedness check (HTML is not XML; informational) ===
ET.fromstring ParseError (expected for HTML void elements): mismatched tag: line 13, column 2
```

Sub-results:
- parses with no conformance errors — **PASS** (strict=True raised nothing; 0 errors)
- no duplicate ids — **PASS**
- every in-page anchor resolves — **PASS**
- every `<img>` has non-empty alt — **FAIL (1 literal violation)** — see defect D1
- `<svg role=img>` / aria-labels — all three SVGs carry `role="img"` + `aria-label`
  (`favicon.svg`, `astra-lockup-horizontal-dark.svg`, `astra-mark-dark.svg`). **PASS**
- heading order sane, exactly one h1 — **PASS**
- `<html lang>` + viewport meta present — **PASS**

**W3: FAIL (one literal sub-check).** All structural checks pass except the letter of the
"non-empty alt" rule. See D1 below for the full analysis — the failing `<img>` is the
**decorative footer mark** (`alt=""` + `aria-hidden="true"`), which is the WCAG-correct
pattern; the failing element is the same one the author's own script (and its report) missed,
because `verify_site.py` has **no `alt` check at all**.

---

## W4 — renders without JS, makes no external requests

### W4a — http(s) references in HTML/CSS/JS

```
$ cd /workspace/project/deliveries/astra-launch/website
$ grep -rniE "https?://" index.html styles.css main.js
exit=1   # no matches
```

### W4b — script/link/href/src inventory

```
$ grep -niE "<script|<link|@import|src=|href=" index.html styles.css main.js
index.html:11:  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
index.html:12:  <link rel="stylesheet" href="styles.css">
index.html:15:  <a class="skip-link" href="#main">Skip to main content</a>
index.html:19:      <a class="brand" href="#top">
index.html:20:        <img class="brand-lockup" src="assets/brand/astra-lockup-horizontal-dark.svg"
index.html:25:          <li><a href="#services">Services</a></li>
index.html:26:          <li><a href="#how">How we work</a></li>
index.html:27:          <li><a href="#contact">Contact</a></li>
index.html:45:          <a class="btn btn-primary" href="#contact">Start a project</a>
index.html:46:          <a class="btn btn-ghost" href="#services">See what we do</a>
index.html:148:          <a class="btn btn-primary btn-lg" href="mailto:hello@astra-agency.dev?subject=Project%20brief%20for%20AI%20ASTRA%20AGENCY">Email hello@astra-agency.dev</a>
index.html:161:        <img src="assets/brand/astra-mark-dark.svg" alt="" width="24" height="24" aria-hidden="true">
index.html:169:  <script src="main.js" defer></script>
```

### W4c — dynamic APIs (fetch/XHR/eval/document.write/import/Function/WebSocket/sendBeacon)

```
$ grep -rniE "fetch\(|XMLHttpRequest|eval\(|document\.write|import\(|new Function|WebSocket|navigator\.sendBeacon" index.html styles.css main.js
exit=1   # no matches
```

### W4d — all URL-bearing attribute values

```
$ grep -oE "(src|href|action|poster|data)=\"[^\"]*\"" index.html
href="assets/favicon.svg"
href="styles.css"
href="#main"
href="#top"
src="assets/brand/astra-lockup-horizontal-dark.svg"
href="#services"
href="#how"
href="#contact"
href="#contact"
href="#services"
href="mailto:hello@astra-agency.dev?subject=Project%20brief%20for%20AI%20ASTRA%20AGENCY"
src="assets/brand/astra-mark-dark.svg"
src="main.js"
```

Also checked: no `<base>` tag (`grep -n "<base" index.html` -> exit=1), no
`preconnect`/`dns-prefetch`/`preload` hints, no `@import`, no iframes/objects/embeds/forms,
no inline `on*=` handlers.

**Every external-request hit found in HTML/CSS/JS: NONE (zero).** The only non-relative URL
is the `mailto:` link, which triggers no network request and is expected.

Note (informational, not a network request): the SVGs use the XML namespace literal
`xmlns="http://www.w3.org/2000/svg"`. This is a namespace identifier, never fetched.

### W4e — visible content present in static HTML (no-JS fallback)

```
$ python3 -c 'check key phrases in raw index.html'
PRESENT 'We build digital products'
PRESENT 'What we do'
PRESENT 'Web &amp; app build'
PRESENT 'AI automation'
PRESENT 'Video &amp; design'
PRESENT 'Digital products'
PRESENT 'How we work'
PRESENT 'Brief &amp; plan'
PRESENT 'Verify'
PRESENT 'Deliver'
PRESENT 'An agent workforce, not a chatbot'
PRESENT 'Start a project'
PRESENT 'hello@astra-agency.dev'
PRESENT 'AI ASTRA AGENCY'
PRESENT 'No trackers, no cookies'
```

`main.js` is pure progressive enhancement: it only *removes* the `no-js` class and adds
`reveal`/`is-visible` classes. The default CSS keeps content visible (`.no-js .reveal { opacity: 1 }`),
and no section markup is injected by JS. All section text is in the static HTML.

**W4: PASS.** No external requests; content fully present without JS.

---

## W5 — break tests (static / non-browser analysis)

### W5a — very long text: every `px` width in the CSS

Every literal `px` value in `styles.css` (line-by-line):

```
$ python3 -  # regex -?[0-9]*\.?[0-9]+px over styles.css
styles.css:23:      4px  --r-xs: 4px; --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-xl: 28px;
styles.css:23:      8px  (radius)
styles.css:23:     12px  (radius)
styles.css:23:     16px  (radius)
styles.css:23:     28px  (radius)
styles.css:26:      8px  --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 32px;
styles.css:26:     12px  (spacing)
styles.css:26:     16px  (spacing)
styles.css:26:     24px  (spacing)
styles.css:26:     32px  (spacing)
styles.css:27:     48px  --s7: 48px; --s8: 64px; --s9: 96px;
styles.css:27:     64px  (spacing)
styles.css:27:     96px  (spacing)
styles.css:48:     16px  font-size: 16px;
styles.css:53:   1100px  radial-gradient(1100px 620px ...)
styles.css:53:    620px  radial-gradient(... 620px ...)
styles.css:54:    900px  radial-gradient(900px 560px ...)
styles.css:54:    560px  radial-gradient(... 560px ...)
styles.css:55:    820px  radial-gradient(820px 540px ...)
styles.css:55:    540px  radial-gradient(... 540px ...)
styles.css:70:      3px  outline: 3px solid var(--focus);
styles.css:71:      3px  outline-offset: 3px;
styles.css:77:  -9999px  left: -9999px;
styles.css:99:     10px  backdrop-filter: blur(10px);
styles.css:101:     1px  border-bottom: 1px solid var(--border);
styles.css:112:    30px  .brand-lockup { height: 30px; width: auto; }
styles.css:113:    26px  @media (max-width: 26em) { .brand-lockup { height: 26px; } }
styles.css:126:   999px  border-radius: 999px;
styles.css:144:     1px  border: 1px solid var(--border);
styles.css:145:   999px  border-radius: 999px;
styles.css:177:   999px  border-radius: 999px;
styles.css:180:     1px  border: 1px solid transparent;
styles.css:183:    -1px  .btn:hover { transform: translateY(-1px); }
styles.css:206:     1px  border: 1px solid var(--border);
styles.css:221:     1px  .section-alt { border-block: 1px solid var(--border); }
styles.css:242:     1px  border: 1px solid var(--border);
styles.css:256:    46px  width: 46px;      (.card-icon)
styles.css:257:    46px  height: 46px;
styles.css:261:     1px  border: 1px solid var(--border);
styles.css:276:     1px  border: 1px solid var(--border);
styles.css:292:   999px  border-radius: 999px;
styles.css:300:     1px  border: 1px solid var(--border);
styles.css:301:     3px  border-left: 3px solid var(--tertiary);
styles.css:316:     1px  border-top: 1px solid var(--border);
styles.css:330:    24px  .footer-brand img { height: 24px; width: auto; }
styles.css:346:    14px  .reveal { transform: translateY(14px); }
```

Classification of the large/absolute values:
- `1100/620/900/560/820/540px` — sizes of **`radial-gradient` background blobs** on
  `body`. Backgrounds are painted, clipped to the element, and do **not** contribute to
  layout/scroll width. Cannot cause overflow.
- `999px` — `border-radius` on pill shapes. Does not affect box size.
- `-9999px` — `left: -9999px` on the off-screen `.skip-link`. Absolutely positioned, so it is
  out of flow; it does not widen the page (and is brought on-screen on `:focus`).
- `46px`, `30px`, `26px`, `24px` — fixed sizes for an icon box and logo heights, each with
  `width: auto` where an image; these are small and sit inside fluid containers.

`width`/`max-width` declarations:

```
$ grep -nE "width" styles.css
64:img, svg { max-width: 100%; height: auto; }
88:  width: 100%;
89:  max-width: var(--wrap);          /* 68rem */
112:.brand-lockup { ... height: 30px; width: auto; }
135:.hero-inner { max-width: 52rem; }
165:  max-width: 44rem;
202:  max-width: 34rem;
222:.section-head { max-width: 46rem; ... }
256:  width: 46px;
286:  width: 2rem;                     /* .step-num */
312:.contact-note { margin: 0 auto; max-width: 34rem; ... }
330:.footer-brand img { height: 24px; width: auto; }
```

**No fixed `width` on any layout container** — the container is `width:100%; max-width:68rem`.
Card/step grids use `minmax(0, 1fr)`. So long *text* reflows/wraps normally.

Longest unbreakable token in the visible copy:

```
$ python3 -  # longest \S+ tokens in tag-stripped index.html
22 'hello@astra-agency.dev'
15 'self-contained.'
13 'independently'
...
```

The longest token is `hello@astra-agency.dev` (22 chars) in the contact paragraph.
Reasoned estimate: a 320px viewport has ~320 − 2×24px gutter ≈ 272px of content width;
22 chars at 16px sans ≈ 150–170px — comfortably inside. **No fixed-width container can
overflow** because none has a fixed px width larger than its content area.

Caveat (honest): there is **no** `word-break` / `overflow-wrap` / `hyphens` / `white-space`
rule anywhere (`grep ... -> exit=1`), and no `overflow-x` guard. A single future token longer
than ~34 chars (or a wide user-injected string) inside the fixed-content boxes would push the
page wider than the viewport, because nothing caps the *minimum* inline size. For the current
copy this does not trigger. This is a latent robustness gap, not an active defect.

### W5b — missing asset (404) behaviour

```
$ curl -s -o /tmp/qaw/404body.txt -w "GET /assets/does-not-exist.svg -> %{http_code} bytes=%{size_download} ctype=%{content_type}\n" "$BASE/assets/does-not-exist.svg"
GET /assets/does-not-exist.svg -> 404 bytes=335 ctype=text/html;charset=utf-8
--- body ---
<!DOCTYPE HTML>
<html lang="en">
    <head>...<title>Error response</title>...</head>
    <body><h1>Error response</h1><p>Error code: 404</p><p>Message: File not found.</p>...</body>
</html>
```

Findings if an image/svg 404s:
- The server returns a plain 404 HTML page (no image bytes). A browser rendering that as an
  `<img>` shows a broken-image placeholder; because every `<img>` here carries explicit
  `width`/`height` **attributes** plus CSS `max-width:100%; height:auto`, the box keeps its
  reserved dimensions — **layout does not collapse**.
- Hero/header lockup `<img>` has a real `alt` ("AI ASTRA AGENCY"), so the accessible name
  survives a 404.
- The footer mark `<img>` has `alt=""` + `aria-hidden="true"` (decorative), so a 404 there is
  silently ignored by AT — acceptable for decoration.
- The three inline `<svg>` icons are inline markup (not fetched), so they cannot 404.
- Risk: the brand wordmark is *entirely* an SVG image (no live-text fallback in the header),
  so a header-lockup 404 would leave only the alt text as the visible brand. Minor.

### W5c — 320px viewport horizontal-overflow reasoning (STATIC assessment)

**This is a static (non-browser) assessment.** I have no headless browser in this environment,
so I cannot measure a real layout or a real scroll width. I reason only from the CSS.

Evidence:
- `.wrap { width: 100%; max-width: 68rem; margin-inline: auto; padding-inline: var(--gutter) }`
  — the only page container is fluid; `--gutter` is `24px` (or `32px` at ≥60em). At 320px the
  container = 320px minus 48px padding = 272px content. **No `100vw`.** (`grep -nE "100vw"` → none.)
- All grids use `minmax(0, 1fr)`:
  `.hero-facts { grid-template-columns: repeat(3, minmax(0,1fr)) }`,
  `.cards`/`.steps` default `1fr` then `repeat(2, minmax(0,1fr))` at ≥40em and
  `repeat(4, minmax(0,1fr))` at ≥60em. The `minmax(0, 1fr)` `0` min-track prevents grid
  items from forcing overflow. **PASS by construction.**
- Media queries present: `@media (max-width: 26em)` (brand shrink), `(min-width: 40em)`,
  `(min-width: 60em)`, plus three `(prefers-reduced-motion: reduce)`. All mobile-first.
- No negative `margin` anywhere (`grep -nE "margin[^:]*:\s*-"` → none); the only negative
  length is `translateY(-1px)` on hover.
- Absolutely-positioned items (`.skip-link` at `left:-9999px`; `.step-num` inside a padded
  `.step`) are out of flow and do not widen the page.
- `img, svg { max-width: 100%; height: auto }` prevents media from exceeding its box.
- **No `overflow-x: hidden` guard exists.** Overflow is avoided by construction, not masked.

**Conclusion (static): a 320px viewport would NOT horizontally overflow** for the delivered
content, because the container is fluid, every grid track uses `minmax(0,1fr)`, there are no
fixed-width layout boxes, no `100vw`, and no negative margins. **What this cannot prove:**
it does not measure real rendered/scroll width; it cannot catch sub-pixel overflow from a
particular font's glyph widths, and the absence of `overflow-wrap`/`overflow-x` means a
future over-long unbreakable token would overflow (see W5a caveat).

---

## Defects / findings

**D1 (LOW / accessibility nit, literal W3 sub-check FAIL) — decorative footer `<img>` has empty alt.**
`index.html:161`: `<img src="assets/brand/astra-mark-dark.svg" alt="" width="24" height="24" aria-hidden="true">`.
- The acceptance text says "every `<img>` has a non-empty alt". Taken literally → **FAIL**.
- By WCAG 2.2 SC 1.1.1, a purely decorative image SHOULD have `alt=""` (optionally with
  `aria-hidden="true"`). This is the **correct** pattern for a decorative footer mark that
  sits next to the live text "AI ASTRA AGENCY". So the *implementation is right*; the
  *frozen criterion as written* is not met by this element.
- **Discrepancy with the author:** the author's `VERIFY.md` claims "imgs missing alt: NONE",
  but `verify_site.py` contains **no `alt` check at all** (verified: `grep -nE "alt|img|svg"
  verify_site.py` returns only URL/external-ref logic, no `alt` inspection). The author's
  alt claim is therefore **unsubstantiated by their own script** — I could not reproduce it.
- Repro: `python3 w3.py` → section W3d → `imgs missing non-empty alt: ['assets/brand/astra-mark-dark.svg']`.

**D2 (INFO) — no `word-break`/`overflow-wrap`/`overflow-x` guard.** Latent; not triggered by
current content. See W5a.

**D3 (INFO, environment — not a deliverable defect) — server exposes non-page files.**
The runtime serves the whole directory (`server: SimpleHTTP/0.6`). `GET /VERIFY.md -> 200`,
`GET /verify_site.py -> 200`. No secret is exposed (only the author's own docs/script), but the
"document root == project folder" means the verification script and notes are publicly
downloadable. Recommend serving only `index.html` + `styles.css` + `main.js` + `assets/`.

---

## Verdict summary

| Criterion | Result | Basis |
|---|---|---|
| W1 URL 200 + stability + assets | **PASS** | 52/52 requests `200`; all 5 assets `200` |
| W2 byte-identity | **PASS** | md5 `6829df56…` matches source, `/`, `/index.html`; all assets match |
| W3 HTML validity/structure | **FAIL (1 sub-check)** | strict parse PASS, ids/anchors/headings/lang/viewport PASS; 1 `<img alt="">` violates literal rule (D1) |
| W4 no-JS + no external requests | **PASS** | 0 external refs; 0 fetch/XHR/eval; all content in static HTML |
| W5 break tests | **PASS (static)** | no fixed-width layout box; `minmax(0,1fr)`; no 100vw/neg-margin; 404 keeps layout; caveats stated |

**Overall: 4/5 PASS, W3 FAIL on the literal "non-empty alt" rule (D1).** No blocking
defect; the single failure is a defensible decorative-image pattern that the frozen
criterion disallows as written. Honest limitation: W5 is a static CSS assessment, not a
browser measurement.

---

### Reproduction (all commands)

```
# W1
URL="https://work-1-lkpxywjdeyhpzogp.prod-runtime.all-hands.dev/"
for i in $(seq 1 12); do curl -s -o /dev/null -w "%{http_code} %{time_total}\n" "$URL"; sleep 2.5; done
for p in styles.css main.js assets/favicon.svg assets/brand/astra-lockup-horizontal-dark.svg assets/brand/astra-mark-dark.svg; do
  curl -s -o /dev/null -w "$p -> %{http_code} %{size_download}\n" "$URL/$p"; done
# W2
curl -s -o /tmp/root.html "$URL/"; curl -s -o /tmp/idx.html "$URL/index.html"
md5sum /tmp/root.html /tmp/idx.html /workspace/project/deliveries/astra-launch/website/index.html
cmp /workspace/project/deliveries/astra-launch/website/index.html /tmp/root.html && echo IDENTICAL
# W3 / W4 / W5
python3 /tmp/qaw/w3.py
grep -rniE "https?://" index.html styles.css main.js
grep -rniE "fetch\(|XMLHttpRequest|eval\(|document\.write" index.html styles.css main.js
grep -oE "[0-9]*\.?[0-9]+px" styles.css | sort -u
```
