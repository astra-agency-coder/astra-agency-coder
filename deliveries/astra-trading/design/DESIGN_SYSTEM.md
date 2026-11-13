# Astra Trading — Design System

> **Status:** design deliverable · **Author:** Creative department (`astra-design-systems`) · **Date:** 2026-11-13
> **Token source of truth:** `../brand/tokens.json` (colour, type) + `tokens.extended.json` (spacing, radius, shadow, motion, z, opacity, border).
> **Companion files:** `INFORMATION_ARCHITECTURE.md`, `WIREFRAMES.md`, `landing-mockup.html`.
>
> **Token notation.** Colours are written as `semantic.dark.<name>` → hex. Spacing as `space-N`
> (px in brackets). Radius `radius.*`. Shadows `shadow.*`. Motion `motion.duration.*` /
> `motion.easing.*`. Every component below cites the tokens it consumes. **No component may
> invent a colour, spacing or radius outside these files.**

---

## 0. Principles

1. **Instrument, not hype.** Every element reads as a measured read-out. Gold is a *signal colour*, not decoration; it appears on the primary action, the live price and the brand mark — nowhere else at scale.
2. **Density with air.** Tight data in a generous frame: `space-4` inside controls, `space-6/8` between sections. Never cramped, never sparse.
3. **Honest states.** Loading, stale, offline, empty and error are *designed*, not afterthoughts. The product must never look alive when it is not.
4. **RTL is structural.** Logical properties everywhere; only the enumerated icons mirror.
5. **One focus language.** A single `shadow.focus-ring` (gold, 2px, offset 2px) on every interactive element.
6. **Motion is punctuation.** 120–320 ms, `standard` easing, disabled under `prefers-reduced-motion`.

### Global tokens used across the system

| Token | Value | Use |
|---|---|---|
| `semantic.dark.background` | `#07070C` | page |
| `semantic.dark.surface-1` | `#12121A` | cards |
| `semantic.dark.surface-2` | `#1B1B26` | nested rows, inputs |
| `semantic.dark.outline` | `#2A2A38` | 1px borders |
| `semantic.dark.outline-strong` | `#5A5F72` | interactive borders |
| `semantic.dark.on-background` | `#EEF0F7` | primary text |
| `semantic.dark.on-surface-muted` | `#A9AEBF` | secondary text |
| `semantic.dark.on-surface-subtle` | `#767C90` | captions |
| `semantic.dark.primary` | `#E8C766` | gold signal |
| `semantic.dark.on-primary` | `#07070C` | ink on gold |
| `semantic.dark.accent` | `#C9B0F0` | violet (parent link) |
| `semantic.dark.bull / bear / flat` | `#16C79A` / `#FF4D6D` / `#8E93A6` | chart semantics |

---

## 1. Button

**Purpose.** The single action primitive.

**Variants**
| Variant | Background | Text | Border | Use |
|---|---|---|---|---|
| `primary` | `primary` #E8C766 | `on-primary` #07070C | none | one per view: Start trial, Upgrade, Verify |
| `secondary` | `surface-2` | `on-surface` | `outline-strong` | supporting actions (Copy, Export) |
| `ghost` | transparent | `on-surface-muted` | transparent | tertiary / nav |
| `danger` | `bear-400` wash 14% | `bear-400` | `bear-600` | destructive (Cancel subscription) |
| `link` | none | `primary` | underline on hover | inline |

**Sizes** `sm` 32px (`space-2`/`space-3`, `type-sm`) · `md` 40px · `lg` 48px (hero CTA).

