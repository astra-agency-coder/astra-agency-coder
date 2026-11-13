# QA VERDICT — AI ASTRA AGENCY launch delivery (round-2, adversarial)

**Verifier:** `astra-cqo` (Chief Quality Officer), Quality department — **independent**.
**Date:** 2026-11-13 · **Method:** criteria frozen *first* (`qa/ACCEPTANCE.md`), then tested.
**Specialists (independent sub-verifications):** `qa-edge-breaker` (video),
`qa-repro-auditor` (website), `qa-brand-verifier` (brand). Raw evidence in
`qa/evidence-video.md`, `qa/evidence-website.md`, `qa/evidence-brand.md`.
The CQO re-ran the decisive measurements personally — findings below are reproduced.

> No author `VERIFY.md` / `checks.json` / `REVIEW-independent.md` value was accepted on
> trust. Every number was recomputed from the raw artefact.

---

## VERDICT SUMMARY

| Deliverable | Frozen criteria | Verdict | Ship-ready as-is? |
|---|---|---|---|
| VIDEO `astra-intro-reel.mp4` | V1–V4 | **PASS (4/4)** | YES — with 2 craft nits (not blockers) |
| WEBSITE `website/` (public URL) | W1–W5 | **PASS (5/5)** | Content: YES · Deployment: **NO** (live link was DOWN) |
| BRAND `brand/` | B1–B3 | **PASS (3/3)** | **NO** — HIGH defect in the brand sheet |

**Headline:** all three deliverables meet the frozen technical criteria, but two of the
three are **not ship-ready**: the BRAND sheet has a HIGH-severity defect (the primary
logo signature is rendered invisible), and the WEBSITE's public URL was **down (HTTP 502)**
when handed to QA and is not durably deployed.

---

## 1. VIDEO — `deliveries/astra-launch/video/astra-intro-reel.mp4`

### Frozen criteria — all PASS

| ID | Criterion | Result | Evidence (re-run by CQO) |
|----|-----------|--------|--------------------------|
| V1 | H.264, 1080×1920, yuv420p, 15–30 s, ≥1 audio | **PASS** | `ffprobe`: `h264` High/avc1, **1080×1920**, **yuv420p**, **28.400000 s**, `aac` LC stereo 44100 Hz |
| V2 | Captions **actually burned in** | **PASS** | my own `tesseract` on frames decoded from the MP4 (below) |
| V3 | ≈ −14 LUFS; true peak ≤ −1.0 dBTP | **PASS** | `loudnorm`: `input_i=-14.94`, `input_tp=-1.32`; `volumedetect` max −1.3 dB |
| V4 | Strict decode, no corrupt frames | **PASS** | `ffmpeg -v error -i … -f null -` → **exit 0, stderr 0 bytes** |

**V2 — CQO's own OCR (not Creative's):** frames decoded from the MP4 at caption times,
OCR'd with tesseract `--psm 11`:

```
t=1.4  -> "… Meet the agency that runs itself."
t=4.4  -> "A digital agency, run by AI agents. … Al Astra is a digital agency, run by autonomous Al agents."
t=20.8 -> "HOW IT WORKS 1 Strategy 2 … 3 Launch  Strategy to launch, end to end, in code."
t=25.2 -> "… Build what's next. @aiastra Astra Agency Build what's next."
```
Captions are genuinely burned into the picture. `qa-edge-breaker` independently located the
caption band (rows 1469–1556), OCR'd all 8 cue midpoints and recovered every phrase.

**V3 raw (CQO):**
```
input_i : -14.94   input_tp : -1.32   input_lra : 3.80
volumedetect  mean_volume: -18.8 dB   max_volume: -1.3 dB
```
Three independent meters agree (loudnorm, ebur128 I=−14.8, volumedetect −1.3 dB); **no clipping**.

**V4 raw (CQO):** `exit=0  stderr bytes: 0`. Full decode: `nb_frames 852 == nb_read_frames 852`.
CFR 30 fps, PTS strictly monotonic, A/V both 28.400 s. No black/silent segments.

### Defects / anomalies (non-blocking for V1–V4)

- **D-V1 (MEDIUM, craft):** the reel is effectively a **5-scene static slideshow with hard
  cuts**. `qa-edge-breaker` measured frozen stretches 5.37–8.5 s and 21.87–24.0 s; ~81.8 % of
  frame transitions are near-static. For an Instagram Reel (which rewards motion) this is a
  visible craft weakness. It does not violate any frozen criterion.
