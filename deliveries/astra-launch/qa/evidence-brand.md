# Independent QA evidence — BRAND deliverable

**Verifier:** `qa-brand-verifier` (Quality dept; independent of the author `astra-ccr`)
**Date:** 2026-11-13
**Target:** `/workspace/project/deliveries/astra-launch/brand/` (read-only)
**Method:** every number below was recomputed from the raw files with my own scripts run in
`/tmp/qa-brand/`. The author's `checks.json` / `VERIFY.md` and the Creative
`REVIEW-independent.md` were treated as *claims to falsify*, not as sources of truth.

**Tooling (verified present, no installs):** Pillow 11.3.0, numpy 2.5.4, cairosvg 2.9.1,
`xml.etree.ElementTree`, tesseract 5.5.0.

**Summary:** B1 **PASS** · B2 **PASS** · B3 **PASS** (0 discrepancies > 0.05). Two real
content defects reproduced independently (HIGH + MEDIUM) on the brand sheet — they are
*not* among the B1–B3 frozen criteria but are reported as defects.

---

## B1 — Every *.svg parses as XML AND renders non-blank — **PASS**

### Command
```bash
python3 /tmp/qa-brand/b1_svg2.py
```
Script parses each SVG with `xml.etree.ElementTree`, reads `viewBox`, then rasterizes at
**native size** with `cairosvg.svg2png(url=...)` and counts `alpha>0` pixels and distinct
colours restricted to opaque pixels.

### Raw output
```
SVG count: 9
========================================================================================================
file                                     parse viewBox                txt raster(px)     opaque(a>0) distinct@opaque
--------------------------------------------------------------------------------------------------------
astra-lockup-horizontal-dark.svg         True  0 0 1253.2 174.0       0   (1253, 174)    25249       199
astra-lockup-horizontal-light.svg        True  0 0 1253.2 174.0       0   (1253, 174)    25249       157
astra-mark-dark.svg                      True  0 0 512 512            0   (512, 512)     62024       123
astra-mark-light.svg                     True  0 0 512 512            0   (512, 512)     62024       104
astra-mark-mono-black.svg                True  0 0 512 512            0   (512, 512)     62024       1
astra-mark-mono-white.svg                True  0 0 512 512            0   (512, 512)     62024       1
astra-mark.svg                           True  0 0 512 512            0   (512, 512)     62024       104
astra-wordmark-dark.svg                  True  -0.7 -68.3 1033.2 69.6 0   (1033, 70)     27490       81
astra-wordmark-light.svg                 True  -0.7 -68.3 1033.2 69.6 0   (1033, 70)     27490       62
```

### Per-file result

