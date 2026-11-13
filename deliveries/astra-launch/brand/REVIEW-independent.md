# Independent design review — AI ASTRA AGENCY brand deliverables

**Auditor:** `astra-design-critic` (independent; did not author these files)
**Date:** 2026-11-13
**Scope:** `/workspace/project/deliveries/astra-launch/brand/` (read-only audit)

## Method

Everything below was measured from the files on disk with my own scripts; no value is
copied from the author's `checks.json` / `VERIFY.md` without independent re-derivation.

- **SVG:** parsed each `*.svg` with `xml.etree.ElementTree`, read `viewBox`, rendered
  each with **cairosvg** and counted opaque pixels / distinct colours in the raster.
- **Tokens:** re-implemented the ref→sys alias check and re-computed every
  `color.sys_resolved` value directly from `color.ref`.
- **Contrast:** re-implemented WCAG 2.x relative luminance and the `(L1+0.05)/(L2+0.05)`
  ratio from scratch; applied to declared token pairs, to the mark-vs-surface pairs, and
  to the *actual rendered pixels* of the brand sheet and logo rasters.
- **Rasters:** opened every PNG with Pillow, ran `Image.verify()`, counted distinct
  colours, and tested for the exact expected hexes.
- **Brand sheet:** 2400 px check, non-blank check, edge-ink / content-extent test for
  off-canvas overrun, **tesseract** OCR (whole sheet + tight region crops), and per-region
  pixel measurement of text-vs-background.
- **Geometry:** decomposed the mark's SVG path commands and rendered the mark to a
  per-row ink map to test the guide's construction claims.

---

## Findings

### 1. HIGH — "Primary signature" lockup panel is rendered dark-on-dark and is effectively invisible
**File/region:** `astra-brand-sheet.png`, "01 LOGO SYSTEM" section, the large rounded
panel spanning x 140–2260, y 1290–1510 (label *"Horizontal lockup — primary signature"*).
**Measured:** the panel background is `#131217` (`neutral-10`). Into it the builder pastes
`astra-lockup-horizontal-light.svg`, whose wordmark fill is `#1C1B20` (`on-surface` light).
Measured ink pixels of `#1C1B20` inside the panel = **20 191 px**, against a panel bg of
`#131217` → **contrast 1.09:1**. The pasted mark is also low-contrast on that panel:
violet `#5A2EA6` = **2.11:1**, star cyan `#0D7D8F` = **3.86:1**. A tight OCR crop of the
pasted lockup returns only a single stray glyph ("A"); the wordmark is not machine-readable.
**Why it matters:** this is the showcase of the *primary* logo signature on the flagship
brand sheet. It is the one place a reviewer would look to see the lockup, and it renders
essentially blank (dark text on a dark plate). A light lockup belongs on a light plate, or
the dark lockup variant should have been used here.

### 2. MEDIUM — Key-roles swatch "on-surface" label is invisible (ink = fill)
**File/region:** `astra-brand-sheet.png`, "02 COLOUR SYSTEM" → "Key roles (resolved)" row,
5th of 6 swatches, x ≈ 1567–1903, y 2656–2806.
**Measured:** the swatch fill is `#1C1B20` and the code draws the label with the *same*
colour (`on-surface` light) → **contrast 1.00:1**. A pixel scan of the swatch interior finds
only the fill colour and **zero** label-ink pixels; tesseract returns nothing legible from
the crop. The other five swatches are fine (measured: primary 8.84:1, secondary 4.83:1,
tertiary 4.73:1, surface 16.63:1, inverse-surface 13.07:1).
**Why it matters:** one of six key colour roles is presented without a readable name/value —
the reader cannot tell which chip is `on-surface` without counting.

### 3. LOW — Footer legal line drops to 3.32:1 over the cyan glow
**File/region:** `astra-brand-sheet.png`, footer line 2
(*"Fonts are DejaVu substitutes. Mark and palette are ASTRA's own; …"*), y ≈ 4109–4126,
left-aligned from x = 140.
**Measured:** text colour `#7A797E` (`neutral-50`). Where it crosses the bottom-left cyan
glow the local modal background is `#0B2E39` → **3.32:1**, below the 4.5:1 small-text
threshold. (On the plain cosmic bg `#0B0A12` the same line is 4.56:1; footer line 1
`#949499` is 4.75:1 over the glow and passes.)
**Why it matters:** it is small (24 px) supporting text at the very bottom of the sheet and
it is the line that carries the honesty disclosure; over the glow it is under-contrast.