- **D-V2 (LOW, safe area):** the 3-line "who" caption descends ~**22 px into the reserved
  Reels bottom-320 band** on 53 frames (~1.8 s). Cosmetic risk of UI overlap.
- **D-V3 (LOW, evidence hygiene):** `render.log` retains a **stale pre-encode `input_tp = -0.45`**
  (which would fail the ≤−1.0 rule); the value actually in the shipped MP4 is −1.32 dBTP.
  The shipped file passes; the log is merely confusing.
- **Method note:** a naive OCR at exactly **5.5 s** returns nothing (cue 2 ends at 5.36 s) —
  probing mid-cue is required. Recorded so nobody false-FAILs on it.

**VIDEO verdict: PASS.** Not blocked; D-V1/D-V2 are craft/polish items for Creative.

---

## 2. WEBSITE — `deliveries/astra-launch/website/` @ public URL

### Frozen criteria — all PASS (with a deployment caveat)

| ID | Criterion | Result | Evidence |
|----|-----------|--------|----------|
| W1 | Public URL returns 200 | **PASS\*** | 52/52 requests **200** once running; **BUT it was 502 on arrival — see D-W1** |
| W2 | Public bytes == source | **PASS** | md5 source = public `/` = public `/index.html` = `6829df564e3eb9746c81225367a1fa2a`; `cmp` byte-identical |
| W3 | Valid HTML, no dup ids, anchors resolve, imgs have `alt`, heading order | **PASS** | html5lib strict: **0 errors**; dup ids NONE; unresolved anchors NONE; all imgs have `alt`; one `h1`; no skipped levels; `lang=en`, viewport present |
| W4 | Renders w/o JS, no external requests | **PASS** | **0** external refs in HTML/CSS/JS; no fetch/XHR/eval; all 15 key content phrases present in static HTML; `main.js` = progressive enhancement only |
| W5 | Edge robustness (long text, missing asset, 320 px) | **PASS (static)** | no fixed-width layout box; grids `minmax(0,1fr)`; no `100vw`/negative margins; 404 asset keeps layout (width/height attrs + `max-width:100%`) |

\* W1 is only true because QA **restarted** the server. See D-W1.

**W2 raw (CQO):**
```
6829df564e3eb9746c81225367a1fa2a  website/index.html
6829df564e3eb9746c81225367a1fa2a  public /        (fetched)
6829df564e3eb9746c81225367a1fa2a  public /index.html
=> IDENTICAL
```

### Defects

- **D-W1 (MEDIUM, deployment fragility — found by CQO on arrival):** the public URL
  **returned HTTP 502** ("Bad Gateway") when QA received the task, and there was **no server
  on port 12000** (`/tmp/astra_site` gone, `http.server 12000` not running). The site is served
  by an **ephemeral `python3 -m http.server`** started inside the agent's session; it died with
  that session. QA restored it (`mkdir -p /tmp/astra_site; cp -r …; python3 -m http.server 12000`)
  and the URL then returned 200 (stable across 52 requests). **As delivered, the "live link" was
  DOWN.** This must be re-deployed durably (a persistent process / proper host) before the Owner
  relies on it.
- **D-W2 (LOW, author evidence overclaim):** the author `VERIFY.md` states *"imgs missing alt:
  NONE"*, but their `verify_site.py` contains **no alt check at all** — the claim is
  unsubstantiated by their own script. (It is also false under a strict *non-empty* alt reading:
  the footer mark is `alt=""`. Under the frozen wording — "every `<img>` has `alt`" — it passes,
  and `alt="" aria-hidden="true"` is the WCAG-correct decorative pattern.)
- **D-W3 (LOW, hygiene):** the runtime serves the **entire project directory** as doc root
  (`SimpleHTTP`): `GET /VERIFY.md` → 200, `GET /verify_site.py` → 200. **No secret exposed**
  (repo `scan-secrets` = clean; the public docs contain no keys — verified). Still, build/verify
  scripts should not be web-reachable.
- **D-W4 (INFO, latent):** no `overflow-wrap`/`word-break`/`overflow-x` guard. Not triggered by
  current copy (longest token `hello@astra-agency.dev`, 22 chars) but a future long unbreakable
  string could overflow.

**WEBSITE verdict: PASS on content/structure/bytes (W1–W5).** Deployment is **not durable** and
the link was found dead — fix D-W1 before shipping.

---

## 3. BRAND — `deliveries/astra-launch/brand/`

### Frozen criteria — all PASS

