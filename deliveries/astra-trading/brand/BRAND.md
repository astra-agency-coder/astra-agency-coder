# Astra Trading — Brand Guidelines v1

**Product brand of AI ASTRA AGENCY** · dark-first · trilingual (ar / en / tr)

> *Gold, decoded.*

---

## 1. The mark — "The Ingot A"

The symbol is an **A** built from three straight-edged primitives:

| Part | Meaning |
|---|---|
| The left diagonal leg | the letterform — reads as “A” even at 16 px |
| The right leg, a solid vertical bar | a **gold bullion (Au)** — the asset itself, as a measured element (not a cartoon coin) |
| The crossbar, a gauge tick that runs past the leg | the **instrument / read-out** — analysis, not hype |

**Concepts explored (and rejected):**

| | Concept | Verdict |
|---|---|---|
| A | Signal Waveform | rejected — reads as generic “audio/telecom”, weak at 16 px |
| B | Precision Caliper | rejected — too mechanical, hard to own as a single glyph |
| **C** | **The Ingot A** | **CHOSEN** — a letterform **and** a bullion **and** a gauge |

**Why C:** it is a letterform first (survives the smallest favicon without the
wordmark), an object second (the asset, rendered as a measured element), an
instrument third (the read-out). Credibility over hype. Three primitives, unioned
exactly, so the geometry is provable and scales losslessly.

## 2. Files

| File | Use |
|---|---|
| `logo-primary.svg` | default signature (mark + wordmark), dark background |
| `logo-mark.svg` | mark alone, gold on dark |
| `logo-mark-onlight.svg` | mark for light surfaces |
| `logo-mono.svg` | single-colour (inherits `currentColor`) |
| `favicon.svg` | 32×32 favicon, legible at 16 px |
| `wordmark-en.svg` | English wordmark |
| `wordmark-ar.svg` | **Arabic wordmark — designed RTL, connected letterforms** |
| `wordmark-tr.svg` | Turkish wordmark (ğ ş ı İ ö ü ç) |
| `brand-sheet.png` | full identity board (2000×3000) |
| `tokens.json` | palette + type scale, machine-readable |

## 3. Colour

**Dark-first.** Page background `neutral-3 #07070C`. Gold is the primary signal
colour; violet is inherited from the AI ASTRA AGENCY parent brand (sub-brand link).

- **Brand gold** `gold-500 #C9A227` · bright gold `gold-300 #E8C766` (primary on dark)
- **Violet accent** `violet-300 #C9B0F0` (parent-brand link)
- **Neutrals** cool, near-black first (`#07070C` → `#EEF0F7`)

**Chart language (colour-blind-considerate):**

| Role | Token | Hex |
|---|---|---|
| Bull | `bull-400` | `#16C79A` (teal-green, not pure green) |
| Bear | `bear-400` | `#FF4D6D` (rose-red, not pure red) |
| Flat | `flat-400` | `#8E93A6` |
| Gold price line | `gold-300` | `#E8C766` |

Teal-green vs rose-red stays distinguishable under deuteranopia (avoids the
red/green trap). `flat` grey covers indecision.

## 4. Typography

| Role | Family | Licence |
|---|---|---|
| Display / numerals | **Space Grotesk** | OFL-1.1 |
| Body (Latin) | **IBM Plex Sans** | OFL-1.1 |
| **Arabic (all RTL text)** | **IBM Plex Sans Arabic** | OFL-1.1 |
| Data / prices / tickers | **IBM Plex Mono** | OFL-1.1 |

Fonts are self-hosted under `fonts/` with their OFL licence files. IBM Plex Sans
Arabic has full Arabic glyph coverage; IBM Plex Sans covers Turkish
(ğ ş ı İ ö ü ç). No proprietary fonts are embedded.

## 5. Wordmarks in three scripts

- **English** — Space Grotesk, tight tracking.
- **Arabic (RTL)** — designed right-to-left with **connected letterforms**; this
  is a real Arabic wordmark, **not** a mirrored Latin hack.
- **Turkish** — Latin with correct Turkish diacritics (ğ ş ı İ ö ü ç).

The Arabic wordmark starts at the right edge of its column. RTL is a design
decision, not a CSS mirror.

## 6. Clear space & minimum sizes

- **Clear space** = 0.5 × mark height on all sides (diagram on the brand sheet).
- **Minimum sizes:** mark **16 px** · lockup **120 px** wide · print **10 mm**.
- At small sizes, prefer the **mark alone** over the full lockup.

## 7. Contrast — measured (WCAG)

Validated programmatically (`build/palette.py`). **24/24 pairs pass, 0 failures.**
Representative ratios:

| Pair | Ratio | Grade |
|---|---|---|
| body text `#EEF0F7` on `#07070C` | 17.65 | AAA |
| gold `#E8C766` on `#07070C` | 12.24 | AAA |
| gold `#C9A227` on `#12121A` | 7.70 | AAA |
| bull `#16C79A` on chart `#0C0C13` | 8.97 | AAA |
| bear `#FF4D6D` on `#07070C` | 6.25 | AA |
| caption `#767C90` on `#07070C` | 4.84 | AA |
| ink on gold button | 12.24 | AAA |
| interactive border on bg | 3.17 | AA (graphic) |

The only sub-AA pair is the **decorative divider** (1.42), which is exempt by
WCAG (non-informational). It is never used to convey meaning.

## 8. Do / Don't

**Do**
- Keep the clear space; prefer the mark at small sizes.
- Use `gold-300` as the primary signal colour on dark surfaces.
- Design Arabic RTL from the right edge; keep Turkish diacritics intact.
- Use the bull/bear/flat trio for all chart semantics.

**Don't**
- Don't place gold-on-gold or dark-on-dark.
- Don't recolour the mark outside the ramp; don't add gradients/bevels/shadows.
- Don't stretch, rotate, or outline the mark.
- Don't mirror Latin to fake Arabic.
- Don't use "get-rich" imagery — no rockets, raining money, or cartoon coins.

## 9. Sub-brand relationship

Astra Trading is a **product** brand under **AI ASTRA AGENCY**. It shares the
parent's commitment to precision and its **violet accent**, but has its own mark
and name. Where the two appear together, the parent is the endorser and Astra
Trading is the endorsed product.

## 10. Honest limitations

- The favicon and wordmarks were verified by rendering at 16 px / small sizes and
  by contrast measurement; they were **not** reviewed by a human designer.
- Turkish/Arabic rendering depends on the self-hosted fonts shipping with the app;
  if a fallback font is used, diacritics and Arabic joining may degrade.
- The brand sheet's chart panel uses **illustrative** prices, not live data.

---

*Prepared by the AI ASTRA AGENCY Creative department (astra-ccr), verified and
completed by the CEO. Generated by an AI agent — no human designer involved.*
