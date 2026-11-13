# Astra Trading — Strategy & Product Plan v2

> **Status:** planning document · **Author:** Product department (`astra-cpo`) · **Date:** 2026-11-13
> **Supersedes:** `PLAN.md` (v1) and extends `AI-SETUPS.md`.
> **Companion files:** `BRIEF.md`, `brand/BRAND.md`, `engine/analysis.py`, `engine/market.py`, `db/001_core_schema.sql`.
>
> **Honesty contract for this document.** Every competitor price, feature and
> complaint below is either (a) taken from a page this department fetched on
> 2026-11-13 (URL given) or (b) explicitly marked **`unverified`**. Where a page
> blocked us (403) or is JavaScript-only, we say so instead of guessing. Numbers
> about *our* product are labelled **estimate**. Nothing here is a promise of
> revenue.

---

## 0. Executive summary (the blunt version)

1. **The category is crowded, the *niche* is not.** Charting (TradingView),
   journaling (TradeZella, Edgewonk), community sentiment (Myfxbook, FX Blue),
   AI scanners (Trade Ideas, TrendSpider) and indicator packs (LuxAlgo) all
   exist and are priced between **$14.95/mo and $349/mo** (verified). **None of
   the eight global competitors we could inspect is a gold-specialised,
   trilingual (ar/en/tr) structure + liquidity analysis product with a public,
   auditable track record.** That intersection is our wedge.
2. **Our real moat is not the algorithm — it is the Arabic/Turkish experience
   plus verifiable honesty.** Anyone can cluster pivots into zones (our engine
   already does). Almost nobody in this market publishes a *raw, un-editable*
   performance log in Arabic. That is defensible because it is a commitment, not
   a feature.
3. **What is genuinely hard (do not pretend otherwise):** (a) reliable, cheap,
   real-time gold data; (b) making an "AI setup" legally safe in every
   jurisdiction we sell to; (c) distribution — a great Arabic gold tool with no
   audience earns nothing; (d) crypto-only payment excludes the majority of
   casual buyers in the Gulf and Turkey, who expect cards and local wallets.
4. **Crypto-only is a deliberate trade-off, not a free win.** It removes
   chargebacks and card-processor risk, but it costs conversion. We must measure
   that cost, not assume it away. See §4.
5. **The "Command Deck" UX is our cheapest differentiator.** Data density,
   disciplined motion and an always-on readings rail can make a $19 tool *feel*
   like a $200 terminal — without a single hype word. See §6.

---

## 1. Competitor teardown

All prices verified by direct page fetch on **2026-11-13** unless marked
`unverified`. Currency is USD unless stated. A 403/JS-only block is recorded as
such — we do not fill the gap with a guess.

### 1.1 Summary table

| Product | Category | Entry price (verified) | Model | Gold/XAU specialisation? | Public track record? | Source URL |
|---|---|---|---|---|---|---|
| **TradingView** | Charting platform | $14.95/mo (Essential); tiers to $239.95/mo | Subscription, monthly/annual | No (multi-asset) | No | https://www.tradingview.com/pricing/ |
| **TradeZella** | Trade journal | $35/mo (Essential); $59 Pro; $99 Ultra | Subscription | No (any instrument) | No | https://www.tradezella.com/pricing |
| **Edgewonk** | Trade journal | $35/mo, or $197 / 12 mo; a **$169** one-off tier is shown | Subscription + one-off | No | No | https://www.edgewonk.com/pricing |
| **Myfxbook** | Trade analytics / community | **unverified** (site returned HTTP 403 to our fetch) | Freemium (unverified) | No | Community track records (user-generated) | https://www.myfxbook.com/ |
| **FX Blue** | Free analytics + tools | Free tools; premium chart tiers **unverified** (`/pricing` → 404) | Freemium | No | No | https://www.fxblue.com/ |
| **Trade Ideas** | AI stock scanner | $127/mo (TI Standard); $254/mo (TI Premium) | Subscription | No — US equities focus | No | https://www.trade-ideas.com/pricing/ |
| **TrendSpider** | Automated TA + AI | Entry tier advertised "7 days for $29" then ~$91/mo; higher tiers to $349/mo | Subscription | No — multi-market | Backtesting, not a public audited log | https://trendspider.com/pricing/ |
| **LuxAlgo** | Indicator / toolkit suite | $24.99/mo (Essential); $39.99 Premium; $59.99 Ultimate; $119.99 Ultra | Subscription | No — indicator packs | No | https://www.luxalgo.com/pricing/ |

