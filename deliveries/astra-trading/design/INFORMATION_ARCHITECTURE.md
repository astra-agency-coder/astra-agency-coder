# Astra Trading — Information Architecture

> **Status:** design deliverable · **Author:** Creative department (`astra-design-systems`) · **Date:** 2026-11-13
> **Sources of truth:** `docs/SCOPE.md`, `brand/BRAND.md`, `brand/tokens.json`, `PLAN-V2.md`, `db/001_core_schema.sql`, `engine/analysis.py`, `web/js/i18n.js`.
> **Companion files:** `WIREFRAMES.md`, `DESIGN_SYSTEM.md`, `tokens.extended.json`, `landing-mockup.html`.
>
> **Honesty contract.** Every page below maps to a real capability in the
> existing engine/schema, or is explicitly marked **[roadmap]** (v2/v3 per
> `PLAN-V2.md` §3). Nothing here promises returns; the product is *analysis*, not
> advice, and the copy rules in `PLAN-V2.md` §2.4 are binding on every screen.

---

## 0. The one-line model

**Astra Trading is two products under one brand:**

| Surface | Job | Audience | Success signal |
|---|---|---|---|
| **Marketing site** (`/`) | *Convince a stranger it is honest and useful.* | Cold visitors from search / social / word-of-mouth in ar·en·tr. | Visitor opens the live deck within 60 s. |
| **The Deck** (`/app`) | *Give a paying trader the gold read in under 10 seconds.* | Signed-in users (trialing or Pro). | Setup understood → executed or dismissed, repeat visits. |
| **Public track record** (`/track-record`) | *Prove the deck is not lying.* | Skeptics, buyers on the fence, press. | "Is this a scam?" answered with data. |

Everything else (checkout, auth, legal) is plumbing in service of those three.

---

## 1. Site map

```
Astra Trading
│
├── / ............................ Marketing landing (public, no auth)
│   ├── #hero                     Promise + live ticker + product shot
│   ├── #live-proof               "The deck, live" — embedded real chart snippet
│   ├── #how-it-works             4-step method (structure → liquidity → scenario → record)
│   ├── #features                 Capability grid (6 cards)
│   ├── #track-record             Public, auto-graded record (real numbers from DB)
│   ├── #pricing                  3 tiers + USDT checkout entry
│   ├── #faq                      Objection handling ("is this a signal group?")
│   ├── #disclaimer               Risk + "analysis, not advice"
│   └── footer                    Product / Legal / Language / Status
│
├── /track-record ................ Public performance log (no auth, no PII)
│   ├── summary band              wins / losses / BE / open / avg R (from `track_record` view)
│   ├── filters                   timeframe · direction · session · date range
│   ├── setups table              every published setup, outcome, R, link to detail
│   └── methodology link          → /method
│
├── /method ...................... How the analysis is computed (no auth)
│   ├── engine explainer          zones, liquidity, bias, ATR, session — plain language
│   ├── rules table               each level's reproducible rule + version
│   └── limitations               honest "what this cannot do" panel
│
├── /pricing ..................... Standalone pricing (deep-linkable)
│   └── (same three tiers as landing #pricing)
│
├── /auth ........................ Sign in / Sign up
│   ├── sign-in                   email+password or magic link
│   ├── sign-up                   email → profile → 7-day trial auto-created
│   └── locale                    ar / en / tr captured at signup (default ar)
│
├── /app ......................... THE DECK (auth required)
│   ├── top bar                   brand · live status · trial chip · language · account
│   ├── chart column
│   │   ├── XAUUSD chart          candles + S/R zones + liquidity + session shading
│   │   ├── price header          live price, change, bid/ask/spread
│   │   ├── timeframe switcher    5m / 15m / 1h / 4h / 1D
│   │   ├── zone legend           colour key (bull/bear/flat/gold/liquidity)
│   │   └── tape ticker           scrolling recent prints
│   ├── side column
│   │   ├── setup card            direction · entry · stop · TP1-3 · R:R · confidence · factors · invalidation  [GATED]
│   │   ├── position calculator   account · risk% · contract · stop → lot size
│   │   └── live readings rail    price · bid · ask · spread · ATR · bias · session · nearest S/R · liquidity count
│   └── disclaimer bar            persistent on every screen
│
├── /app/setup/:id ............... Setup detail (auth required)
│   ├── scenario header           direction, R:R, status, published timestamp
│   ├── level ladder              entry / stop / TP1-3 visualised on a mini-chart
│   ├── rationale                 written reasoning (locale-aware, from DB rationale_{ar,en,tr})
│   ├── factors                   bullet list of contributing rules
│   ├── lifecycle timeline        proposed → triggered → tp/stop → closed (from `setup_events`)
│   ├── risk calculator           pre-filled from this setup
│   └── share / export            TradingView levels copy, share link  [roadmap v2]
│
├── /app/alerts .................. Alerts config  [roadmap v2]
├── /app/journal ................. Trade journal + stats  [roadmap v2]
│
├── /checkout .................... USDT subscription checkout (auth required)
│   ├── plan summary              Astra Pro · $39/mo · what unlocks
│   ├── network selector          USDT-TRC20 (primary) · BEP20 · Solana  [multi-net roadmap]
│   ├── wallet + QR               receive-only address, copy button
│   ├── tx-hash verifier          paste hash → on-chain verify (`/api/v1/payments/verify`)
│   ├── status states             pending → confirmed → activated (manual confirm note)
│   └── trust row                 receive-only, no keys, on-chain only
│
├── /legal/terms ................. Terms of use
├── /legal/privacy ............... Privacy policy
├── /legal/risk .................. Risk disclosure
└── /status ...................... Live system status (data feed, engine, payments)
```