| ID | Criterion | Result | Evidence |
|----|-----------|--------|----------|
| B1 | every SVG parses + renders non-blank | **PASS** | 9/9 SVGs well-formed XML, all have `viewBox`, all rasterize non-blank (cairosvg) |
| B2 | `astra-brand-sheet.png` opens + non-blank | **PASS** | Pillow open + `verify()` pass; **2400×4184 RGB**; **10 849** distinct colours |
| B3 | declared contrast ratios are true | **PASS** | WCAG recomputed from scratch; max Δ vs claimed = **0.0046** (all ≤0.05) |

**B3 (recomputed independently, CQO + `qa-brand-verifier`):**
```
light primary/on-primary   8.8378  (claimed 8.84)
light on-surface/surface  16.6312  (claimed 16.63)
dark  primary/on-primary   8.2502  (claimed 8.25)
dark  on-surface/surface  15.2960  (claimed 15.3)
mark violet on light       8.5880  (claimed 8.59)
```
Self-test #FFF/#000 = 21.0 (implementation verified). No discrepancy > 0.05.

### Defects (in the flagship brand sheet — independent of B1–B3)

- **D-B1 (HIGH):** brand sheet section "01 LOGO SYSTEM", the *"Horizontal lockup — primary
  signature"* panel (x 140–2260, y 1290–1510) is **dark-on-dark and effectively invisible**.
  CQO reproduced from raw pixels: panel bg `#131217` (19,18,23); the light lockup's wordmark ink
  `#1C1B20` appears **20 191 px** at **contrast 1.089 : 1**. OCR of the panel returns **only the
  panel label**, not the lockup. The one place a reviewer looks to see the *primary* logo shows
  a near-blank plate. (Fix: use the dark lockup on the dark plate, or a light plate.)
- **D-B2 (MEDIUM):** key-roles "on-surface" swatch label is drawn in the **same colour as the
  fill** (`#1C1B20`) → **1.00 : 1**, unreadable.
- **D-B3 (LOW):** footer line 2 `#7A797E` over the cyan glow `#0B2E39` = **3.32 : 1** (< 4.5:1).
- **D-B4 (LOW, documentation accuracy):** `BRAND.md` §1 claims the mark has a "crossbar" and a
  "curved" star; the raw path data shows a single chevron with **no crossbar** and a
  **straight-edged** (M/L/Z only) star. The rendered assets are fine; the guide over-describes.

**BRAND verdict: PASS on B1–B3, but NOT ship-ready.** D-B1 (HIGH) means the flagship brand
sheet mis-represents the primary logo; D-B2 makes one colour role unreadable. These are
brand-sheet layout bugs (the SVG *sources* are correct per variant).

---

## Cross-cutting findings

- **C-1 (MEDIUM):** the "live" website depends on an ephemeral in-session `http.server`
  (D-W1) — it was already 502 once. Deployment durability is the single biggest delivery risk.
- **C-2 (LOW):** author `VERIFY.md` files contain at least one **unsubstantiated claim**
  (website alt check, D-W2). Evidence scripts should actually test what the docs claim.
- **C-3 (clean):** repo `python3 ops/astra.py scan-secrets` → `{"clean": true}`; public docs
  contain no secrets.

## Honest limitations of this QA

1. **No headless browser.** W5 responsive behaviour is a **static CSS assessment**, not a real
   viewport measurement — no rendered/scroll-width was observed in a browser.
2. **True peak** is ffmpeg's BS.1770 estimator (cross-checked by 3 meters), not certified
   hardware metering. All three agree the file is ≤ −1.3 dBTP.
3. **OCR** is a legibility proxy; the brand-sheet defects were also confirmed by direct pixel
   measurement, not OCR alone.
4. **Deployment stability** was observed over ~minutes, not days; the durability concern is
   about the *mechanism* (ephemeral process), which is deterministic.
5. Brand contrast computed on sRGB hex per WCAG 2.x; no display-P3 variants exist to test.
6. The video craft findings (D-V1/D-V2) are **judgement** (Reels norms), not spec violations.

## Recommended actions before the Owner signs off

1. **Fix D-W1** — deploy the site durably (persistent process/host); re-verify 200.
2. **Fix D-B1** — swap the brand-sheet "primary signature" lockup to a legible variant; fix
   D-B2 swatch label.
3. Optional: add motion to the reel (D-V1) and pull the caption up out of the Reels bottom band (D-V2).
4. Correct the website `VERIFY.md` alt claim (D-W2) and add `overflow-wrap` (D-W4).