> **Note on TrendSpider and TradingView:** both pages are heavily promotional
> (countdown discounts, "65% off"). The numbers above are the **list** figures we
> read in the page payload; the *effective* price a user pays depends on the
> promotion running that day. We treat list price as the comparison anchor.

### 1.2 Per-competitor notes

**TradingView — the charting default.**
- *Does well:* best-in-class charting, huge indicator library, social ideas feed,
  and the price of entry is genuinely low ($14.95/mo).
- *Weakness for our user:* it is a **toolbox, not an answer**. A gold trader still
  has to draw zones, find liquidity and write a plan. Nothing is gold-specific and
  nothing is Arabic-first.
- *The ONE gap we own:* **pre-drawn, gold-specific structure** delivered as a
  plain-language scenario — the work TradingView makes you do, done for you.
- *Blunt:* we can never out-chart TradingView. We must integrate with it (export
  levels, share an ideas link) and win on *interpretation*, not drawing.

**TradeZella — the journal leader.**
- *Does well:* excellent post-trade analytics, broker sync, "Zella" review UX.
- *Weakness:* it is **backward-looking** — you must already have trades to log. It
  gives you nothing *before* the entry.
- *The ONE gap we own:* we operate **pre-trade** (where is the zone, what is the
  plan). A journal is a natural *v2 add-on* for us, not a competitor to beat head-on.
- *Verified price detail:* $35 / $59 / $99 per month; annual billing $315 / $531 /
  $891 per year (page shows "$26 / $44 / $74 per month billed yearly").

**Edgewonk — the disciplined-journaling one-off.**
- *Does well:* strong statistics and psychology framing; a one-off price appeals to
  people who hate subscriptions.
- *Weakness:* same pre-trade blind spot as TradeZella; the UI is dense and dated.
- *The ONE gap we own:* a **one-off "Founder" tier** as a *packaging experiment*
  (see §4), not a permanent model — recurring revenue must dominate.
- *Verified price detail:* page states "invest $169 today", plus $197 / 12 months
  and $35 / month; EU/UK VAT variants are listed (e.g. Germany $234.43 incl. 19%).

**Myfxbook — community + analytics.**
- *Does well:* broker-linked account stats and a long-running community.
- *Weakness:* **unverified pricing** (our fetch was blocked with HTTP 403; the
  site is JS-heavy). Its "track record" is *user-supplied* and self-reported, which
  is exactly the credibility gap we exploit with an *auto-graded* log.
- *The ONE gap we own:* a **system-generated, non-editable** record — the opposite
  of self-reported stats.

**FX Blue — the free-tool giant.**
- *Does well:* an enormous library of genuinely free calculators, charts and
  sentiment tools; strong SEO gravity.
- *Weakness:* free tools with **no opinion** — it shows you data, never a plan.
  Premium chart pricing could not be verified (`/pricing` returned 404).
- *The ONE gap we own:* *synthesis*. Free tools make you assemble the picture;
  we hand you a scenario with entry/stop/targets and the reasoning.
- *Blunt:* FX Blue will out-rank us on generic "position size calculator" SEO. We
  must win on long-tail, intent-rich, *gold-specific* queries (§5).

**Trade Ideas — the AI-scanner benchmark.**
- *Does well:* real-time algorithmic scanning with a long track record of marketing
  the "Holly" AI. At $127–$254/mo it proves traders pay *premium* prices for
  automation.
- *Weakness:* equities-first, English-only, expensive, and it is a *scanner* (a
  list of candidates), not a *gold narrative*.
- *The ONE gap we own:* price anchoring. Trade Ideas at $254/mo makes our
  ~$19/mo look trivial *if we frame the comparison honestly*.

**TrendSpider — automated TA + AI.**
- *Does well:* automated technical analysis, backtesting, and now an AI assistant
  ("Sidekick"). It is the closest philosophical neighbour to us.
- *Weakness:* broad multi-market scope, no gold focus, no Arabic/Turkish, and its
  promotions are aggressive (up to "65% off"), which trains users to wait for sales.
- *The ONE gap we own:* **narrow and deep beats broad and shallow** for one asset
  class — plus a public track record they do not publish.
- *Blunt:* TrendSpider is the competitor most likely to add a gold-AI feature. Our
  defence is language + niche + the honesty brand, not features.

**LuxAlgo — the indicator-pack model.**
- *Does well:* sells TradingView indicator suites at $24.99–$119.99/mo with a
  polished funnel and a free paper-trading account + journal.
- *Weakness:* it is **inside TradingView** — you must have a TradingView plan, and
  the output is indicator lines, not a written plan.