---

## 2. Marketing landing — section by section

> Order is deliberate: **promise → proof → mechanism → capability → honesty → price → objection → exit.**
> The record comes *before* the price, because in this market trust is the blocker, not price.

| # | Section | Purpose | Content | Primary action |
|---|---|---|---|---|
| 1 | **Hero** | Stop the scroll; state the wedge in one line. | Headline *"Gold, decoded."*; sub: gold-only structure + liquidity + a scenario with the reasoning; **live price ticker** (real XAUUSD); primary CTA **Open the live deck — free 7 days**; secondary **See the track record**; small print *no card required · ar/en/tr*. | `→ /auth` (start trial) |
| 2 | **Live proof** | Show, don't tell. | Embedded real candlestick chart (SVG) with a support zone, a resistance zone and a liquidity line drawn by the engine; a floating "setup" chip with entry/stop/TP. | `→ /app` (view full deck) |
| 3 | **How it works** | Make the method legible in 4 steps. | ① Map structure (S/R) ② Find liquidity ③ Publish a scenario (entry/stop/TPs/R:R) ④ Score it publicly. Each step = icon + one honest sentence. | `→ /method` |
| 4 | **Features** | Justify a paid tier. | 6 cards: Gold-only structure · Liquidity map · Session context · Rule-based scenarios · Public record · Position sizing. | `→ /app` |
| 5 | **Track record** | The trust weapon. | Real numbers pulled from `track_record`: wins / losses / BE / open / avg R, with a "how this is scored" link and an explicit *not a profit promise* note. | `→ /track-record` |
| 6 | **Pricing** | Convert. | Free (delayed setups) · **Pro $39/mo** (full live setups, alerts, sizing) · Founder annual (packaging experiment). USDT badge. | `→ /checkout` |
| 7 | **FAQ** | Kill objections. | "Is this a signal group?" (no), "Do you execute trades?" (no), "What's the track record?" (public), "How do I pay?" (USDT on-chain), "Which markets?" (XAU/USD at launch). | expand inline |
| 8 | **Disclaimer** | Legal + ethical floor. | Technical analysis for education; not investment advice; past performance ≠ future results. | — |
| 9 | **Footer** | Navigation + trust + status. | Product · Legal · Language · data-source status · "Generated by an AI agent" disclosure. | `→ /legal/*`, `→ /status` |

**Landing copy rules (binding):** no "signals", no "guaranteed", no profit figures, no fake testimonials, no "AI that trades for you". If we have no users yet, we show the record and the method — never invented social proof.

---

## 3. The Deck — panel by panel

| Panel | Purpose | Content (real fields) | Primary action |
|---|---|---|---|
| **Top bar** | Orientation + status + account. | Logo, "LIVE / OFFLINE SNAPSHOT" pill, trial chip (days left), language switch, account menu. | open account / upgrade |
| **Chart** | The read at a glance. | Canvas candles from `market.fetch_ohlc`; S/R bands from `cluster_zones`; liquidity lines from `find_liquidity`; session shading from `session_context`. | switch timeframe |
| **Price header** | Instant number. | `price`, Δ vs prior bar, bid/ask/spread from `fetch_tick`. | — |
| **Setup card** | The decision. | `direction`, `entry`, `stop_loss`, `tp1/2/3`, `risk_reward`, `confidence`, `factors[]`, `invalidation`, `rationale`. **Gated** after trial. | Upgrade (when gated) |
| **Position calculator** | Make it executable safely. | inputs: account, risk %, contract size, stop distance → output: lots, risk $, R at TP1. | copy lot size |
| **Live readings rail** | Density that feels like a terminal. | price, bid, ask, spread, ATR(14), bias (EMA21/50), active session, nearest support, nearest resistance, liquidity count. | — |
| **Disclaimer bar** | Non-negotiable. | "Technical analysis for education only — not investment advice." + symbol tag. | — |

**Gating model (from schema):** new profile → `subscriptions.status = 'trialing'`, `trial_ends_at = now()+7d`. On expiry the setup card is **blurred + overlaid** with an upgrade prompt + wallet address; the chart, zones and readings stay visible (value is *shown* before it is *sold*). Pro unlock = `status = 'active'`.

---

