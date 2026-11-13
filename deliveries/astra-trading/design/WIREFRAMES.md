# Astra Trading — Wireframes

> **Status:** design deliverable · **Author:** Creative department (`astra-design-systems`) · **Date:** 2026-11-13
> **Companion files:** `INFORMATION_ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `tokens.extended.json`, `landing-mockup.html`.
>
> Every wireframe is annotated with **RTL behaviour**. Notation:
> `[→]` mirroring icon · `⟪ ⟫` logical start/end edges · `▲`/`▼` bull/bear semantics (never colour-only).
> Widths assume a 1240 px container on desktop, 16 px gutters on mobile.
> Spacing tokens in brackets, e.g. `[space-8 = 64px]`.

---

## Legend

```
┌─┐ ┌──┐ ┌────┐   box / panel        ·····  hidden / collapsed     ▓  blurred (paywall)
│ │ │  │ │    │   borders                ●  live dot              ▼▲  bear / bull candle
└─┘ └──┘ └────┘   ── section rule       ⚑  CTA (primary)          [T] token reference
```

---

## 1. Landing — Hero

```
DESKTOP (≥1180px) — LTR                                        RTL: mirrored column order
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  [logo] Astra Trading        Live chart  Track record  Method  Pricing   [EN|AR|TR]   │  header [h 64px]
│                                                            [ Open the deck → ]        │  ghost CTA
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   ╔══════════════════════════════════════════╗   ╔══════════════════════════════════╗ │
│   ║  ● LIVE · XAU/USD · 20:05 UTC            ║   ║  ┌────────────────────────────┐  ║ │
│   ║                                          ║   ║  │ XAUUSD 1h      ● LIVE      │  ║ │
│   ║  Gold, decoded.                          ║   ║  │  3,876.93  ▲ +4.10 +0.11%  │  ║ │
│   ║                                          ║   ║  │ ──────────────────────────  │  ║ │
│   ║  AI-mapped structure, liquidity and      ║   ║  │  ╷  ╷   ╷   ╷  ╷   candlestick │  ║ │
│   ║  a rule-based scenario for gold —        ║   ║  │  │  │  ╷│  ╷│  │   SVG chart   │  ║ │
│   ║  with the reasoning, and a public        ║   ║  │ ╶┴──┴──┴┴──┴┴──┴╴ resistance  │  ║ │
│   ║  record of every call.                   ║   ║  │ ··············· liquidity ··  │  ║ │
│   ║                                          ║   ║  │ ╶┬──┬──┬┬──┬┬──┬╴ support     │  ║ │
│   ║  [ Open the deck — free 7 days  → ]      ║   ║  │                            │  ║ │
│   ║  [ See the track record ]                ║   ║  └────────────────────────────┘  ║ │
│   ║                                          ║   ║   ┌ setup chip ───────────────┐   ║ │
│   ║  no card · ar / en / tr · analysis only  ║   ║   │ ▼ SHORT  R:R 2.0  conf 78% │   ║ │
│   ╚══════════════════════════════════════════╝   ║   └───────────────────────────┘   ║ │
│      text column (6/12)  [space-6 gap]           ╚══════════════════════════════════╝ │
│                                                        product shot (6/12)             │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ▸ tape:  XAU 3876.9 ▲ · 3877.1 ▲ · 3876.4 ▼ · 3875.0 · 3878.3 ▲ · 3879.0 ▲ ····      │  ticker [motion.tape]
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**RTL behaviour (hero)**
- Text column moves to the **right**, product shot to the **left** (grid auto-flow via logical `order`).
- Headline starts at the right edge; `text-align: start`.
- Primary CTA icon `[→]` **mirrors** to `[←]`; the arrow is in `rtl.mirror_icons`.
- Live dot and price chip keep **numerals LTR** (`dir="ltr"` on the price span) — `3,876.93` never reverses.
- The candlestick chart and its price axis are **never mirrored** (`rtl.never_mirror`): time still flows left→right, matching every charting tool.
- Tape scrolls in the RTL reading direction (right→left reversed).