- *The ONE gap we own:* a **standalone answer** that does not require the user to
  own another subscription or learn a new indicator language.

### 1.3 Arabic & Turkish landscape

*Fetch status (2026-11-13):* many regional sites block automated fetches (HTTP
403). We verified the **existence** of the major destinations via the Internet
Archive Wayback Machine (`http://archive.org/wayback/available?url=…`) and record
capability as `unverified` where we could not read the page.

| Tool / destination | Language | Category | Automated S/R or liquidity? | Price | URL (existence verified via Wayback) |
|---|---|---|---|---|---|
| Investing.com (TR) | Turkish | Market data + news | No — data display | Free (ads) | https://tr.investing.com/ |
| Investing.com (SA) | Arabic | Market data + news | No — data display | Free (ads) | https://sa.investing.com/ |
| Mubasher | Arabic | Market data + news | No | Free (ads) | https://mubasher.info/ |
| Argaam | Arabic | Market data + news | No | Free (ads) | https://www.argaam.com/ |
| Altın.in | Turkish | Gold forum + prices | No — community | Free | https://www.altin.in/ |
| Bigpara (Hürriyet) | Turkish | Gold/forex prices | No — data display | Free | https://bigpara.hurriyet.com.tr/ |
| Tradersup | Turkish/English | Broker comparison | No | Free | https://tradersup.com/ |

**Direct answer to the strategic question: does a trilingual, automated
gold-structure tool already exist?** On the evidence we could gather: **no such
product was found** — the Arabic and Turkish landscape we could inspect is
dominated by price-display, news and community sites, not automated structure
analysis with a published track record. This is a **"not found", not a proven
"does not exist"**; a paid search/App-Store crawl is required before we commit
marketing spend to that claim (see §8, open items).

> **Unverified items in §1.3:** exact pricing, feature lists, app ratings and
> download counts for every regional tool (all blocked to automated fetch).


---

## 2. Positioning

### 2.1 The one-sentence position

> **Astra Trading is the gold desk in your pocket: it draws the zones, names the
> liquidity, and hands you a scenario with the reasoning — in Arabic, English or
> Turkish — and it publishes every scenario's real result, win or lose.**

### 2.2 Why we win in ar / en / tr

| Dimension | Incumbents | Astra Trading | Why it matters |
|---|---|---|---|
| **Asset focus** | Multi-asset everything | **Gold only (XAU/USD) at launch** | A specialist can encode gold's session behaviour, its round-number magnetism and its news sensitivity better than a generic tool. |
| **Language** | English-first; Arabic/Turkish as afterthought or absent | **Designed in all three, RTL first** (per `BRAND.md`) | The Gulf + Turkey + Levant gold audience is large and under-served by *analysis* tools. |
| **Output** | Lines, indicators, data tables | **A written scenario** (entry/stop/TPs/R:R + rationale) | Removes interpretation load — the thing a beginner pays to skip. |
| **Trust** | Marketing claims, self-reported stats | **Auto-graded, non-editable public track record** | Directly answers "is this a scam?" — the #1 objection in this market. |
| **Price** | $35–$254/mo (verified) | **~$19/mo anchor (estimate)** | Undercuts TradeZella/Edgewonk/Trade Ideas while beating TradingView on interpretation. |

### 2.3 Positioning statement (internal)

*For gold traders in the Arab world and Turkey who are tired of drawing zones by
hand and being sold "signals", Astra Trading is a gold analysis desk that shows
the structure, the liquidity and a reasoned scenario — and proves its own record —
unlike TradingView (a toolbox), TradeZella/Edgewonk (post-trade journals), or
signal channels (unverifiable).*

### 2.4 What we must NEVER claim (positioning guardrails)

- No "signals", no "guaranteed", no profit promises, no win-rate brags without the
  raw log attached.
- No "AI that trades for you". We are analysis; the user executes.
- No fake social proof. Until we have real users, our landing page shows the
  *track record*, the *method*, and the *disclaimer* — not testimonials we do not have.

---

## 3. Feature map v1 / v2 / v3 (tied to the existing engine)

**What already exists (verified by reading the code):**
- `engine/market.py` — candle fetch from BiQuote (`GET /api/{symbol}/ohlc`), on-disk
  cache, timeframes 1m/5m/15m/30m/1h/4h/1d, `fetch_tick()` for bid/ask/spread.