| File | XML parse | viewBox | opaque px (α>0) | distinct @opaque | non-blank | Verdict |
|---|---|---|---|---|---|---|
| astra-lockup-horizontal-dark.svg | OK | `0 0 1253.2 174.0` | 25 249 | 199 | yes | PASS |
| astra-lockup-horizontal-light.svg | OK | `0 0 1253.2 174.0` | 25 249 | 157 | yes | PASS |
| astra-mark-dark.svg | OK | `0 0 512 512` | 62 024 | 123 | yes | PASS |
| astra-mark-light.svg | OK | `0 0 512 512` | 62 024 | 104 | yes | PASS |
| astra-mark-mono-black.svg | OK | `0 0 512 512` | 62 024 | 1 (pure #000) | yes | PASS |
| astra-mark-mono-white.svg | OK | `0 0 512 512` | 62 024 | 1 (pure #FFF) | yes | PASS |
| astra-mark.svg | OK | `0 0 512 512` | 62 024 | 104 | yes | PASS |
| astra-wordmark-dark.svg | OK | `-0.7 -68.3 1033.2 69.6` | 27 490 | 81 | yes | PASS |
| astra-wordmark-light.svg | OK | `-0.7 -68.3 1033.2 69.6` | 27 490 | 62 | yes | PASS |

Notes:
- All 9 files parse as well-formed XML; all have a `viewBox`; all render to non-blank rasters.
- 0 `<text>` elements across all SVGs (counted by iterating elements) — wordmarks are true
  vector outlines, so the "no font dependency" claim holds.
- The two mono marks render as a single colour (1 distinct opaque colour) by design — they
  are still non-blank (62 024 opaque px each).
- `astra-mark.svg` is byte-identical to `astra-mark-light.svg` (md5 `d23985371ac16cbbb3fac892380bd8fe`
  for both, from `md5sum *.svg`) — a documented alias, not a defect.

**B1 = PASS.**

---

## B2 — astra-brand-sheet.png opens, `verify()` passes, non-blank — **PASS**

### Command
```bash
python3 /tmp/qa-brand/b2_png.py
```
Opens every PNG, runs `Image.verify()`, then re-opens for `size`/`mode`/distinct-colour count.

### Raw output (all 11 PNGs)
```
PNG count: 11
========================================================================================================
file                                         size         mode   verify()  distinct  mean    std
--------------------------------------------------------------------------------------------------------
astra-brand-sheet.png                        (2400, 4184) RGB    pass      10849       52.56   69.84
logo-lockup-dark-2000x300.png                (2000, 300)  RGB    pass      543         35.86   65.27
logo-lockup-dark-transparent-2000x300.png    (2000, 300)  RGBA   pass      208         25.70   71.69
logo-lockup-light-2000x300.png               (2000, 300)  RGB    pass      540        230.06   65.35
logo-lockup-light-transparent-2000x300.png   (2000, 300)  RGBA   pass      171          4.96   18.54
logo-mark-dark-1024.png                      (1024, 1024) RGBA   pass      126         48.11   87.93
logo-mark-light-1024.png                     (1024, 1024) RGBA   pass      106         23.51   48.92
logo-mark-mono-black-1024.png                (1024, 1024) RGB    pass      202        195.79  107.50
logo-mark-mono-white-1024.png                (1024, 1024) RGB    pass      202         59.21  107.50
logo-mark-on-dark-1024.png                   (1024, 1024) RGB    pass      284         57.64   82.14
logo-mark-on-light-1024.png                  (1024, 1024) RGB    pass      279        217.29   68.59
```

### Brand-sheet specifics (criterion B2)
- **Opens:** yes (Pillow).
- **`Image.verify()`:** **pass** (no exception).
- **Size:** **2400 × 4184**, mode RGB — matches the author's `checks.json` claim (2400×4184).
- **Non-blank:** **10 849 distinct colours**, mean 52.56, std 69.84 → clearly non-blank.

### Edge / overrun cross-check (adversarial)
Command `python3 /tmp/qa-brand/edges.py`:
```
top     min=(11, 10, 18) max=(40, 21, 68)
bottom  min=(11, 10, 18) max=(11, 46, 57)
left    min=(11, 10, 18) max=(11, 46, 57)
right   min=(11, 10, 18) max=(40, 21, 68)
edge pixels with sum(RGB)>300 (bright/content-like): 0
```
All four border rows/cols are pure background gradient (max RGB sum 148, zero bright
pixels) → **no content overruns the canvas.**

**B2 = PASS.**

---

## B3 — WCAG contrast recomputed from scratch — **PASS** (0 discrepancies > 0.05)

### Method
`/tmp/qa-brand/b3_contrast.py` re-implements WCAG 2.x relative luminance from scratch
(sRGB→linear per-channel, coefficients 0.2126/0.7152/0.0722, ratio `(L1+0.05)/(L2+0.05)`),
**no external colour library**. Self-test on known values:
```
#FFFFFF vs #000000 = 21.0 (expect 21.0)
#FFFFFF vs #FFFFFF = 1.0  (expect 1.0)
```
`/tmp/qa-brand/b3_tokens.py` then pulls the fg/bg hex values *directly from tokens.json*
(`color.sys_resolved` / `color.ref`) and compares to `checks.json → contrast`.

### Token-integrity cross-check (raw output)
```
color.ref entries: 44
unbacked sys entries: []
sys_resolved mismatches: 0
```

### Computed vs claimed (raw output)
```
pair                                   computed  claimed  diff    flag
----------------------------------------------------------------------------
light primary/on-primary                  8.8378 8.84      0.0022 OK
light on-surface/surface                 16.6312 16.63     0.0012 OK
light secondary/on-secondary              4.8307 4.83      0.0007 OK
light tertiary/on-tertiary                4.7344 4.73      0.0044 OK
dark primary/on-primary                   8.2502 8.25      0.0002 OK
dark on-surface/surface                  15.2960 15.3      0.0040 OK
dark secondary/on-secondary              10.5154 10.52     0.0046 OK
dark tertiary/on-tertiary                 9.5812 9.58      0.0012 OK
mark violet on light surface              8.5880 8.59      0.0020 OK
mark light-violet on dark surface        10.2702 10.27     0.0002 OK

max |computed-claimed| = 0.0046 -> threshold 0.05 -> PASS
```

### Required pairs — detail

| Pair | fg (token) | bg (token) | My ratio | Claimed | Δ | Flag (>0.05) |
|---|---|---|---|---|---|---|
| light primary / on-primary | #5A2EA6 | #FFFFFF | **8.8378** | 8.84 | 0.0022 | none |
| light on-surface / surface | #1C1B20 | #FDFBFE | **16.6312** | 16.63 | 0.0012 | none |
| dark primary / on-primary | #C9B0F0 | #2D1450 | **8.2502** | 8.25 | 0.0002 | none |
| dark on-surface / surface | #E6E1E9 | #0B0A12 | **15.2960** | 15.3 | 0.0040 | none |
| mark violet on light surface | #5A2EA6 | #FDFBFE | **8.5880** | 8.59 | 0.0020 | none |

**Largest deviation across all 10 pairs = 0.0046, well under the 0.05 threshold.**
No pair fails the >0.05 discrepancy flag. **B3 = PASS.**

---

## Adversarial checks (beyond B1–B3) — defects reproduced independently

### Mark-colour presence (claimed in VERIFY.md) — **CONFIRMED**
Command `python3 /tmp/qa-brand/adversarial.py`:
```
== claimed mark-colour presence (VERIFY.md) ==
on-light: {'#5A2EA6': 229816, '#0D7D8F': 11382}
on-dark : {'#C9B0F0': 229816, '#8FDBE4': 11382}
light mark png: {'#5A2EA6': 230856, '#0D7D8F': 11674}
dark  mark png: {'#C9B0F0': 231096, '#8FDBE4': 11652}
```
All expected hexes present in the rasters — the author's claim is true.

### SVG fill colours per variant (copy-paste defect scan)
```
astra-lockup-horizontal-dark.svg  -> #8FDBE4, #C9B0F0, #E6E1E9   (correct dark palette)
astra-lockup-horizontal-light.svg -> #0D7D8F, #1C1B20, #5A2EA6   (correct light palette)
astra-mark-dark.svg               -> #8FDBE4, #C9B0F0
astra-mark-light.svg              -> #0D7D8F, #5A2EA6
astra-mark-mono-black.svg         -> #000000 x2
astra-mark-mono-white.svg         -> #FFFFFF x2
astra-mark.svg                    -> #0D7D8F, #5A2EA6
astra-wordmark-dark.svg           -> #E6E1E9
astra-wordmark-light.svg          -> #1C1B20
```
No swapped/wrong fills in any source SVG. **The defects below are brand-sheet layout
defects, not SVG-source defects.**

### DEFECT-1 (HIGH) — brand sheet "primary signature" lockup panel is dark-on-dark
Command `python3 /tmp/qa-brand/adversarial.py`, region y 1290–1510, x 140–2260:
```
top colours in panel band (colour:count):
    (19, 18, 23) 430383      <- panel bg #131217 (neutral-10)
    (28, 27, 32) 20191       <- light on-surface ink #1C1B20
    (90, 46, 166) 5054       <- violet #5A2EA6
    (203, 201, 207) 2905
count #1C1B20 (light on-surface) in band: 20191
count #131217 (neutral-10 panel bg?) in band: 430383
```
Recomputed contrasts (`adversarial2.py`):
```
HIGH  lockup ink #1C1B20 on panel bg #131217 = 1.09
      panel violet #5A2EA6 on #131217        = 2.11
      panel cyan   #0D7D8F on #131217        = 3.86
```
A **light** lockup (wordmark ink `#1C1B20`) is pasted onto a **dark** `#131217` plate →
**1.09:1**, effectively invisible. This reproduces the Creative review's HIGH finding from
raw pixels. (OCR below confirms the wordmark there is not machine-readable.)

### DEFECT-2 (MEDIUM) — brand sheet key-roles "on-surface" swatch label invisible
Command `python3 /tmp/qa-brand/adversarial.py`, region x 1567–1903, y 2656–2806:
```
    (28, 27, 32) 50207       <- swatch fill #1C1B20
    (11, 10, 18) 193         <- panel bg only
count #1C1B20: 50207
distinct colours in swatch: 2
MED   swatch fill #1C1B20 with label #1C1B20 = 1.0
```
The swatch fill is `#1C1B20` and the label is drawn in the **same** colour → 1.00:1; the
swatch interior contains only the fill (no distinct label ink). Reproduces the MEDIUM
finding. (OCR reads "surface inverse-surface" but the `on-surface` label is absent.)

### DEFECT-3 (LOW) — footer line 2 under-contrast over the cyan glow
Command `python3 /tmp/qa-brand/adversarial2.py`, footer band y 4100–4135:
```
    (11, 46, 57) 30305       <- local cyan-glow bg #0B2E39
    (122, 121, 126) 3209     <- text #7A797E (neutral-50)
   contrast #7A797E vs #0B2E39 (glow): 3.32
   contrast #7A797E vs #0B0A12 (plain): 4.56
```
Footer line 2 (`#7A797E`) drops to **3.32:1** where it crosses the glow — below the 4.5:1
small-text threshold. Reproduces the LOW finding.

### OCR (supporting legibility evidence)
`tesseract astra-brand-sheet.png sheet_ocr` → 249 words. Relevant excerpt:
```
01 LOGO SYSTEM
A A A
Mark - light bg Mark - dark bg Mono black Mono white
Horizontal lockup —
+ primary signature
...
Key roles (resolved)
surface inverse-surface
#FDEBFE #313036
```
The "Horizontal lockup — primary signature" label reads back, but the lockup artwork
itself yields no legible text (only the stray "A A A" from the mark row) — consistent with
DEFECT-1. The key-roles row yields "surface" and "inverse-surface" but **no `on-surface`
label** — consistent with DEFECT-2. ("#FDEBFE" is OCR mis-reading of #FDFBFE.)

### Note on BRAND.md construction claim (documentation, not a B-criterion)
`BRAND.md` §1 describes "two nested chevron strokes with a crossbar" and a "curved" star.
From the raw SVG path data (e.g. `astra-mark-light.svg`) the mark is a **single 6-vertex
chevron polygon** with **no crossbar**, and the star path uses only `M/L/Z` (8 straight
vertices, no curve commands; `C/Q/A/S` absent anywhere in the mark). This is a
documentation over-claim; it does not affect any rendered asset. (I confirm the raw path
data; I did not re-derive the ink map.)

---

## Verdict

| Criterion | Result | Evidence |
|---|---|---|
| **B1** every SVG parses + renders non-blank | **PASS** | 9/9 parse; 9/9 non-blank; viewBoxes + opaque-pixel counts tabulated |
| **B2** brand sheet opens, verify() passes, non-blank | **PASS** | 2400×4184 RGB, verify() pass, 10 849 distinct colours |
| **B3** WCAG ratios recomputed vs claimed | **PASS** | max Δ = 0.0046 (< 0.05); 0 discrepancies flagged |

**Defects found (not part of B1–B3):** 1 HIGH (brand sheet lockup panel dark-on-dark,
1.09:1), 1 MEDIUM (key-roles `on-surface` swatch label = fill, 1.00:1), 1 LOW (footer line 2
3.32:1 over glow). All three independently reproduced from raw pixels.

## Honest limitations
- Contrast is computed on sRGB hex values per the WCAG 2.x formula; no display-P3/non-sRGB
  variants are provided, so none were tested.
- B1 "non-blank" is measured as `alpha>0` pixel count plus distinct-opaque-colour count; a
  raster with ≥1 opaque pixel passes — this does not judge aesthetic quality.
- OCR is a legibility proxy; DEFECT-1/2 were also confirmed by direct pixel measurement,
  not OCR alone.
- The BRAND.md geometry note was assessed from raw path commands only (no rendered ink map
  in this pass); it is a documentation-accuracy observation, not a deliverable defect.
- I did not modify any file in `deliveries/astra-launch/brand/`; only this evidence file was
  written.
