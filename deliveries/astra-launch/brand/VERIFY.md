# Brand deliverables — verification

Generated 2026-11-13T14:52:05Z by `brand/verify.py` (Creative / `astra-ccr`).

Every figure below was measured from the files on disk in this directory.

## Round-2 QA fixes (brand sheet) — defect → change → measured

`astra-cqo` round-2 found 4 brand defects. All are fixed and re-measured below from the regenerated `astra-brand-sheet.png`.

| ID | Defect | Change | Measured now |
|---|---|---|---|
| D-B1 | “primary signature” lockup invisible — light lockup (#1C1B20) on dark plate (#131217) = **1.089:1** | pasted the **dark** lockup (#E6E1E9 wordmark) on the dark plate | **9.72:1** (19 858 ink px; wordmark OCR-readable) |
| D-B2 | key-roles `on-surface` swatch label ink = fill (#1C1B20) = **1.00:1** | pick the legible ink for each swatch label | **17.11:1** (white on #1C1B20; OCR reads “on-surface #1C1B20”) |
| D-B3 | footer line 2 #7A797E over cyan glow #0B2E42 = **3.32:1** | raised ink to `neutral-70` #AFAFB4 | **6.57:1** over the glow |
| D-B4 | `BRAND.md` §1 described a “crossbar” and a “curved” star the path data does not contain | corrected to a single chevron with no crossbar and a straight-edged star (no curve commands) | wording now matches the raw geometry |

**Regression guard:** `make_brand_sheet.py` now registers every text and swatch element it draws, re-measures each one's local background from the rendered PNG, and **exits non-zero if any element is below 4.5:1**. The count and the minimum are asserted in `checks.json` (`sheet_elements_count`, `sheet_contrast_min`, `sheet_contrast_failures`).

## PNG assets — open + integrity + size

| File | Size (px) | Mode | Opens | verify() | Distinct colours |
|---|---|---|---|---|---|
| `astra-brand-sheet.png` | 2400×4184 | RGB | yes | pass | 10952 |
| `logo-lockup-dark-2000x300.png` | 2000×300 | RGB | yes | pass | 543 |
| `logo-lockup-dark-transparent-2000x300.png` | 2000×300 | RGBA | yes | pass | 208 |
| `logo-lockup-light-2000x300.png` | 2000×300 | RGB | yes | pass | 540 |
| `logo-lockup-light-transparent-2000x300.png` | 2000×300 | RGBA | yes | pass | 171 |
| `logo-mark-dark-1024.png` | 1024×1024 | RGBA | yes | pass | 126 |
| `logo-mark-light-1024.png` | 1024×1024 | RGBA | yes | pass | 106 |
| `logo-mark-mono-black-1024.png` | 1024×1024 | RGB | yes | pass | 202 |
| `logo-mark-mono-white-1024.png` | 1024×1024 | RGB | yes | pass | 202 |
| `logo-mark-on-dark-1024.png` | 1024×1024 | RGB | yes | pass | 284 |
| `logo-mark-on-light-1024.png` | 1024×1024 | RGB | yes | pass | 279 |

## SVG assets — XML parse + viewBox

| File | Parses | viewBox | Root |
|---|---|---|---|
| `astra-lockup-horizontal-dark.svg` | yes | `0 0 1253.2 174.0` | `svg` |
| `astra-lockup-horizontal-light.svg` | yes | `0 0 1253.2 174.0` | `svg` |
| `astra-mark-dark.svg` | yes | `0 0 512 512` | `svg` |
| `astra-mark-light.svg` | yes | `0 0 512 512` | `svg` |
| `astra-mark-mono-black.svg` | yes | `0 0 512 512` | `svg` |
| `astra-mark-mono-white.svg` | yes | `0 0 512 512` | `svg` |
| `astra-mark.svg` | yes | `0 0 512 512` | `svg` |
| `astra-wordmark-dark.svg` | yes | `-0.7 -68.3 1033.2 69.6` | `svg` |
| `astra-wordmark-light.svg` | yes | `-0.7 -68.3 1033.2 69.6` | `svg` |

## tokens.json — integrity

- Valid JSON: **yes**
- `color.ref` entries: **44**
- `color.sys` values not backed by a ref token: **0** (all backed — ref→sys aliasing holds)
- Typography scale entries: **15**
- Spacing scale steps: **11**

## WCAG contrast (declared text pairs)

| Pair | Ratio | Requirement | Result |
|---|---|---|---|
| light: primary / on-primary | 8.84:1 | ≥ 4.5:1 | PASS |
| light: on-surface / surface | 16.63:1 | ≥ 4.5:1 | PASS |
| light: secondary / on-secondary | 4.83:1 | ≥ 4.5:1 | PASS |
| light: tertiary / on-tertiary | 4.73:1 | ≥ 4.5:1 | PASS |
| dark: primary / on-primary | 8.25:1 | ≥ 4.5:1 | PASS |
| dark: on-surface / surface | 15.3:1 | ≥ 4.5:1 | PASS |
| dark: secondary / on-secondary | 10.52:1 | ≥ 4.5:1 | PASS |
| dark: tertiary / on-tertiary | 9.58:1 | ≥ 4.5:1 | PASS |
| mark: violet on light surface | 8.59:1 | ≥ 3.0:1 | PASS |
| mark: light-violet on dark surface | 10.27:1 | ≥ 3.0:1 | PASS |

## Brand sheet — per-element contrast (measured from the shipped PNG)

Every text and swatch element on `astra-brand-sheet.png` is registered in `checks.json` → `sheet_elements` with its ink colour(s) and bounding box. This section **re-measures** each element's local background from the rendered PNG (modal colour of the padding ring for plate text, modal colour of the box interior for panels/swatches) and recomputes the WCAG ratio. Requirement: **every element ≥ 4.5:1**.

| Element | Kind | Ink | Measured bg | Ratio | Req | Result |
|---|---|---|---|---|---|---|
| header · lockup | logo | #E6E1E9/#C9B0F0/#8FDBE4 | `#%02X%02X%02X` | 8.55:1 | ≥3:1 | PASS |
| header · eyebrow | text | #C9B0F0 | `#%02X%02X%02X` | 9.00:1 | ≥4.5:1 | PASS |
| header · strapline | text | #E6E1E9 | `#%02X%02X%02X` | 12.73:1 | ≥4.5:1 | PASS |
| header · subline | text | #AFAFB4 | `#%02X%02X%02X` | 7.51:1 | ≥4.5:1 | PASS |
| section · 01  LOGO SYSTEM | text | #8FDBE4 | `#%02X%02X%02X` | 10.76:1 | ≥4.5:1 | PASS |
| logo tile 1 · mark | logo | #5A2EA6/#0D7D8F | `#%02X%02X%02X` | 4.69:1 | ≥3:1 | PASS |
| logo tile 1 · caption | text | #5F5E63 | `#%02X%02X%02X` | 6.24:1 | ≥4.5:1 | PASS |
| logo tile 2 · mark | logo | #C9B0F0/#8FDBE4 | `#%02X%02X%02X` | 10.27:1 | ≥3:1 | PASS |
| logo tile 2 · caption | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| logo tile 3 · mark | logo | #000000 | `#%02X%02X%02X` | 21.00:1 | ≥3:1 | PASS |
| logo tile 3 · caption | text | #5F5E63 | `#%02X%02X%02X` | 6.43:1 | ≥4.5:1 | PASS |
| logo tile 4 · mark | logo | #FFFFFF | `#%02X%02X%02X` | 21.00:1 | ≥3:1 | PASS |
| logo tile 4 · caption | text | #AFAFB4 | `#%02X%02X%02X` | 9.61:1 | ≥4.5:1 | PASS |
| 01 · primary-signature lockup | logo | #E6E1E9/#C9B0F0/#8FDBE4 | `#%02X%02X%02X` | 9.72:1 | ≥3:1 | PASS |
| 01 · lockup label | text | #CBC9CF | `#%02X%02X%02X` | 11.36:1 | ≥4.5:1 | PASS |
| section · 02  COLOUR SYSTEM | text | #8FDBE4 | `#%02X%02X%02X` | 12.59:1 | ≥4.5:1 | PASS |
| 02 · ramp Primary · violet | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| 02 · violet-10 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-20 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-30 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-40 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-50 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-60 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-70 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-80 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-90 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-95 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · violet-99 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · ramp Secondary · cyan | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| 02 · cyan-10 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · cyan-20 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · cyan-40 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · cyan-60 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · cyan-80 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · cyan-90 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · ramp Tertiary · gold | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| 02 · gold-10 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · gold-20 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · gold-40 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · gold-60 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · gold-80 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · gold-90 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · ramp Neutral | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| 02 · neutral-6 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-10 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-20 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-30 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-50 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-70 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-90 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-95 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · neutral-99 step label | text | #949499 | `#%02X%02X%02X` | 6.52:1 | ≥4.5:1 | PASS |
| 02 · key-roles heading | text | #AFAFB4 | `#%02X%02X%02X` | 9.02:1 | ≥4.5:1 | PASS |
| 02 · role primary label | text | #FFFFFF | `#%02X%02X%02X` | 8.84:1 | ≥4.5:1 | PASS |
| 02 · role secondary label | text | #FFFFFF | `#%02X%02X%02X` | 4.83:1 | ≥4.5:1 | PASS |
| 02 · role tertiary label | text | #FFFFFF | `#%02X%02X%02X` | 4.73:1 | ≥4.5:1 | PASS |
| 02 · role surface label | text | #0B0A12 | `#%02X%02X%02X` | 19.14:1 | ≥4.5:1 | PASS |
| 02 · role on-surface label | text | #FFFFFF | `#%02X%02X%02X` | 17.11:1 | ≥4.5:1 | PASS |
| 02 · role inverse-surface label | text | #FFFFFF | `#%02X%02X%02X` | 13.07:1 | ≥4.5:1 | PASS |
| section · 03  TYPOGRAPHY | text | #8FDBE4 | `#%02X%02X%02X` | 12.59:1 | ≥4.5:1 | PASS |
| 03 · brand-face note | text | #AFAFB4 | `#%02X%02X%02X` | 8.24:1 | ≥4.5:1 | PASS |
| 03 · display specimen | text | #F1EEF5 | `#%02X%02X%02X` | 14.45:1 | ≥4.5:1 | PASS |
| 03 · ui-face note | text | #AFAFB4 | `#%02X%02X%02X` | 7.12:1 | ≥4.5:1 | PASS |
| 03 · body specimen | text | #F1EEF5 | `#%02X%02X%02X` | 13.09:1 | ≥4.5:1 | PASS |
| 03 · scale display-large | text | #F1EEF5 | `#%02X%02X%02X` | 12.66:1 | ≥4.5:1 | PASS |
| 03 · scale display-large detail | text | #949499 | `#%02X%02X%02X` | 4.98:1 | ≥4.5:1 | PASS |
| 03 · scale headline-large | text | #F1EEF5 | `#%02X%02X%02X` | 12.49:1 | ≥4.5:1 | PASS |
| 03 · scale headline-large detail | text | #949499 | `#%02X%02X%02X` | 4.92:1 | ≥4.5:1 | PASS |
| 03 · scale title-large | text | #F1EEF5 | `#%02X%02X%02X` | 12.49:1 | ≥4.5:1 | PASS |
| 03 · scale title-large detail | text | #949499 | `#%02X%02X%02X` | 4.86:1 | ≥4.5:1 | PASS |
| 03 · scale body-large | text | #F1EEF5 | `#%02X%02X%02X` | 12.49:1 | ≥4.5:1 | PASS |
| 03 · scale body-large detail | text | #949499 | `#%02X%02X%02X` | 4.81:1 | ≥4.5:1 | PASS |
| 03 · scale label-large | text | #F1EEF5 | `#%02X%02X%02X` | 12.49:1 | ≥4.5:1 | PASS |
| 03 · scale label-large detail | text | #949499 | `#%02X%02X%02X` | 4.75:1 | ≥4.5:1 | PASS |
| section · 04  USAGE RULES | text | #8FDBE4 | `#%02X%02X%02X` | 9.17:1 | ≥4.5:1 | PASS |
| 04 · clear-space mark | logo | #C9B0F0/#8FDBE4 | `#%02X%02X%02X` | 9.72:1 | ≥3:1 | PASS |
| 04 · clear-space caption | text | #CBC9CF | `#%02X%02X%02X` | 11.36:1 | ≥4.5:1 | PASS |
| 04 · DO heading | text | #A6E7B5 | `#%02X%02X%02X` | 10.05:1 | ≥4.5:1 | PASS |
| 04 · DO item 1 | text | #E6E1E9 | `#%02X%02X%02X` | 11.14:1 | ≥4.5:1 | PASS |
| 04 · DO item 2 | text | #E6E1E9 | `#%02X%02X%02X` | 11.14:1 | ≥4.5:1 | PASS |
| 04 · DO item 3 | text | #E6E1E9 | `#%02X%02X%02X` | 11.14:1 | ≥4.5:1 | PASS |
| 04 · DO item 4 | text | #E6E1E9 | `#%02X%02X%02X` | 11.14:1 | ≥4.5:1 | PASS |
| 04 · DON'T heading | text | #F2B8B5 | `#%02X%02X%02X` | 9.11:1 | ≥4.5:1 | PASS |
| 04 · DON'T item 1 | text | #E6E1E9 | `#%02X%02X%02X` | 12.08:1 | ≥4.5:1 | PASS |
| 04 · DON'T item 2 | text | #E6E1E9 | `#%02X%02X%02X` | 11.81:1 | ≥4.5:1 | PASS |
| 04 · DON'T item 3 | text | #E6E1E9 | `#%02X%02X%02X` | 11.81:1 | ≥4.5:1 | PASS |
| 04 · DON'T item 4 | text | #E6E1E9 | `#%02X%02X%02X` | 11.68:1 | ≥4.5:1 | PASS |
| footer · line 1 | text | #949499 | `#%02X%02X%02X` | 4.75:1 | ≥4.5:1 | PASS |
| footer · line 2 | text | #AFAFB4 | `#%02X%02X%02X` | 6.57:1 | ≥4.5:1 | PASS |

- Elements checked: **89**; failures: **0**
- Minimum ratio across all sheet elements: **4.69:1** (`logo tile 1 · mark`) — threshold 4.5:1

## Wordmark — vector outline (no font dependency)

- `astra-wordmark-dark.svg`: `<path>` present = **True**, `<text>` element = **False** (outlined — renders without the font installed)
- `astra-wordmark-light.svg`: `<path>` present = **True**, `<text>` element = **False** (outlined — renders without the font installed)

## Logo raster colour verification

- `logo-mark-on-light-1024.png`: contains mark violet `#5A2EA6` = **True**, star cyan `#0D7D8F` = **True**
- `logo-mark-on-dark-1024.png`: contains mark violet `#C9B0F0` = **True**, star cyan `#8FDBE4` = **True**

## Result

**ALL CHECKS PASSED**