**States**
| State | Treatment |
|---|---|
| default | as variant |
| hover | `filter: brightness(1.06)`; ghost/secondary → `surface-2` bg |
| focus-visible | `shadow.focus-ring` |
| active | `transform: translateY(motion.distance.lift)` |
| disabled | `opacity.disabled` 0.45, `cursor: not-allowed` |
| loading | label → spinner (`icon.sm`), width locked, `aria-busy="true"` |
| error | not applicable (buttons don't error; the *result* does) |

**Tokens:** `radius.md` · `space-3`/`space-5` · `type.sm|base` · `weight.bold` · `motion.duration.fast` · `shadow.focus-ring`.
**Anatomy:** `[optional icon] label [optional trailing icon]`, `gap space-2`.
**A11y:** min target 40×40 px (`lg` 48px); icon-only buttons require `aria-label`; loading keeps label for AT via `aria-live`.
**RTL:** trailing arrow icon mirrors (`rtl.mirror_icons`); label flows RTL; padding via logical props.

---

## 2. Icon Button

**Purpose.** Compact action where the glyph is unambiguous (copy, close, expand, refresh).

**Variants:** `ghost` (default), `filled`, `outline`.
**Sizes:** 32 / 40 / 48 px square, `radius.md` (or `radius.circle` for floating).
**States:** default / hover (`surface-2` wash) / focus (`focus-ring`) / active / disabled / loading (spinner replaces glyph) / **copied** (glyph → ✓ for 1.2 s).
**Tokens:** `icon.sm|md` · `radius.md` · `opacity.hover-wash`.
**A11y:** mandatory `aria-label` + `title`; `aria-live="polite"` announces "Copied".
**RTL:** directional glyphs (arrow, chevron) mirror; non-directional (copy, close, play) do not.

---

## 3. Text Input & Number Input

**Purpose.** Single-line entry; numeric entry with `inputmode="decimal"`.

**Variants:** `text`, `number` (stepper optional), `email`, `search` (leading icon), `textarea` (multi-line, `measure.prose`).
**Sizes:** `md` 40px (default), `lg` 48px (checkout).
**States**
| State | Treatment |
|---|---|
| default | bg `surface-2` (deck) / `neutral-5` (dense calc), border `outline`, text `on-surface`, `mono` for numbers |
| hover | border `outline-strong` |
| focus | border `primary`, `shadow.focus-ring` |
| disabled | `opacity.disabled`, bg unchanged |
| loading | trailing spinner (async validate) |
| error | border `bear-400`, helper text `bear-400`, `aria-invalid="true"` |
| success | border `bull-600`, ✓ glyph |
| filled/valid | border `outline-strong` |

**Tokens:** `radius.sm` · `space-2`/`space-3` · `type.base` · `font.mono` (numeric) · `shadow.focus-ring`.
**Anatomy:** label (`type-xs`, `on-surface-subtle`) → field → helper/error row.
**A11y:** `<label for>` always; error text linked via `aria-describedby`; number inputs `inputmode="decimal"` + `step`.
**RTL:** label `text-align: start`; numeric field `dir="ltr"` with `text-align: end`; leading search icon moves to inline-start automatically.

---

## 4. Select / Dropdown

**Purpose.** Choose one option (network selector, timeframe on mobile, locale on mobile).

**Variants:** native `<select>` (mobile, a11y-safe) · custom listbox (desktop, styled).
**States:** default / hover / focus (`focus-ring`) / open (chevron rotates 180°) / disabled / error.
**Tokens:** `radius.md` · `z.dropdown` · `shadow.md` · `space-3`.
**A11y:** keyboard `↑↓ Home End Enter Esc`; `role="listbox"`/`option`; active option highlighted with `gold-wash-10`.
**RTL:** chevron sits inline-end, mirrors on open; option text `text-align: start`.

---

## 5. Checkbox, Radio & Switch

**Purpose.** Binary/choice toggles (session shading, alerts on/off, plan selection).

**Variants:** `checkbox` (accent `primary`, 16px) · `radio` (16px, circle) · `switch` (36×20, track `neutral-20` → `primary` when on).
**States:** default / hover / focus (`focus-ring`) / checked / disabled / error.
**Tokens:** `radius.sm` (checkbox), `radius.pill` (switch) · `motion.duration.fast` (knob slide).
**A11y:** label is the tap target (min 24px tall, 44px recommended); switch uses `role="switch"` + `aria-checked`.
**RTL:** switch knob travels inline-end→start when checked (logical `inset-inline-start`).

---

## 6. Segmented Control (Timeframe / Tabs)

**Purpose.** Switch between mutually exclusive views — timeframes (`5m 15m 1h 4h 1D`), deck tabs, plan cadence (monthly/annual).

**Variants:** `pill` (deck timeframe, bg `neutral-5`, container `radius.md`) · `underline` (content tabs).
**States:** default (text `on-surface-muted`) / hover (`surface-2`) / **selected** (`primary` bg, `on-primary` text, `weight.bold`, `aria-pressed="true"`) / focus / disabled.
**Tokens:** `radius.sm|md` · `space-2`/`space-3` · `motion.duration.fast` (bg fade).
**A11y:** `role="group"` + `aria-label`; each item a `<button aria-pressed>`; arrow-key roving focus.
**RTL:** item order is logical (5m first); container is direction-neutral; identifiers stay LTR.

---

## 7. Card / Panel

**Purpose.** The content container for everything.

**Variants:** `default` (surface-1 + `outline` border + `radius.lg`) · `interactive` (hover lifts border to `outline-strong`) · `accent` (1px `gold-800` border + gold wash, for the pricing highlight) · `flush` (no padding, for charts/tables).
**Anatomy:** optional `card-head` (uppercase mono title + actions, bottom border) → `card-body` (`space-4`) → optional `card-foot`.
**States:** default / hover (interactive) / focus-within (`focus-ring` inset) / loading (skeleton rows) / empty (illustrated message) / error.
**Tokens:** `surface-1` · `outline` · `radius.lg` · `shadow.sm` (raised) / `shadow.none` (flat) · `space-3|4`.
**A11y:** if interactive, it is a real `<a>`/`<button>`, not a `div` with `onclick`; heading is an `<h3>`.
**RTL:** `card-head` title at inline-start, actions at inline-end; Arabic titles drop uppercase + letter-spacing.

---

## 8. Badge / Pill

**Purpose.** Compact status/label (trial chip, plan tag, timeframe, confidence band).

**Variants:** `neutral` (outline) · `gold` (upgrade/pro) · `bull` · `bear` · `violet` (accent) · `solid` (filled).
**States:** static (no interactive states); `pulsing` variant for live.
**Tokens:** `radius.pill` · `type.xs` (`mono` for numeric) · `space-1|2` · wash colours from `color.overlay`.
**A11y:** colour is never the sole carrier — a glyph or word accompanies every semantic colour.
**RTL:** padding logical; text flows RTL; numeric pills `dir="ltr"`.

---

## 9. Direction Badge (LONG / SHORT / NO SETUP)

**Purpose.** The most important semantic in the product — the trade direction.

**Variants**
| Variant | Icon | Colour | Wash | Border |
|---|---|---|---|---|
| LONG | ▲ | `bull-400` | `bull-wash-14` | `bull-600` |
| SHORT | ▼ | `bear-400` | `bear-wash-14` | `bear-600` |
| NO SETUP | — | `flat-400` | `surface-2` | `outline` |

**States:** default only (static semantic).
**Tokens:** `radius.pill` · `type.sm` `mono` `weight.bold` · glyph + word (colour-blind safe).
**RTL:** glyph is not mirrored (▲/▼ are shape, not direction-of-reading).

---

## 10. Live Status Pill

**Purpose.** Tell the user — honestly — whether data is live, stale, or an offline snapshot.

**Variants:** `live` (bull dot, pulsing, "LIVE") · `stale` (flat dot, no pulse, "DELAYED") · `offline` (flat dot, "OFFLINE SNAPSHOT") · `connecting` (grey dot, "CONNECTING…").
**States:** the four above; `prefers-reduced-motion` disables the pulse (keeps the dot).
**Tokens:** `radius.pill` · `mono` `type.xs` · `motion.duration.*` pulse (`box-shadow` keyframe).
**A11y:** `role="status"` `aria-live="polite"`; state also in text (never dot-only).
**RTL:** dot at inline-start; text flows RTL.

---

## 11. Price Ticker / Tape

**Purpose.** The ambient "this thing is alive" element — a scrolling strip of recent prints.

**Variants:** `tape` (scrolling marquee) · `inline` (single symbol + delta).
**Anatomy:** repeating `[symbol] [price] [▲/▼]` cells, `gap space-5`, `mono`, `type-sm`.
**States:** default (animating) / paused (hover or `prefers-reduced-motion`) / stale (dims to `on-surface-subtle`).
**Tokens:** `motion.duration.tape` 32 s `linear` · `chart-bg` background · `space-4`.
**A11y:** `aria-hidden="true"` on the decorative tape (a live region elsewhere carries the real price); never the sole source of a number.
**RTL:** tape translates in the reading direction; `animation-direction: reverse` under `[dir="rtl"]`.

---

## 12. Price Header (Big Number)

**Purpose.** The hero number on the deck.

**Variants:** `hero` (clamp 30→46px) · `inline` (18px) · `compact` (chart-axis labels).
**States:** up (`bull`) / down (`bear`) / flat (`flat`) / **flashing** (brief bg flash on tick, 320 ms, disabled under reduced motion) / stale (muted).
**Tokens:** `mono` `weight.bold` `tracking.tighter` · `font-variant-numeric: tabular-nums` · `motion.duration.slow`.
**A11y:** wrapped in `dir="ltr"`; change announced via a polite live region.
**RTL:** numerals LTR as a unit; symbol tag at inline-end.

---

## 13. Candlestick Chart Frame

**Purpose.** The chart shell: plot area + overlays + axes + legend, no external lib.

**Anatomy:** `chart-holder` (bg `chart-bg`) → gridlines (`outline`, 10% opacity) → S/R bands (bull/bear wash 22% + 1px border) → liquidity lines (`violet-300`, dashed) → session shading (`violet-wash-16`) → candles (bull `#16C79A` / bear `#FF4D6D`) → current-price line (`gold-300`, 2px) → axis labels (`mono` `type-xs`).
**Variants:** `full` (deck, 460px) · `mini` (setup detail, 240px) · `spark` (card thumbnail, 48px, line only).
**States:** default / loading (shimmer over `chart-bg`) / empty ("No chart data for this timeframe") / error ("Feed unavailable — showing last snapshot") / stale (dimmed + badge).
**Tokens:** `chart-bg` `neutral-5` · `bull-400`/`bear-400`/`flat-400`/`gold-300` · `radius.lg` (frame) · `space-3|4`.
**A11y:** `<canvas role="img">` with a text `aria-label` summarising trend + zones; a data table alternative is provided for screen readers.
**RTL:** **never mirrored** — price axis stays on the right (LTR convention), time flows L→R; legend reads RTL.

---

## 14. Zone Legend

**Purpose.** Decode the chart's visual language.

**Anatomy:** inline list of `[swatch] label`; swatches: bull band, bear band, liquidity dash (`violet`), price line (`gold`), session shade.
**Variants:** `full` (deck footer) · `compact` (mini-chart, tooltip-on-tap).
**States:** static.
**Tokens:** swatch colours from chart language · `type.xs` · `gap space-3`.
**A11y:** each item is real text, not a colour-only chip.
**RTL:** swatch at inline-start; list wraps.

---

## 15. Setup Card

**Purpose.** The product's decision surface: direction, levels, confidence, reasoning — and the paywall host.

**Anatomy:** `card-head` (title + "published, never edited") → `direction-badge` → `level-ladder` → `confidence-meter` → `factors list` → `rationale` quote → `invalidation` note.
**Variants:** `live` (full) · `gated` (content `filter: blur(7px)` + `opacity 0.35` + overlay) · `closed` (result band: WIN/LOSS/BE + R) · `none` ("NO SETUP — engine stays flat").
**States:** default / gated / loading (skeleton) / closed / none.
**Tokens:** `surface-1` · `radius.lg` · `space-4` · `bull/bear/gold`.
**A11y:** when gated, the overlay is `role="dialog"` `aria-modal="true"` with focus trapped; blurred content is `aria-hidden`.
**RTL:** all rows logical; numeric column LTR; blur is direction-neutral.

---

## 16. Level Ladder

**Purpose.** Show entry/stop/targets as a vertical, ordered scale.

**Anatomy:** rows `[pip] label · value · R-multiple`; pips: entry (`gold`), stop (`bear`), TP (`bull`); a hairline between entry and targets marks the risk side.
**Variants:** `card` (in setup card) · `detail` (setup page, with R column) · `compact` (tooltip).
**States:** default / `hit` (TP row gets bull check) / `missed` (row struck through, `flat`) / loading.
**Tokens:** `surface-2` rows · `outline` 1px dividers · `mono` values · `space-3`.
**A11y:** rendered as a `<dl>` (term = label, definition = value); R-multiple has a text suffix ("R").
**RTL:** label inline-start, value inline-end; the value cell is `dir="ltr"`.

---

## 17. Confidence Meter

**Purpose.** Show the model's confidence without implying certainty.

**Anatomy:** label + percentage + 8px track (`neutral-20`) + fill (gold gradient `gold-500 → gold-300`) + band word (Low/Medium/High).
**Variants:** `bar` (default) · `dots` (5-step) · `ring` (compact).
**States:** default / loading (indeterminate shimmer) / muted (when setup is `none`).
**Tokens:** `radius.pill` · `motion.duration.slower` (width transition) · `gold-500/300`.
**A11y:** `role="progressbar"` `aria-valuenow`; the band word carries the meaning (never colour-only); copy states it is *not* a probability of profit.
**RTL:** fill grows from inline-start.

---

## 18. Stat / KPI Tile

**Purpose.** Dense read-outs (live readings rail, track-record summary).

**Anatomy:** `stat-k` (uppercase mono label, `type.xs`, `on-surface-subtle`) → `stat-v` (`mono`, 18px) → optional `stat-sub` (context).
**Variants:** `default` · `accent` (gold value) · `bull`/`bear` (signed value) · `wide` (spans 2).
**States:** default / loading (skeleton bar) / empty ("—") / stale (muted + "as of HH:MM").
**Tokens:** `surface-1` cells on an `outline` 1px grid · `space-3|4` · `mono`.
**A11y:** label+value read as one unit; use `<dl>` where grouped.
**RTL:** label/value stacked, `text-align: start`; value `dir="ltr"`.

---

## 19. Track-Record Table (Data Table)

**Purpose.** The honesty weapon — the public, auto-graded performance log.

**Anatomy:** `summary band` (wins/losses/BE/open/avg R as stat tiles) → `filter bar` → `<table>` (date · direction · entry · stop · TP · outcome · R · timeframe · link).
**Variants:** `public` (no PII) · `compact` (landing embed, 5 rows + "view all") · `detail`.
**States:** default / loading (row skeletons) / empty ("No published setups yet — the log starts when shadow mode graduates") / error (retry) / **filtered** (chip shows active filters).
**Tokens:** `surface-1`/`surface-2` zebra · `outline` hairlines · `mono` numerics · `bull/bear/flat` outcome pills · `space-3`.
**A11y:** real `<table>` with `<th scope>`; sortable headers are buttons with `aria-sort`; outcome never colour-only (has text "WIN/LOSS/BE").
**RTL:** table direction flips; numeric cells `dir="ltr"`; sort chevron mirrors; the table is horizontally scrollable on mobile with the first column sticky.

---

## 20. Tooltip

**Purpose.** Explain a term (ATR, R:R, liquidity) without leaving the page.

**Variants:** `hover` (desktop) · `tap` (mobile) · `rich` (mini chart).
**States:** hidden / visible / dismissed.
**Tokens:** `surface-2` · `radius.sm` · `shadow.md` · `z.tooltip` · `type.xs` · `motion.duration.fast` (fade+rise `motion.distance.rise`).
**A11y:** trigger has `aria-describedby`; appears on focus, not hover only; dismissible with `Esc`.
**RTL:** positioning uses `inset-inline-*`; arrow mirrors.

---

## 21. Modal / Dialog

**Purpose.** Focused tasks (upgrade, confirm, payment detail).

**Variants:** `centered` (max `layout.prose`) · `sheet` (mobile bottom sheet) · `confirm` (two buttons).
**States:** opening (fade+scale from `motion.easing.decelerate`) / open / closing / loading (busy CTA) / error.
**Tokens:** `surface-1` · `radius.lg` · `shadow.xl` · `z.modal` · scrim `overlay.scrim-72` + `blur.scrim`.
**A11y:** `role="dialog"` `aria-modal="true"`, focus trap, `Esc` closes, focus returns to trigger.
**RTL:** layout mirrors; close button stays top inline-end; scrim direction-neutral.

---

## 22. Toast / Notification

**Purpose.** Confirm a small thing happened (copied, verified, Pro activated).

**Variants:** `info` · `success` (`bull`) · `error` (`bear`) · `warning` (gold).
**States:** enter (rise+fade) / visible (auto-dismiss 4 s) / hover-pause / dismissed (swipe or ×).
**Tokens:** `surface-2` · `radius.md` · `shadow.lg` · `z.toast` · `inset-inline-end space-5`, `bottom space-5` · `motion.duration.base`.
**A11y:** `role="status"` `aria-live="polite"` (errors `assertive`); never the only feedback for a critical action.
**RTL:** anchored inline-end (left in RTL); slide direction follows.

---

## 23. Paywall / Gate Overlay

**Purpose.** Convert a trialing user at the moment of value, without hiding the product.

**Anatomy:** radial scrim over the blurred card → lock badge (gold ring) → headline → one-line value recap → `primary` CTA "Upgrade to Astra Pro" → "Crypto only · USDT (TRC20)" → wallet address block → how-to note → secondary "Restart trial (demo)".
**Variants:** `trial-expired` · `feature-locked` (alerts/journal) · `soft` (nudge, dismissible).
**States:** locked / unlocking (spinner on CTA) / unlocked (overlay unmounts, toast confirms).
**Tokens:** `overlay.scrim-94` radial · `gold-900` badge bg · `gold-700` badge border · `radius.lg` · `z.overlay`.
**A11y:** `role="dialog"` `aria-modal`, focus moves to the CTA; blurred content `aria-hidden`; the chart/readings remain reachable behind (not part of the trap).
**RTL:** centered content is direction-neutral; CTA and address flow RTL; address `dir="ltr"`.

---

## 24. Wallet / Address Block

**Purpose.** Show a receive-only crypto address safely and legibly.

**Anatomy:** label → mono address (`dir="ltr"`, `overflow-wrap: anywhere`, `font.mono` `type.xs`) → Copy icon-button → optional QR → network tag.
**Variants:** `inline` (gate overlay) · `card` (checkout) · `qr` (checkout, 160px).
**States:** default / copied (icon → ✓, "Address copied" toast) / truncated (short form with middle ellipsis on mobile).
**Tokens:** `surface-2` · `radius.sm` · `mono` · `gold-300` address tint.
**A11y:** `aria-label="USDT TRC20 address"`; copy button announces result.
**RTL:** address never reflows to RTL; wraps on character boundaries.

---

## 25. Disclaimer / Alert Banner

**Purpose.** The non-negotiable risk line, present on every screen.

**Variants:** `inline-bar` (desktop footer of deck, gold-tinted) · `sticky-mini` (mobile, pinned bottom) · `block` (landing #disclaimer, full) · `error-banner` (`bear` wash, data-feed failure).
**States:** static / dismissible (block variant only) / sticky.
**Tokens:** `gold-900` wash bg · `gold-800` border-top · `gold-200` text · `type.sm` · `z.sticky` (mini).
**A11y:** `role="note"`; contrast checked (`gold-200` on dark gold wash ≥ AA).
**RTL:** icon at inline-start; text flows RTL in Arabic.

---

## 26. Section Header / Eyebrow

**Purpose.** Establish rhythm and hierarchy on the landing page.

**Anatomy:** optional `eyebrow` (uppercase mono, `type.xs`, `gold-300`, `tracking.widest`) → `h2` (display, `display_scale.h2`) → `lead` (`type.lg`, `on-surface-muted`, `measure.prose`) → optional centered/left align.
**Variants:** `left` · `center`.
**States:** static.
**Tokens:** `display` font · `space-7|8` section rhythm · `tracking.widest`.
**RTL:** eyebrow tracking reset for Arabic; alignment `text-align: start` / `center` (center is direction-safe).

---

## 27. Skeleton / Loading

**Purpose.** Perceived performance without lying about content.

**Variants:** `text` (line), `card`, `table-row`, `chart` (shimmer over `chart-bg`), `stat`.
**States:** animating (shimmer `neutral-12 → neutral-20`) / static (reduced motion) / replaced by content.
**Tokens:** `neutral-12`/`neutral-20` · `radius.sm` · `motion.duration.slower` · `opacity`.
**A11y:** container `aria-busy="true"` + `aria-live="polite"` "Loading…".
**RTL:** shimmer direction follows reading direction.

---

## 28. Accordion (FAQ)

**Purpose.** Handle objections without a wall of text.

**Anatomy:** `[question ▾]` row → expanded answer panel.
**Variants:** `single` (one open) · `multi`.
**States:** collapsed / expanded (chevron rotates, height animates) / focus / disabled.
**Tokens:** `surface-1` · `outline` dividers · `radius.md` · `motion.duration.base`.
**A11y:** `<button aria-expanded>` + region; keyboard operable.
**RTL:** chevron at inline-end, mirrors.

---

## 29. Language Switcher

**Purpose.** Switch ar / en / tr anywhere; RTL flips instantly.

**Variants:** `segmented` (header, 3 items) · `menu` (mobile).
**States:** default / active (locale `aria-pressed="true"`, gold) / hover / focus.
**Tokens:** `radius.pill` · `outline` border · `mono` `type.xs` · `space-2|3`.
**A11y:** `role="group"` `aria-label="Language"`; labels in their own script (العربية · English · Türkçe).
**RTL:** switcher stays inline-end of the header; on RTL it moves to the left edge (logical).

---

## 30. Footer

**Purpose.** Navigation, trust, locale, status, disclosure.

**Anatomy:** brand block (mark + about) · Product links · Legal links · Language · data-source status · "Generated by an AI agent" note · risk line.
**Variants:** `full` (landing) · `compact` (app).
**States:** static; links have hover/focus.
**Tokens:** `neutral-5` bg · `outline` border-top · `space-6|7` · `type.sm|xs`.
**A11y:** `<footer>` landmark; link lists are `<ul>`; external links flagged.
**RTL:** columns reorder right→left; link text RTL.

---

## 31. Stepper (Checkout status)

**Purpose.** Show where a USDT payment is in its lifecycle.

**Anatomy:** 3 nodes `pending → confirmed → activated` with connectors.
**Variants:** `horizontal` (desktop) · `vertical` (mobile).
**States:** `done` (bull ✓) / `current` (gold ring, pulsing) / `upcoming` (`flat`).
**Tokens:** `bull`/`gold`/`flat` · `radius.circle` · `motion.duration.base`.
**A11y:** `role="list"` with `aria-current="step"`; each step has a text label.
**RTL:** connector arrows reverse; node order stays logical (pending first, at inline-start).

---

## 32. QR Code Block

**Purpose.** Scan-to-pay without transcription errors.

**Variants:** `plain` (mono-on-surface, quiet zone) · `branded` (mark in centre, gold finder squares).
**States:** default / loading / error ("QR unavailable — copy the address").
**Tokens:** `neutral-0` plate (QR needs light background for scanners) · `radius.md` · `space-3` quiet zone.
**A11y:** `role="img"` `aria-label="QR code for the USDT TRC20 address"`; the address text is always shown beside it.
**RTL:** QR image never mirrored; sits at inline-start of the payment row.

---

## 33. Breadcrumb

**Purpose.** Orientation on detail pages.

**Anatomy:** `Deck / Setup / #id` with chevron separators; last item not a link.
**States:** default / hover / focus.
**Tokens:** `type.xs` · `on-surface-subtle` · `space-2`.
**A11y:** `<nav aria-label="Breadcrumb">` + `<ol>`; `aria-current="page"` on the last item.
**RTL:** chevrons mirror; order flows RTL.

---

## 34. Avatar / Account Menu

**Purpose.** Account access, plan status, sign-out.

**Anatomy:** avatar (initials on `surface-2`, gold ring if Pro) → dropdown menu (plan · locale · billing · sign out).
**States:** closed / open / focus / disabled.
**Tokens:** `radius.circle` · `z.dropdown` · `shadow.md` · `space-2|3`.
**A11y:** `aria-haspopup="menu"` `aria-expanded`; `Esc` closes; focus trap within menu.
**RTL:** menu opens to inline-end; item icons at inline-start.

---

## Component coverage check

| # | Component | # | Component |
|---|---|---|---|
| 1 | Button | 18 | Stat / KPI tile |
| 2 | Icon button | 19 | Track-record table |
| 3 | Text / number input | 20 | Tooltip |
| 4 | Select / dropdown | 21 | Modal / dialog |
| 5 | Checkbox / radio / switch | 22 | Toast |
| 6 | Segmented control | 23 | Paywall / gate overlay |
| 7 | Card / panel | 24 | Wallet / address block |
| 8 | Badge / pill | 25 | Disclaimer / alert banner |
| 9 | Direction badge | 26 | Section header / eyebrow |
| 27 | Skeleton / loading | 10 | Live status pill |
| 28 | Accordion | 11 | Price ticker / tape |
| 29 | Language switcher | 12 | Price header |
| 30 | Footer | 13 | Candlestick chart frame |
| 31 | Stepper | 14 | Zone legend |
| 32 | QR block | 15 | Setup card |
| 33 | Breadcrumb | 16 | Level ladder |
| 34 | Avatar / account menu | 17 | Confidence meter |

**34 components specified** (requirement: ≥ 20). ✅

---

## Appendix A — Interaction state matrix (all interactive components)

| Component | default | hover | focus | active | disabled | loading | error |
|---|---|---|---|---|---|---|---|
| Button | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | n/a |
| Icon button | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | n/a |
| Input | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Select | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Checkbox/switch | ✓ | ✓ | ✓ | ✓ | ✓ | n/a | ✓ |
| Segmented | ✓ | ✓ | ✓ | ✓ | ✓ | n/a | n/a |
| Card (interactive) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Table row | ✓ | ✓ | ✓ | ✓ | n/a | ✓ | ✓ |
| Setup card | ✓ | n/a | ✓ | n/a | ✓ | ✓ | ✓ |
| Accordion | ✓ | ✓ | ✓ | ✓ | ✓ | n/a | n/a |

## Appendix B — Motion budget

| Interaction | Duration | Easing |
|---|---|---|
| hover wash / border | `fast` 120 ms | `standard` |
| button press | `fast` 120 ms | `standard` |
| tooltip / toast enter | `base` 200 ms | `decelerate` |
| modal enter | `slow` 320 ms | `decelerate` |
| price flash | `slow` 320 ms | `standard` |
| confidence fill | `slower` 520 ms | `emphasized` |
| ticker tape | 32 000 ms | `linear` |

All motion is disabled (or reduced to opacity only) under `prefers-reduced-motion: reduce`.

---

*Prepared by the AI ASTRA AGENCY Creative department (`astra-design-systems`). Generated by an AI agent — no human designer involved.*