**Mobile (<820px)**
```
┌───────────────────────┐
│ [logo]      [☰]  [AR] │
├───────────────────────┤
│ ● LIVE · XAU/USD      │
│                       │
│ Gold, decoded.        │   ← h1 clamps 72→40px
│                       │
│ AI-mapped structure…  │
│                       │
│ [ Open the deck → ]   │   ← full-width CTA, min 48px tall
│ [ See track record ]  │
│                       │
│ no card · ar/en/tr    │
│ ┌───────────────────┐ │
│ │   product shot    │ │   ← chart stacks BELOW text
│ │   (SVG chart)     │ │
│ └───────────────────┘ │
│ ▸ tape ·············· │
└───────────────────────┘
```
RTL mobile: identical structure mirrored; CTA stays full-width so mirroring is invisible; `[☰]` hamburger moves to the **left** edge.

---

## 2. Landing — Features

```
DESKTOP — 3×2 card grid  (gap space-5 = 24px)
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                        Built for one asset, done properly                    │   ← section h2
│        Six capabilities — no toolkit, no indicator language to learn.        │   ← lead
│                                                                              │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                    │
│  │ [icon]         │ │ [icon]         │ │ [icon]         │                    │
│  │ Gold-only      │ │ Liquidity map  │ │ Session        │                    │
│  │ structure      │ │                │ │ context        │                    │
│  │ ───────────    │ │ ───────────    │ │ ───────────    │                    │
│  │ Auto-clustered │ │ Equal highs /  │ │ Asia / London  │                    │
│  │ support & res. │ │ lows, round    │ │ / NY shading,  │                    │
│  │ with a strength│ │ numbers,       │ │ so you know    │                    │
│  │ score.         │ │ session highs. │ │ when to sit out│                    │
│  └────────────────┘ └────────────────┘ └────────────────┘                    │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                    │
│  │ Rule-based     │ │ Public record  │ │ Position       │                    │
│  │ scenarios      │ │                │ │ sizing         │                    │
│  │ ───────────    │ │ ───────────    │ │ ───────────    │                    │
│  │ Entry, stop,   │ │ Auto-graded,   │ │ Turn a scenario│                    │
│  │ TP1-3, R:R and │ │ never edited.  │ │ into a safe    │                    │
│  │ the reasoning. │ │ Win or lose.   │ │ position size. │                    │
│  └────────────────┘ └────────────────┘ └────────────────┘                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

**RTL:** card order reads right→left; icon sits at the **inline-start** (right) of each card; the `───` rule under the title uses `border-inline-start`. Numerals in body copy (e.g. "TP1-3") stay LTR.

**Mobile:** single column, `gap space-4`; icons shrink `icon-lg → icon-md`.

---

## 3. Landing — Pricing

```
DESKTOP — 3 tiers, middle emphasised
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Simple, honest pricing                            │
│                  Pay in USDT. No card. Cancel by not renewing.               │
│                                                                              │
│  ┌────────────────┐   ╔════════════════╗   ┌────────────────┐                │
│  │ Free           │   ║ MOST POPULAR   ║   │ Founder        │                │
│  │                │   ║ Astra Pro      ║   │                │                │
│  │ $0             │   ║                ║   │ $349 / year    │                │
│  │ forever        │   ║ $39 / month    ║   │ (2 months off) │                │
│  │ ────────────── │   ║ ────────────── ║   │ ────────────── │                │
│  │ ✓ Live chart   │   ║ ✓ Everything   ║   │ ✓ Everything in│                │
│  │ ✓ Zones        │   ║   in Free      ║   │   Pro          │                │
│  │ ✓ Readings     │   ║ ✓ Full live    ║   │ ✓ Priority data│                │
│  │ ✗ Setups delayed│  ║   setups       ║   │   refresh      │                │
│  │ ✗ No alerts    │   ║ ✓ Alerts       ║   │ ✓ Direct line  │                │
│  │                │   ║ ✓ Sizing       ║   │   to support   │                │
│  │ [ Start free ] │   ║ [ Get Pro ] ⚑  │   │ [ Go Founder ] │                │
│  └────────────────┘   ╚════════════════╝   └────────────────┘                │
│                       ▲ gold border + glow, raised                          │
│                                                                              │
│  ⓘ Pay with USDT on TRON (TRC20) — receive-only wallet, verified on-chain.   │
└──────────────────────────────────────────────────────────────────────────────┘
```

**RTL:** tiers read right→left (Founder leftmost, Free rightmost); the "MOST POPULAR" ribbon sits at the **inline-start** (top-right) of the Pro card; check/cross icons stay at the inline-start of each list item; `$39` and `$349` stay LTR.

**Mobile:** tiers stack; **Pro is re-ordered to the top** (`order: -1`) so the recommended plan is seen first; the price row stays horizontal.

---

## 4. App — The Deck (chart + setups + track record)

```
DESKTOP (≥1180px)  — grid: minmax(0,1fr) | 400px
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ [logo] Astra Trading   ● LIVE   ·····        [◷ 5 days left]   [EN|AR|TR]   [account ▾] │ top bar
├──────────────────────────────────────────────────┬────────────────────────────────────┤
│  ┌ chart card ─────────────────────────────────┐ │ ┌ setup card (GATED) ──────────────┐ │
│  │ XAUUSD — GOLD / US DOLLAR   [☑ sessions]    │ │ │  AI-PROPOSED SETUP               │ │
│  │  3,876.93  ▼ -6.20 (-0.16%)   [5m 15m 1h 4h]│ │ │  ┌────────────────────────────┐  │ │
│  │  ────────────────────────────────────────── │ │ │  │  ▓▓▓ blurred content ▓▓▓   │  │ │
│  │  │              ╷   ╷    ╷  resistance      │ │ │  │  ▓▓▓ (setup details) ▓▓▓   │  │ │
│  │  │   ╷  ╷  ╷  │  │   │   │  zone            │ │ │  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  │ │
│  │  │  ││ ││ ││  │  │   │   │                 │ │ │  └────────────────────────────┘  │ │
│  │  │ ╶┴┴─┴┴─┴┴──┴──┴───┴───┴╴ ·· liquidity ··│ │ │        ┌──────────────┐          │ │
│  │  │ ╶┬┬─┬┬─┬┬──┬──┬───┬───┬╴ support zone   │ │ │        │  🔒 lock     │          │ │
│  │  │  ││ ││ ││  │  │   │   │  ─── price ───  │ │ │        └──────────────┘          │ │
│  │  └────────────────────────────────────────── │ │ │  Your free trial has ended      │ │
│  │  ▲ bull ▼ bear ▢ sup ▢ res ┈ liq ─ price     │ │ │  Setups, liquidity & context…   │ │
│  │  ▸ tape: 3876.9 ▲ · 3877.1 ▲ · 3876.4 ▼ ···· │ │ │  [ Upgrade to Astra Pro ] ⚑     │ │
│  └──────────────────────────────────────────────┘ │ │  Crypto only · USDT (TRC20)     │ │
│  ┌ position calculator ─────────────────────────┐ │ │  ┌ wallet ────────────────────┐ │ │
│  │ account [10000]  risk% [1.0]  contract [100] │ │ │  │ TFBEwXbB4i…JmE6   [Copy]  │ │ │
│  │ stop dist [11.20]                            │ │ │  └────────────────────────────┘ │ │
│  │ ┌ lots 0.89 ┐ ┌ risk $111 ┐ ┌ R@TP1 1.0 ┐    │ │ │  Send USDT (TRC20) then send   │ │
│  │ └───────────┘ └───────────┘ └───────────┘    │ │ │  us the tx ID to activate.      │ │
│  └──────────────────────────────────────────────┘ │ └────────────────────────────────┘ │
│                                                    │ ┌ live readings ─────────────────┐ │
│                                                    │ │ PRICE    3,876.93  ATR(14) 16.1│ │
│                                                    │ │ BID      3,876.60  BIAS ▼ bear │ │
│                                                    │ │ ASK      3,877.20  SESSION NY  │ │
│                                                    │ │ SPREAD   0.60      LIQ 12 lvls │ │
│                                                    │ │ NEAREST SUP 3,872.6 RES 3,905.4│ │
│                                                    │ └────────────────────────────────┘ │
├──────────────────────────────────────────────────┴────────────────────────────────────┤
│ ⚠ Technical analysis for education only — not investment advice.     XAUUSD · analysis │  disclaimer
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**RTL behaviour (deck)**
- Column order flips: **side rail on the LEFT**, chart on the RIGHT. Implemented with grid areas, not `direction` hacks.
- Card titles, labels, and the disclaimer use IBM Plex Sans Arabic; `text-transform: uppercase` and letter-spacing are **dropped** for Arabic (they break Arabic joins).
- Price header: the big number stays `dir="ltr"`; the ▲/▼ and change value stay LTR as a unit.
- Timeframe switcher (`5m 15m 1h 4h 1D`) stays LTR — these are identifiers, not prose.
- Zone legend swatches stay at the inline-start of each label.
- The candlestick chart is **never mirrored** (price axis LTR, time L→R).
- Wallet address is `dir="ltr"` with `overflow-wrap: anywhere` so a 34-char hash cannot overflow the RTL card.
- Blur overlay (`filter: blur`) and the lock badge are position-independent.

