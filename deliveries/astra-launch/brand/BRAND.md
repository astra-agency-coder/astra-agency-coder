# AI ASTRA AGENCY — Brand Guide

**Version** 2.0.0 · **Owner** `astra-ccr` (Creative) · **Date** 2026-11-13
**Companion files** `tokens.json` (machine tokens) · `astra-brand-sheet.png`
(rendered one-page sheet) · `checks.json` (objective checks) · `VERIFY.md`
(verification evidence).

> **AI ASTRA AGENCY** is an autonomous, AI-agent-run digital agency.
> Tone: **modern · technical · trustworthy · cosmic** (Astra = star).

---

## 1. The mark

The mark is a single geometric **chevron that reads as the letter “A”**, with a
four-point **star** (a cosmic accent) set in the A's counter.

- Construction: two nested chevron strokes with a crossbar; the star is the only
  curved element, deliberately contrasting the straight letterform.
- Maximum **two colours** in the primary mark: `primary` (the A) and `secondary`
  (the star). Mono variants use a single colour.

| File | Use | Format |
|---|---|---|
| `astra-mark-light.svg` | Mark for **light** backgrounds (violet A, cyan star) | SVG, `0 0 512 512` |
| `astra-mark-dark.svg` | Mark for **dark** backgrounds (light-violet A, light-cyan star) | SVG |
| `astra-mark-mono-black.svg` | Single-colour, black (stamps, fax, engraving) | SVG |
| `astra-mark-mono-white.svg` | Single-colour, white (on photography / dark fills) | SVG |
| `astra-mark.svg` | Alias of the light mark | SVG |

### Lockups

| File | What | Use |
|---|---|---|
| `astra-lockup-horizontal-light.svg` | Mark + “AI ASTRA AGENCY” wordmark, dark text | **Primary signature**, light bg |
| `astra-lockup-horizontal-dark.svg` | Same, light text | Primary signature, dark bg |
| `astra-wordmark-light.svg` / `astra-wordmark-dark.svg` | Wordmark only | When the mark already appears nearby |

The wordmark is drawn as **vector outlines** (converted from the brand face with
`fontTools`), so the lockups carry **no font dependency** and render identically
everywhere. Raster renders of every logo are provided at 1024–2000 px.

---

## 2. Colour system

Two tiers, the same shape as published design-token systems: a **reference ramp**
(`color.ref`, named steps) feeds **system roles** (`color.sys`, semantic names).
Every system value resolves to a reference token — see `tokens.json` →
`color.sys_resolved`. Full values in `tokens.json`; the sheet renders them.

**Core roles (light / dark):**

| Role | Light | Dark | Meaning |
|---|---|---|---|
| `primary` | `#5A2EA6` | `#C9B0F0` | Brand violet — the A, primary actions |
| `secondary` | `#0D7D8F` | `#8FDBE4` | Star cyan — accent, links, focus |
| `tertiary` | `#9A6A00` | `#F5D488` | Gold — highlights, badges |
| `surface` | `#FDFBFE` | `#0B0A12` | Page background |
| `on-surface` | `#1C1B20` | `#E6E1E9` | Body text |
| `inverse-surface` | `#313036` | `#E6E1E9` | Inverted panels |

Contrast is guaranteed: the minimum ratio across all declared text pairs is
**4.73:1** (WCAG AA) — see `checks.json`. The mark itself is 8.59:1 on the light
surface and 10.27:1 on the dark surface.

---

## 3. Typography

| Role | Family | Notes |
|---|---|---|
| **Brand** | **DejaVu Serif** (Bold for display) | Headlines, lockups. **Substitute** for the licensed brand serif in this environment. |
| **UI / body** | **DejaVu Sans** | Interface, body copy, captions |
| **Mono** | **DejaVu Sans Mono** | Code, data |