## 4. The user journey (end-to-end)

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │  1. DISCOVER │──▶│   2. TRIAL    │──▶│ 3. SEE LIVE  │──▶│ 4. SUBSCRIBE │
 │  landing page│   │  sign up, 7d  │   │  SETUPS      │   │  pick plan   │
 └──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
                                                                  │
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
 │  8. RENEW /  │◀──│ 7. ACTIVATED │◀──│  6. PAY      │◀─────────┘
 │  RETAIN      │   │  Pro unlocked│   │  USDT on-chain│
 └──────────────┘   └──────────────┘   └──────────────┘
        ▲                                                    ▲
        └──────────────── 5. VERIFY (tx hash) ────────────────┘
```

### Step-by-step

| Step | Trigger | Screen | What the user does | What the system does | Success metric |
|---|---|---|---|---|---|
| **1. Discover** | Search / social / share link. | `/` | Reads hero + live chart; scans record. | Serves locale (default `ar`), renders live ticker. | Bounce < 55%; scroll to #pricing. |
| **2. Trial** | Clicks "Open the live deck". | `/auth` → sign-up. | Enters email, confirms locale. | Creates `profile` (locale captured) → trigger creates `subscription` (`trialing`, +7d). | Signup completion ≥ 60% of auth starts. |
| **3. See live setups** | Lands in deck. | `/app` | Reads the setup card, zones, readings. | Calls `analyse()`; publishes live setup; starts trial countdown. | ≥ 2 sessions in trial. |
| **4. Subscribe** | Trial nears end **or** user wants full setups early. | `/checkout` | Picks Pro (monthly/annual). | Locks price; shows wallet + QR. | Trial→paid ≥ 8% (target, estimate). |
| **5. Verify** | User sends USDT. | `/checkout` (verify panel) | Pastes tx hash. | `verify_trc20()` checks on-chain (TRC20). Records `payments` row `pending`. | Verify attempt within 24 h ≥ 50% of checkouts. |
| **6. Pay** | Funds land at receive-only wallet. | — | Waits. | On-chain confirmation observed; `payments.status='confirmed'` after manual confirm. | — |
| **7. Activated** | Confirm received. | `/app` | Sees setup card unlocked, trial chip → "Pro". | `subscriptions.status='active'`, `period_ends_at=+30d`. Toast: "Pro active." | Activation ≤ 24 h from payment. |
| **8. Renew / retain** | 7 days before `period_ends_at`. | email + `/checkout` | Renews; keeps using alerts/journal. | Reminder (trilingual email) [roadmap v2]. | Renewal ≥ 60% (target, estimate). |

**Honest friction note:** crypto-only payment *will* cost conversion (`PLAN-V2.md` §0.4). The checkout is therefore designed to be maximally reassuring (receive-only, on-chain proof, no keys) and to keep the user *inside* the deck during the wait — the value must stay visible while they pay.

---

## 5. Locale & RTL behaviour (applies to every page)

| Aspect | ar (primary) | en | tr |
|---|---|---|---|
| Direction | **RTL** (`dir="rtl"`) | LTR | LTR |
| Body font | IBM Plex Sans Arabic (all weights) | IBM Plex Sans | IBM Plex Sans |
| Display font | IBM Plex Sans Arabic | Space Grotesk | Space Grotesk |
| Numerals | Western/Latin (market convention), `dir="ltr"` inside RTL | Latin | Latin |
| Default | ✅ (profile default `locale='ar'`) | ✓ | ✓ |
| Layout | CSS logical properties; icons mirrored selectively (`rtl.never_mirror` protects the chart, logo, numbers) | — | — |

**Rule:** RTL is structural (`margin-inline`, `padding-inline`, `inset-inline`, `border-inline-start`), never a `transform: scaleX(-1)` on the whole page. The chart's price axis and all numeric values stay LTR.

---

## 6. Content model (what a page is made of)

| Entity | Source | Rendered on |
|---|---|---|
| `profiles` | Supabase | account menu, locale |
| `subscriptions` | Supabase | trial chip, paywall, checkout |
| `setups` | Supabase (published=true) | deck, `/track-record`, `/app/setup/:id` |
| `setup_events` | Supabase | setup detail timeline |
| `payments` | Supabase | checkout status |
| `track_record` (view) | computed | landing #track-record, `/track-record` |
| `analyse()` payload | FastAPI | deck chart + setup + readings |
| i18n strings | `web/js/i18n.js` | all UI chrome |

---

## 7. Navigation model

- **Public header:** logo · Live chart · Track record · Method · Pricing · **Open the deck** (CTA) · language switch.
- **App header:** logo · live status · timeframe · trial chip · language · account.
- **Footer:** Product · Legal · Language · data-source status · AI disclosure.
- **Breadcrumbs:** only on detail pages (`/app/setup/:id`, `/legal/*`).
- **Mobile:** header collapses to logo + CTA; app stacks chart → setup → readings; a sticky mini-disclaimer pins to the bottom (already implemented in `web/assets/styles.css`).

---

## 8. What is explicitly **out of scope** (so no screen implies it)

- Executing trades, holding funds, promising returns (`SCOPE.md`).
- Any agent holding the Owner's private keys.
- Fake testimonials / invented user counts.
- "AI that trades for you" framing.

---

*Prepared by the AI ASTRA AGENCY Creative department (`astra-design-systems`). Generated by an AI agent — no human designer involved.*