**Mobile (<820px)**
```
┌───────────────────────────┐
│ [logo] ● LIVE  [◷5d] [AR] │
├───────────────────────────┤
│ 3,876.93  ▼ -0.16%        │   price header
│ [5m 15m 1h 4h 1D]         │
│ ┌───────────────────────┐ │
│ │  chart (360px tall)   │ │
│ └───────────────────────┘ │
│ legend wraps              │
│ ▸ tape ·················· │
├───────────────────────────┤
│ ┌ setup card (gated) ───┐ │   setup FIRST after chart
│ │  🔒 upgrade overlay   │ │
│ └───────────────────────┘ │
├───────────────────────────┤
│ live readings (2-col)     │
├───────────────────────────┤
│ position calculator       │
├───────────────────────────┤
│ ⚠ not investment advice   │   sticky mini-disclaimer pinned
└───────────────────────────┘
```
RTL mobile: stack order identical (vertical), so no mirroring risk; only inline-start/end of labels flips.

---

## 5. Setup detail (`/app/setup/:id`)

```
DESKTOP — two columns: narrative (left, 1fr) | mini-chart (right, 420px)
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Back to deck            XAUUSD · 1h · published 2026-11-13 13:00 UTC        │ breadcrumb
├──────────────────────────────────────────────────┬───────────────────────────┤
│  ┌ scenario header ─────────────────────────────┐ │ ┌ mini-chart ───────────┐ │
│  │  ▼ SHORT   R:R 2.00   conf 78%   ● OPEN      │ │ │  ╷  ╷   ╷   ╷  ╷      │ │
│  └──────────────────────────────────────────────┘ │ │  │  │   │   │  │      │ │
│  ┌ level ladder ────────────────────────────────┐ │ │  ─ ─ ─ ─ ─ ─ ─ ─  ─ ─ │ │
│  │  ● STOP      3,914.12   risk   +8.76         │ │ │ ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈ │ │
│  │  ◆ ENTRY     3,905.36   limit                │ │ │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ │
│  │  ─────────────────────────────────────────── │ │ │  ▓ TP zones (gold) ▓ │ │
│  │  ◇ TP1       3,896.61   +1.00R               │ │ │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ │
│  │  ◇ TP2       3,887.85   +2.00R               │ │ │  ─ ─ ─ price ─ ─ ─ ─ │ │
│  │  ◇ TP3       3,879.10   +3.00R               │ │ └───────────────────────┘ │
│  └──────────────────────────────────────────────┘ │ ┌ risk calculator ──────┐ │
│  ┌ rationale ───────────────────────────────────┐ │ │ account [10000]        │ │
│  │ SHORT XAUUSD from resistance at 3,905.36;    │ │ │ risk%   [1.0]          │ │
│  │ stop 3,914.12, targets 3,896.61 / 3,887.85 / │ │ │ → lots 0.89            │ │
│  │ 3,879.10, R:R 2.00.                          │ │ │ → risk $111            │ │
│  └──────────────────────────────────────────────┘ │ └───────────────────────┘ │
│  ┌ factors ─────────────────────────────────────┐ │ ┌ lifecycle ────────────┐ │
│  │ ▸ resistance zone 3905.36–3906.07 (2 touches)│ │ │ ● proposed   13:00    │ │
│  │ ▸ EMA21 below EMA50                          │ │ │ ○ triggered  —        │ │
│  │ ▸ ATR(14) 16.10 — stop beyond 0.5×ATR        │ │ │ ○ tp / stop  —        │ │
│  │ ▸ session: new_york (US data driven)         │ │ │ ○ closed     —        │ │
│  │ ▸ liquidity: equal lows @ 3,877.10           │ │ └───────────────────────┘ │
│  └──────────────────────────────────────────────┘ │                           │
│  invalidation: close above 3,914.12               │                           │
└──────────────────────────────────────────────────┴───────────────────────────┘
```