- `engine/analysis.py` — `atr()`, `sma()`/`ema()`, `swing_points()`,
  `cluster_zones()` (support/resistance with a strength score), `find_zones()`,
  `find_liquidity()` (equal highs/lows, session extremes, round numbers),
  `session_context()` (Asia/London/NY/late in UTC), `bias()` (EMA21/50 structure),
  `build_setup()` (entry/stop/TP1-3/R:R with a `min_rr` gate), `analyse()` (one
  full JSON payload for the chart + setup card).
- `db/001_core_schema.sql` — profiles, subscriptions (7-day trial default),
  setups (with lifecycle enum + outcome fields), setup_events, payments
  (USDT-TRC20 fields), agent_keys, audit_log, alerts, RLS policies, and a public
  `track_record` view.

**Effort scale:** S = ≤2 dev-days · M = 3–5 · L = 6–10 · XL = >10 (estimates, one
competent engineer, assuming data source is solved).

### v1 — "Sellable" (ship the honest core)

| # | Feature | Engine hook | Effort | Notes / risk |
|---|---|---|---|---|
| V1-1 | Trilingual web app (ar RTL / en / tr) on the brand system | — | L | RTL must be designed, not mirrored (`BRAND.md`). |
| V1-2 | Canvas candlestick chart + zone/liquidity/session overlays | `analyse()` payload | L | No external chart lib (offline-safe). |
| V1-3 | Setup card (direction, entry, stop, TP1-3, R:R, confidence, factors) | `build_setup()` | M | Already computed; UI only. |
| V1-4 | Live readings rail (price, bid/ask/spread, ATR, bias, session, distance to S/R) | `fetch_tick()` + `analyse()` | M | The "Command Deck" core (§6). |
| V1-5 | Position-size / risk calculator | new pure function | S | Deterministic; test it. |
| V1-6 | 7-day trial + crypto (USDT-TRC20) subscription gate | schema + on-chain verify | M | Trial fields already in schema. |
| V1-7 | Public track-record page (auto-graded, no PII) | `track_record` view | M | Our trust weapon. |
| V1-8 | Disclaimer on every screen + ToS/Privacy | — | S | Non-negotiable (§7). |
| V1-9 | Timeframe switcher 5m/15m/1h/4h/1D | `market.TIMEFRAMES` | S | Already supported. |

**v1 exit criteria:** a stranger can open the site in any of three languages, see
a gold chart with pre-drawn zones, read a scenario, understand it, and pay — with
the disclaimer visible and the track record public.

### v2 — "Sticky" (retention + alerts)

| # | Feature | Engine hook | Effort | Notes |
|---|---|---|---|---|
| V2-1 | Alerts (email + Telegram) on zone touch / trigger / TP / stop | `setup_events` + alerts table | M | Schema ready. |
| V2-2 | Shadow-mode agent → auto-publish pipeline with approval switch | `agent_keys`, `AI-SETUPS.md` contract | L | Build track record *before* users see it. |
| V2-3 | Auto-grading worker (price vs setup → WIN/LOSS/BE, writes `outcome_r`) | new worker | L | Must be non-editable; audit-logged. |
| V2-4 | User trade journal + stats (win rate, R, expectancy) | new tables | L | Competes with TradeZella on *our* terms. |
| V2-5 | Circuit breaker (3 losses or negative weekly R → auto-halt publishing) | worker + alerts | S | Reputation protection. |
| V2-6 | Post-mortem note per setup ("why it won/lost") | LLM + rationale fields | M | Educational, builds trust. |
| V2-7 | Weekly report email (trilingual) | template + cron | M | Retention driver. |
| V2-8 | TradingView level export / ideas-link share | — | S | Distribution wedge (§5). |

### v3 — "Scale" (expand only after gold is proven)

| # | Feature | Effort | Notes |
|---|---|---|---|
| V3-1 | Additional assets (silver, DXY, majors) | L | Only after gold unit economics are positive. |
| V3-2 | Multi-agent ranking (rank sources by real performance) | L | `AI-SETUPS.md` §7.9. |
| V3-3 | Public API for third-party analysis agents | L | Write-only ingestion, already designed. |
| V3-4 | Android app (Play Store) — see §8 owner dependencies | XL | Store account is an owner dependency. |
| V3-5 | Community room / discussion | XL | High moderation cost — treat as a separate product. |

> **Engineering reality check:** the engine is a solid skeleton, but `bias()` and
> `build_setup()` are **simple heuristics**, not a validated edge. Before we sell
> performance, we must run `AI-SETUPS.md` §7.1 **shadow mode** and measure the
> real hit rate. If it is not better than random, we sell *structure and process*
> (which is still valuable) and **never** imply predictive skill.

