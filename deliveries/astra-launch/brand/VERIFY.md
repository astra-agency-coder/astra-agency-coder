# Brand deliverables — verification

Generated 2026-11-13T13:55:53Z by `brand/verify.py` (Creative / `astra-ccr`).

Every figure below was measured from the files on disk in this directory.

## PNG assets — open + integrity + size

| File | Size (px) | Mode | Opens | verify() | Distinct colours |
|---|---|---|---|---|---|
| `astra-brand-sheet.png` | 2400×4184 | RGB | yes | pass | 10849 |
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

## Wordmark — vector outline (no font dependency)

- `astra-wordmark-dark.svg`: `<path>` present = **True**, `<text>` element = **False** (outlined — renders without the font installed)
- `astra-wordmark-light.svg`: `<path>` present = **True**, `<text>` element = **False** (outlined — renders without the font installed)

## Logo raster colour verification

- `logo-mark-on-light-1024.png`: contains mark violet `#5A2EA6` = **True**, star cyan `#0D7D8F` = **True**
- `logo-mark-on-dark-1024.png`: contains mark violet `#C9B0F0` = **True**, star cyan `#8FDBE4` = **True**

## Result

**ALL CHECKS PASSED**