**RTL:** narrative column to the **right**, mini-chart to the **left**. The level ladder's numeric column is `dir="ltr"` (aligned inline-end) so `3,905.36` and `+2.00R` never reorder. Bullet glyph `▸` mirrors to `◂`. The lifecycle timeline runs top→bottom (direction-neutral). Breadcrumb "← Back" mirrors to "→".

**Mobile:** single column; mini-chart first (context), then scenario header, ladder, rationale, factors, lifecycle.

---

## 6. Checkout (`/checkout`)

```
DESKTOP — centred card, max 720px, two stacked steps
┌──────────────────────────────────────────────────────────────────────────────┐
│                            [logo]      Astra Trading                          │
│                                                                              │
│  ┌ step 1 — your plan ──────────────────────────────────────────────────────┐ │
│  │  Astra Pro                                        $39 / month           │ │
│  │  ✓ Full live setups   ✓ Alerts   ✓ Position sizing   ✓ Public record     │ │
│  │  Billed monthly · pay in USDT · cancel by not renewing                   │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌ step 2 — pay with USDT ──────────────────────────────────────────────────┐ │
│  │  Network   [ USDT-TRC20 ▾ ]        (TRON · low fee)                      │ │
│  │  ┌───────────────┐    Amount   39.00 USDT                                │ │
│  │  │ ▓▓ QR ▓▓ ▓▓ ▓ │    Address  TFBEwXbB4iTyaPC2mtwu5yXSeDjEegJmE6 [Copy]│ │
│  │  │ ▓▓ ▓▓▓▓ ▓▓ ▓▓ │    ────────────────────────────────────────────────── │ │
│  │  │ ▓▓ ▓▓ ▓▓▓▓ ▓▓ │    After sending, paste the transaction hash:        │ │
│  │  └───────────────┘    [ 0x / tx hash ……………………………………… ]  [ Verify ] ⚑  │ │
│  │                                                                          │ │
│  │  ● pending → ○ confirmed → ○ activated   (manual confirm, ≤ 24h)         │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ⓘ Receive-only wallet. We hold no keys and never ask for yours. Verified     │
│    on-chain. Not investment advice.                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

**RTL:** card content mirrors; QR sits at the **inline-start** (right in RTL), the amount/address column at inline-end. The address and tx-hash inputs are **`dir="ltr"`** and `font-family: mono` with `overflow-wrap: anywhere`. The step status row (`pending → confirmed → activated`) **reverses arrow direction** in RTL (→ becomes ←) but keeps step order logical. `[Copy]` feedback toast uses `inset-inline-end`.

**Mobile:** QR on top, address wraps in 3 lines (mono, `anywhere`), inputs full-width, `[Verify]` full-width, status row stacks vertically.

---

## 7. Cross-cutting RTL checklist (applied to all six screens)

| Item | Rule | Token |
|---|---|---|
| Layout direction | CSS logical properties only | `rtl.logical_properties` |
| Mirror icons | arrows, chevrons, external-link | `rtl.mirror_icons` |
| Never mirror | logo, chart, price axis, numeric values, play | `rtl.never_mirror` |
| Numerals | `dir="ltr"` wrapper, tabular figures | `font-variant-numeric` |
| Arabic type | IBM Plex Sans Arabic, all weights | `typography.arabic` |
| Letter-spacing | reset to 0 for Arabic; no uppercase transform | `tracking` |
| Long strings | addresses / hashes `overflow-wrap: anywhere` | — |
| Focus ring | `box-shadow` ring (not `outline-offset`) so it survives RTL | `shadow.focus-ring` |
| Overflow test | 320 px viewport, longest Arabic string, no horizontal scroll | — |

---

*Prepared by the AI ASTRA AGENCY Creative department (`astra-design-systems`). Generated by an AI agent — no human designer involved.*