### 4. LOW — `BRAND.md` over-describes the mark's construction (honesty/accuracy)
**File/region:** `BRAND.md` §1 ("Construction: two nested chevron strokes with a crossbar;
the star is the only curved element, deliberately contrasting the straight letterform.").
**Measured (from the actual path data / rendered ink map):**
- The A is a **single chevron polygon** (one `<path>`, 6 vertices), not "two nested chevron
  strokes".
- There is **no crossbar**. The centre column x=256 is filled only from y≈57–236 (the solid
  apex wedge); below the inner apex the counter is empty (background) until the star at
  y≈274. An A-with-crossbar would show a continuous centre bar; none exists.
- The star is **not curved**. Its path uses only `M`/`L`/`Z` (8 straight vertices, r_out 58 /
  r_in 18). In fact the **entire mark contains zero curve commands** (`C/Q/A/S` absent).
**Why it matters:** the guide's own construction note mis-states the geometry on two counts.
This does not affect the rendered assets, but it is an overclaim in the documentation and
should be corrected (the star is a straight-edged 4-point star; the A is a chevron with no
crossbar). Everything else in the honesty section checks out — see "What passes".

---

## What passes

- **SVG validity (all 9 files).** Every `*.svg` parses as XML, has a `viewBox`, and renders
  via cairosvg to a non-blank raster (e.g. `astra-mark*.svg` → 38 151 opaque px; lockups →
  3 102 px; wordmarks → 4 737 px). No `<text>` elements anywhere (wordmarks are true vector
  outlines) — the "no font dependency" claim is **verified**.
- **Token integrity.** `color.ref` has 44 entries. **0** `color.sys` values are unbacked;
  every `color.sys_resolved` value equals `ref[sys[key]]` for both light and dark (0
  mismatches). The ref→sys aliasing claim holds exactly.
- **Declared contrast pairs (independently recomputed, all match `checks.json`):**
  light primary/on-primary 8.84, light on-surface/surface 16.63, light secondary/on-secondary
  4.83, light tertiary/on-tertiary 4.73, dark primary/on-primary 8.25, dark on-surface/surface
  15.30, dark secondary/on-secondary 10.52, dark tertiary/on-tertiary 9.58 — all ≥ 4.5:1.
  I also checked the *undeclared* pairs: every one is ≥ 4.5:1 **except** `light outline/surface`
  (4.20:1, but outline is a non-text role so 3:1 applies → passes).
- **Mark contrast vs its actual rendered background:** measured from pixels, not tokens —
  `logo-mark-on-light-1024.png` mark `#5A2EA6` on `#FDFBFE` = **8.59:1**;
  `logo-mark-on-dark-1024.png` mark `#C9B0F0` on `#0B0A12` = **10.27:1**. Both ≥ 3:1.
- **Raster logos (all 11 PNGs).** Every file opens with Pillow and `Image.verify()` passes;
  none is blank. Expected hexes are present: `logo-mark-on-light-1024.png` contains
  `#5A2EA6` and `#0D7D8F`; `logo-mark-on-dark-1024.png` contains `#C9B0F0` and `#8FDBE4`
  (all True). Transparent lockups carry real alpha (alpha 0–255).
- **Brand sheet.** Exactly **2400 px** wide (2400×4184), opens, non-blank (10 849 distinct
  colours). Content extent is x 139–2311, y 89–4131 — **nothing overruns the canvas**
  (all four border rows/cols are pure cosmic bg). OCR of the whole sheet is legible and
  correct (headers, sections 01–04, typography specimens, DO/DON'T lists, footer all read
  back cleanly) apart from the two defects above.
- **Honesty, font substitution.** `BRAND.md` §3/§6 and `tokens.json`
  (`typography.font.*.substitute_for`) plainly declare that DejaVu Serif/Sans/Mono are
  open-source **substitutes** for the licensed brand faces. This is honest, not overclaimed.
- **Honesty, originality.** `BRAND.md` §6 states the mark is ASTRA's own and that the guide's
  *structure* follows cited public design systems; `tokens.json` → `meta.structure_studied_from`
  lists those sources. Consistent and honest.
- **`astra-mark.svg`** is a byte-identical alias of `astra-mark-light.svg` (md5 match), as
  documented.

---

## Severity summary

| # | Severity | Region | Measured | Issue |
|---|----------|--------|----------|-------|
| 1 | **HIGH** | brand sheet, lockup panel (y 1290–1510) | 1.09:1 | light lockup (dark text) on dark `#131217` plate — primary signature invisible |
| 2 | **MEDIUM** | brand sheet, key-roles "on-surface" swatch | 1.00:1 | label ink = swatch fill `#1C1B20` — no readable label |
| 3 | **LOW** | brand sheet, footer line 2 (y ≈4109–4126) | 3.32:1 | `#7A797E` text over cyan glow, below 4.5:1 |
| 4 | **LOW** | `BRAND.md` §1 | n/a (text) | mark mis-described: claims a "crossbar" and a "curved" star; measured geometry has neither |

**Totals: 1 HIGH · 1 MEDIUM · 2 LOW.**

## Limitations of this audit

- Contrast is computed on sRGB hex values per the WCAG 2.x formula; I did not test
  non-sRGB/display-P3 variants (none are provided).
- OCR legibility is a proxy for human legibility; the two layout defects were also confirmed
  by direct pixel measurement, not OCR alone.
- The "crossbar"/"curved star" finding is a documentation-accuracy judgement; the rendered
  mark itself is internally consistent across every file.