The type scale is role-named (`display/headline/title/body/label` × s/m/l), each
entry carrying size, line-height, tracking and weight — see `tokens.json` →
`typography.scale`. Example: `display-large` = 57/64, weight 700, tracking −0.5.

> **Licensing note.** No licensed commercial font is available in this
> environment. DejaVu families are open-source substitutes; swap the
> `typography.font` families in `tokens.json` when the brand faces are licensed.

---

## 4. Usage rules

### Clear space
Keep empty space of **0.5 × the mark height (h)** on every side. Nothing — type,
image edge, or another logo — enters that zone.

### Minimum size

| Medium | Minimum mark height |
|---|---|
| Digital / screen | **24 px** |
| Favicon / avatar | **16 px** |
| Print | **12 mm** |

Below these, use the mark alone without the wordmark.

### Approved colourways

| Background | Mark |
|---|---|
| `surface` `#FDFBFE` | `astra-mark-light.svg` (violet A, cyan star) |
| `primary` `#5A2EA6` | mono **white** |
| `inverse-surface` `#313036` | `astra-mark-dark.svg`, or mono white |
| Photography / gradient | mono white over a solid scrim |

### DO
- Scale the mark **uniformly** only.
- Use the approved colourways above.
- Keep the 0.5h clear space.
- Use the horizontal lockup as the default signature.

### DON'T
- **Re-colour** the mark or add gradients outside the palette.
- **Stretch, squash, skew or rotate** it.
- Add outlines, drop shadows or bevels.
- Place it on busy imagery without a solid scrim.
- Crowd it below the clear space or minimum size.

*(The rendered sheet `astra-brand-sheet.png` shows the clear-space diagram and
the DO / DON'T list visually.)*

---

## 5. File inventory

```
tokens.json                     machine-readable tokens (colour, type, spacing, radius, breakpoints)
astra-brand-sheet.png           rendered brand sheet — logo, colour, type, rules (2400 x 4184)
BRAND.md                        this guide
astra-mark-light.svg            mark, light backgrounds
astra-mark-dark.svg             mark, dark backgrounds
astra-mark-mono-black.svg       single-colour mark, black
astra-mark-mono-white.svg       single-colour mark, white
astra-mark.svg                  light mark alias
astra-lockup-horizontal-light.svg   horizontal signature, light
astra-lockup-horizontal-dark.svg    horizontal signature, dark
astra-wordmark-light.svg        wordmark only, light
astra-wordmark-dark.svg         wordmark only, dark
logo-mark-light-1024.png        raster mark (light) 1024x1024
logo-mark-dark-1024.png         raster mark (dark)  1024x1024
logo-mark-on-light-1024.png     raster mark on surface 1024x1024
logo-mark-on-dark-1024.png      raster mark on dark surface 1024x1024
logo-mark-mono-black-1024.png   raster mono black 1024x1024
logo-mark-mono-white-1024.png   raster mono white 1024x1024
logo-lockup-light-2000x300.png  raster horizontal lockup (light bg)
logo-lockup-dark-2000x300.png   raster horizontal lockup (dark bg)
logo-lockup-*-transparent-*.png transparent-background lockups
build_brand.py                  regenerates the SVG + PNG logo suite and tokens.json
make_brand_sheet.py             regenerates the brand sheet + checks.json
checks.json                     objective check output (sizes, SVG parse, contrast)
```

Regenerate everything:

```bash
python3 build_brand.py        # -> SVG + PNG logo suite + tokens.json
python3 make_brand_sheet.py   # -> astra-brand-sheet.png + checks.json
```

---

## 6. Known limitations (stated plainly)

- **Fonts are substitutes.** DejaVu Serif/Sans are used in place of licensed
  brand faces; they are visually close in role but not the final brand type.
- The mark is ASTRA's own geometry — **no third-party logo was copied**. The
  *structure* of this guide (clear-space, minimum size, approved placements,
  misuse list, two-tier tokens) follows publicly published design-system
  conventions, cited in `tokens.json` → `meta.structure_studied_from`.
