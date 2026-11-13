# Astra Trading — Analysis Methodology (XAU/USD)

**Document ID:** `ASTRA-METH-001`
**Version:** 1.0.0
**Status:** normative — this document is the specification the engine must satisfy.
**Scope:** the rule-based analysis engine that turns raw XAU/USD candles into
auditable trade *scenarios* ("setups") and scores them.
**Normative code:** `engine/analysis.py`, `engine/evaluator.py`,
`engine/backtest.py`, `engine/market.py`, `api/app.py`, `db/001_core_schema.sql`.

This document specifies every rule the engine applies, in reproducible and
implementable terms, with the formula and the rationale for each. It is written
so that an independent quant can reimplement the engine from this text alone and
reproduce its published outputs, level for level. Where the shipped code is
weaker than this specification, the gap is listed explicitly in
[§11 Implementation gaps](#11-implementation-gaps); we do not pretend the code
and the paper are the same thing.

A companion machine-readable summary of constants lives in
[§12 Parameter table](#12-parameter-table).

---

## 0. Conventions, notation and units

| Symbol | Meaning |
|---|---|
| $O_t, H_t, L_t, C_t$ | open, high, low, close of bar $t$ |
| $t$ | bar **open time**, ISO-8601 UTC |
| $T$ | timeframe (one of `1m,5m,15m,30m,1h,4h,1d`) |
| $N$ | number of bars in the working window |
| $\text{ATR}$ | Average True Range, defined in [§2](#2-volatility-atr) |
| $\text{mid}(z)$ | $(z.low + z.high)/2$ for a zone $z$ |
| $R$ | one unit of risk $= |entry - stop|$ |
| $x \times \text{ATR}$ | "ATR multiple" — a distance expressed in volatility units |

**Ordering convention.** The data layer (`market.fetch_candles`) returns candles
**newest-first**: `candles[0]` is the most recent bar. The analysis functions
internally reverse to **oldest-first** before doing any time-ordered work. All
formulas below are stated oldest-first; the implementation's reversals are
noted where they matter.

**Price convention.** All prices are quoted in USD per troy ounce. The engine
never converts units and never assumes a contract size; only price distances
matter. One price unit on XAU/USD is $1.00/oz.

**Determinism.** Every function in `engine/analysis.py` is a pure function of
its inputs (candles, parameters). There is no randomness, no clock dependence
except `session_context()` and the liquidity session-extreme rule, and no
network access inside the analysis functions. Given identical candles and the
same `now`, the engine produces identical output. This is a precondition for a
reproducible public track record.

---

## 1. Data

### 1.1 Source

Candles are OHLC bars aggregated by **MetaTrader 5**, retrieved through the
**BiQuote** public OHLC endpoint (`market.py`):

```
GET {BIQUOTE_BASE}/api/{symbol}/ohlc?interval={T}&count={N}
```

- `BIQUOTE_BASE` defaults to `https://biquote.io` (env override).
- The symbol is `XAUUSD`. BiQuote aggregates an MT5 feed; the values are the
  MT5 OHLC aggregates, not a synthetic reconstruction.
- Each bar carries an `openTime` (UTC), `open/high/low/close`, and a tick
  `volume` (`tickVolume`). **Tick volume is not traded volume** and the engine
  does not use it in any signal — see [§9](#9-known-limitations).
- The payload is a JSON object with a `bars` array. Anything else yields an
  empty candle list rather than an exception.

**Caching.** Responses are cached on disk (`ASTRA_CACHE_DIR`, default
`/tmp/astra-cache`) keyed by `(symbol, timeframe, count)`, with a default TTL of
60 s (`ttl` argument; 45 s in the evaluator, 0 = bypass). Rationale: the source
is free and unauthenticated; caching keeps request volume low and lets the
engine run offline in tests. On fetch failure after `retries = 3` attempts
(back-off $1.5 \times (\text{attempt}+1)$ s), a **stale** cache file is served if
present ("stale beats none"); only if neither fresh nor stale data exists does
the fetch raise. The evaluator and loop treat a raised fetch as "skip this
symbol this pass", never as a fabricated bar.

### 1.2 Timeframes

Supported: `1m, 5m, 15m, 30m, 1h, 4h, 1d` (`market.TIMEFRAMES`). Any other
token raises `ValueError`. The live agent scans `1h, 4h, 15m`
(`agent.TIMEFRAMES`) and keeps the single highest-confidence setup across those
timeframes.

### 1.3 Cleaning rules (gaps, NaNs, sentinels)

Two cleaning layers exist and they are deliberately identical in spirit.

**Layer A — parse-time (`market._parse`).** A bar is dropped unless *all* hold:

1. `open, high, low, close` are present and castable to `float`;
2. every value is finite (`math.isfinite`) **and strictly positive**;
3. `high >= low`.

Bars are then sorted by open time, newest-first.

**Layer B — analysis-time (`analysis._clean`).** Applied again at the entry of
every analysis function, because candles can also arrive from the API or tests:

1. all of $O,H,L,C$ finite (rejects `NaN`, `±inf`, and booleans);
2. $\min(O,H,L,C) > 0$ (rejects zero and negative sentinels such as `-1`,
   `0`, or `-9999` used by some feeds for "missing");
3. $H \geq L$ (rejects inverted bars).

**Rationale for two layers.** Layer A protects the wire boundary; Layer B
guarantees the invariant *inside* every consumer, so a single bad bar injected
by any caller cannot propagate a `NaN` through ATR (which would poison every
downstream number). One bad bar must never take the whole analysis down; it is
skipped, not repaired.

**Gaps.** The engine does **not** interpolate or forward-fill missing bars.
A weekend or holiday gap simply means the next bar's true range spans the gap,
which is exactly what Wilder's TR formula ([§2](#2-volatility-atr)) is designed
to absorb. Fabricating synthetic bars to "close" a gap would invent price that
never traded — prohibited by [§8](#8-honesty-rules). The engine also does **not**
resample or align timeframes to a common clock; each timeframe is analysed
independently on its own bars.

**Sentinels.** Beyond the numeric checks above, the engine has no sentinel
table. It assumes the source emits either a valid bar or omits it. Any bar whose
OHLC fails the three tests is treated as absent. This is conservative: a
dropped bar can only make ATR *slightly* wrong, never fake a level.

---

## 2. Volatility: ATR

### 2.1 Definition

The engine uses **Wilder's Average True Range** with period $p = 14$
(`analysis.atr(candles, period=14)`). Let the cleaned, oldest-first series be
$b_1,\dots,b_n$ with $n \ge 2$. The true range of bar $i$ ($i \ge 2$) is

$$
\text{TR}_i = \max\bigl(H_i - L_i,\; |H_i - C_{i-1}|,\; |L_i - C_{i-1}|\bigr)
$$

This is exactly Wilder's definition: the bar's own range, extended to cover a
gap from the previous close. The engine's ATR is the **simple arithmetic mean of
the most recent $p$ true ranges**:

$$
\text{ATR}_p = \frac{1}{p}\sum_{i=n-p+1}^{n} \text{TR}_i
$$

with $p = 14$, and $\text{ATR} = 0$ when fewer than two bars are available or no
true range can be formed. *Reference:* J. Welles Wilder Jr., *New Concepts in
Technical Trading Systems* (1978), ch. 2 — TR and ATR. This is the same
volatility measure used in Wilder's own volatility and directional-movement
systems.

### 2.2 Smoothing choice, and honest disclosure

Wilder's original ATR is an **exponential/Wilder-smoothed** average with
smoothing factor $1/p$:

$$
\text{ATR}_i = \frac{(p-1)\,\text{ATR}_{i-1} + \text{TR}_i}{p}
$$

The shipped code uses the **simple mean of the last $p$ true ranges**, which is
a standard and widely used simplification (and is what most charting packages
call "ATR(14)"). The two agree closely; the simple mean reacts marginally faster
to a step change and needs no warm-up seed. We state this explicitly rather than
claim Wilder-smoothing: **the engine is Wilder-*style* simple-mean ATR, not
Wilder-*recursive* ATR.** A future version may offer the recursive form; the
distinction is logged in [§11](#11-implementation-gaps).

### 2.3 Why ATR gates everything else

ATR is the engine's unit of *scale*. XAU/USD is quoted at four-digit dollar
levels where a "large" move in 2015 is a rounding error in 2026; absolute price
distances are meaningless across regimes. Every distance rule in the engine is
therefore expressed as a multiple of ATR:

| Rule | ATR expression |
|---|---|
| Zone merge tolerance | $0.35 \times \text{ATR}$ (floor 0.40) |
| Liquidity equality tolerance | $0.25 \times \text{ATR}$ (floor 0.30) |
| Zone relevance band | $12 \times \text{ATR}$ (floor 1% of price) |
| Stop padding beyond zone | $0.5 \times \text{ATR}$ |
| "Liquidity nearby" test | $2 \times \text{ATR}$ |

**Rationale.** A zone or an equal-high that is only 20 cents wide on a day with
ATR = 12 is noise; on a day with ATR = 1.2 the same 20 cents is a real feature.
Scaling by ATR makes every threshold self-calibrating to the current regime, so
the engine does not need a human to retune it as gold's volatility changes. If
$\text{ATR} \le 0$ or non-finite, `build_setup` returns `None` — **no volatility
estimate, no setup.** We never fall back to a guessed volatility.

---

## 3. Support / Resistance Zones

This is the heart of the engine. A *level* is a single price; a *zone* is a
band. The engine only ever publishes **zones**, because markets respect bands,
not lines.

### 3.1 Swing pivot detection

**Method: symmetric fractal (rolling-window) pivots.**

Given cleaned candles oldest-first and parameters `left = k`, `right = k` with
$k = 2$ (`swing_points(candles, left=2, right=2)`), index $i$ is a **swing high**
iff

$$
H_i \ge \max_{j \in [i-k,\,i+k]} H_j
$$

and a **swing low** iff

$$
L_i \le \min_{j \in [i-k,\,i+k]} L_j
$$

Only indices $i$ with $k \le i \le n-k-1$ are considered (a pivot needs $k$ bars
on each side). The pivot is recorded as $(i, \text{price}, \text{openTime})$.

**Tie-breaking.** The comparison uses `>=` (highs) and `<=` (lows). A flat
plateau of equal highs therefore yields *every* bar of the plateau as a pivot,
which is intentional: equal highs are liquidity, not a single point
([§4](#4-liquidity)). The consequence — many near-duplicate pivots — is
collapsed by the clustering step.

**Lookback choice $k=2$.** $k$ controls the minimum prominence of a pivot:
larger $k$ finds only "bigger" swings. $k=2$ is the engine default because it
captures the short-term swings a discretionary intraday gold trader actually
marks, while the subsequent ATR-based clustering (below) filters the trivial
ones. It is a **parameter**, not a law: `k` is exposed and the backtester and
tests can override it.

**Confirmation latency (important).** A pivot at index $i$ cannot be known until
bar $i+k$ has closed. Every pivot used by the engine is therefore **confirmed by
$k$ bars**, i.e. it is at least $k$ bars old. There is no look-ahead: the
backtester only ever feeds `build_setup` the bars up to time $t$ and asks for a
view *at* $t$ ([§7](#7-evaluation-and-backtesting)).

### 3.2 Clustering pivots into zones

Swing prices are grouped into zones by a **single-linkage sweep** over
price-sorted pivots (`cluster_zones`).

Let the pivot prices of one kind (highs→resistance, lows→support) be sorted
ascending: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$. With merge tolerance
$\theta$ (see [§3.3](#33-zone-width-as-a-function-of-atr)), pivots $p_{(j)}$ and
$p_{(j+1)}$ join the same zone iff

$$
p_{(j+1)} - p_{(j)} \le \theta
$$

Each maximal run of pivots joined this way is one zone. For a run with prices
$\{p\}$:

$$
z.low = \min\{p\}, \qquad z.high = \max\{p\}, \qquad z.touches = |\{p\}|
$$

**Merge rule, stated exactly.** This is **single-linkage chaining on the price
axis**: pivots are connected to their *nearest already-grouped* neighbour, not
to the group's mean. Consequence: a chain of pivots each within $\theta$ of the
next forms a single zone that may be *wider* than $\theta$ (up to $m\theta$ in
the degenerate case). We accept this because a real supply/demand band often has
a sloping edge; the chaining captures it, and the resulting width feeds the
tightness penalty in [§3.4](#34-zone-strength-scoring), which penalises exactly
these over-wide bands.

### 3.3 Zone width as a function of ATR

The merge tolerance is **volatility-scaled**:

$$
\theta = \max\bigl(0.35 \times \text{ATR},\; 0.40\bigr)
$$

The 0.40 floor is a fixed 40-cent minimum band so that on a dead-flat Asian
session (ATR well under 1) two pivots are not merged merely because "everything
is equal". The $0.35 \times \text{ATR}$ term makes the band widen with the
regime: at ATR = 10 the tolerance is 3.50; at ATR = 1 the tolerance is 0.40.

**Rationale.** The correct width of a support band is the noise scale of the
instrument at that moment. Fixing the width in dollars would make the engine
either over-merge in quiet markets or fragment in volatile ones. Tying it to
ATR is the minimal assumption that keeps one band ≈ one decision.

### 3.4 Zone strength scoring

Each zone receives a strength $S \in [0,1]$ (`cluster_zones`):

$$
S = \min\Bigl(1,\; 0.35 \cdot \tau \;+\; 0.40 \cdot \phi \;+\; 0.25 \cdot \tfrac{\min(\tau,3)}{3}\Bigr)
$$

where

- $\tau = z.touches$ — the number of pivots in the zone (how often price turned
  there);
- $\phi$ — **tightness**:
  $$
  \phi = \begin{cases}
  1 & z.high = z.low \\
  \max\bigl(0,\; 1 - \dfrac{z.high - z.low}{2\theta}\bigr) & \text{otherwise}
  \end{cases}
  $$
  a zone half as wide as the tolerance scores 0.5; a zone as wide as $2\theta$
  scores 0.

**Rationale for the weights.** The three terms encode the three things that make
a level tradeable:

1. **Repetition (0.35, linear in touches).** A level price has rejected more
   than once is more likely to matter again. Linear (not saturating) because
   each additional touch is genuine evidence.
2. **Tightness (0.40, the largest single weight).** A narrow band is a precise
   level; a wide band is a vague region and a poor place to put a stop. This is
   why tightness carries the most weight.
3. **Saturation term (0.25, $\min(\tau,3)/3$).** Rewards reaching 3 touches
   (a classic "triple tap") without letting a 10-touch zone dominate purely by
   count.

$S$ is clamped to 1. Zones are sorted by $S$ descending; `build_setup` picks the
strongest relevant zone in the trade direction.

### 3.5 Recency / freshness

**Documented rule (intended).** A zone that was last touched 200 bars ago is
weaker than one touched 5 bars ago. The engine stores `last_touch` (the open
time of the most recent pivot in the zone) on every zone and exposes it, but the
**current strength formula does not decay with age.** This is a known gap: a
freshness factor of the form

$$
S' = S \cdot \exp\!\Bigl(-\frac{\text{bars since } z.last\_touch}{\lambda}\Bigr),
\quad \lambda \approx 50\text{–}100 \text{ bars}
$$

is specified here as the intended behaviour and listed in
[§11](#11-implementation-gaps) as not yet implemented.

### 3.6 Reaction magnitude, session context (documented, partial)

Two further strength inputs are specified but not yet in the shipped formula:

- **Reaction magnitude.** The size of the move *away* from the pivot
  (e.g. the distance from the pivot price to the next opposite swing, in ATR)
  is evidence of how forcefully the level rejected. Intended as a multiplicative
  factor. Not implemented — gap.
- **Session context.** A touch during London/NY (high liquidity) is more
  meaningful than one in thin late-session trade. The engine already computes
  `session_context()` and tags the *setup* with its session
  ([§5](#5-confluence)), but does not yet fold session into *zone* strength —
  gap.

### 3.7 Relevance filter

Only zones within the relevance band of current price are returned
(`relevant`):

$$
|mid(z) - C_0| \le \max\bigl(12 \times \text{ATR},\; 0.01 \times C_0\bigr)
$$

where $C_0$ is the current (newest) close. The $0.01 \times C_0$ floor is a 1%
band so that on an extremely quiet tape the engine still considers nearby
structure. Kept zones are sorted by absolute distance to price, nearest first.

**Rationale.** A zone 300 dollars away is not actionable for a setup entered
now; publishing it would be noise. The 12×ATR band is generous enough to keep
the "target" zones a trade would travel toward, while trimming the far tail.

### 3.8 Broken vs respected zones

**Respected.** A zone whose band has not been closed through recently: price
approaches, reacts, leaves. The engine implicitly treats every clustered zone as
*respected* at the moment of analysis (it is built from pivots that were, by
construction, turning points).

**Broken.** A zone that price has closed decisively through. The current code
does **not** test or label broken zones; it relies on the pivot window plus the
relevance band to age them out. A zone built on old pivots that price has since
sliced through will still be reported until its pivots fall out of the working
window. The intended rule is: *a zone is broken once a bar closes beyond its far
edge by more than $0.5\times\text{ATR}$; broken zones are demoted, and a broken
resistance becomes candidate support (role reversal).* Not implemented — gap
(see [§11](#11-implementation-gaps)).

---

## 4. Liquidity

Liquidity pools are prices where resting orders (especially stop-losses) are
likely to cluster, and which price is therefore drawn toward. The engine detects
four kinds (`find_liquidity`).

### 4.1 Equal highs / equal lows

Scan the cleaned series oldest-first. For each bar $i$, look ahead at most 11
bars ($j \in [i+1, \min(i+12, n))$). If any bar $j$ satisfies

$$
|H_i - H_j| \le \lambda \quad\text{(equal highs)}
\qquad\text{or}\qquad
|L_i - L_j| \le \lambda \quad\text{(equal lows)}
$$

with liquidity tolerance

$$
\lambda = \max\bigl(0.25 \times \text{ATR},\; 0.30\bigr)
$$

then one liquidity object is emitted at the average of the two prices,
kind `equal_highs` / `equal_lows`, strength $0.7$, note "buy-side / sell-side
liquidity". The inner loop `break`s after the first match for a given $i$, so
each $i$ contributes at most one equal-high and one equal-low object; the
dedupe step ([§4.5](#45-dedupe-and-ranking)) collapses the rest.

**Rationale for the window (≤12 bars).** Equal highs matter when they are close
in *time*: two highs 200 bars apart at the same price are a coincidence; two
within half a day on 1h are a deliberate double top. The window bounds this.

**Rationale for tolerance $\lambda$.** Two highs must be "the same" to a
trader's eye; $\lambda$ is set *tighter* than the zone tolerance $\theta$
(0.25 vs 0.35 × ATR) because "equal" should mean near-identical, not
merely co-located in a band.

### 4.2 Session extremes

For the **current UTC calendar day** (the substring `YYYY-MM-DD` of each bar's
open time), the engine emits the day's high as `session_high` ("stops above",
strength 0.6) and the day's low as `session_low` ("stops below", strength 0.6).
If no bar belongs to the current UTC day, none are emitted.

**Rationale.** The session high/low is the day's visible battle line; stops and
breakout orders accumulate just beyond it. Strength 0.6 is above round numbers
but below equal highs, reflecting that a single day's extreme is a softer
reference than a tested double top.

**Known fragility.** The day is derived from the *system clock* (`datetime.now
(UTC)`), and matching is by string prefix on the bar's `openTime`. This assumes
`openTime` is ISO-8601 with a `YYYY-MM-DD` prefix — true for BiQuote, but a
format change would silently yield zero session extremes. Listed in
[§11](#11-implementation-gaps).

### 4.3 Round numbers

Psychological levels. Let `ref` = current close. The grid step is

$$
\text{step} = \begin{cases} 25.0 & ref > 1000 \\ 1.0 & \text{otherwise}\end{cases}
$$

and the engine emits levels $\text{base} + k\cdot\text{step}$ for
$k \in \{-2,-1,0,1,2\}$ where $\text{base} = \text{round}(ref/\text{step})\cdot
\text{step}$. Each carries strength 0.45 and a "round level" note.

**Rationale.** Traders place orders at "2000", "2050" — round numbers in the
instrument's own quote granularity. For gold above \$1000 the natural grid is
\$25 (the historically traded increments); below \$1000 it is \$1. The $k$ range
keeps the five nearest levels. Strength 0.45 is the lowest of the four kinds:
round numbers are the weakest, most subjective liquidity signal, and the engine
says so in the number.

### 4.4 Strength hierarchy

| Kind | Strength | Why |
|---|---|---|
| `equal_highs` / `equal_lows` | 0.70 | an explicit, testable double tap |
| `session_high` / `session_low` | 0.60 | the day's real battle line |
| `round_number` | 0.45 | psychological, weakest |

These constants are deliberately ordered and are not tunable per-call.

### 4.5 Dedupe and ranking

All liquidity objects are sorted by (strength desc, distance to price asc). A
`(kind, price rounded to 2dp)` key deduplicates; the first (strongest, nearest)
of each pair survives. The final list is re-sorted by absolute distance to
current price. `analyse()` truncates the payload to the nearest 12.

---

## 5. Confluence

### 5.1 Structure bias

Direction is chosen from **structure**, not from a zone
(`bias(candles)`), using two EMAs of the close (oldest-first):

$$
\text{EMA}_p[i] = \alpha\,C_i + (1-\alpha)\,\text{EMA}_p[i-1],\quad
\alpha = \frac{2}{p+1},\quad \text{EMA}_p[0] = C_0
$$

with $p \in \{21, 50\}$. Let $f = \text{EMA}_{21}[-1]$, $s = \text{EMA}_{50}[-1]$,
$L = C[-1]$ (last close). Then:

| Condition | `direction` | `score` |
|---|---|---|
| $f > s$ **and** $L > f$ | `bullish` | 0.7 |
| $f < s$ **and** $L < f$ | `bearish` | 0.7 |
| $f > s$ (only) | `bullish_weak` | 0.4 |
| $f < s$ (only) | `bearish_weak` | 0.4 |
| otherwise | `neutral` | 0.2 |

`build_setup` proceeds on any direction whose name `startswith("bullish")` or
`("bearish")`; `neutral` yields no setup. The `score` feeds the confidence
formula ([§5.3](#53-the-confidence-number)).

**Rationale.** EMA21/EMA50 is the canonical "fast/slow trend" pair. Requiring
price to be on the correct side of the fast EMA (not just the EMAs crossed)
avoids trading a stale cross, hence the higher score for the fully-aligned
cases.

### 5.2 The four confluence inputs

The engine's public claim is that a setup is **confluence of four things**. In
the shipped code their roles are:

| Input | Implemented? | Role |
|---|---|---|
| **Zone** | yes (required) | the entry level and stop anchor; its strength enters confidence |
| **Structure/EMA bias** | yes (required) | selects direction; its score enters confidence |
| **Liquidity** | yes (reported) | nearest pools within $2\times$ATR are listed as factors and shown; **not yet a numeric confidence input** |
| **Fibonacci** | **no** | specified here, not implemented (gap) |
| **Session context** | yes (tagged) | attached to the setup; **not yet a numeric confidence input** |

**Intended Fibonacci rule (specified, not built).** Retracement of the most
recent confirmed swing leg: compute the leg from the last opposite swing pivot
to the current extreme; levels at $0.382, 0.5, 0.618, 0.786$ of that leg; a zone
whose band contains one of these levels gains a confluence bonus. *Reference:*
the Fibonacci retracement convention as popularised by R. N. Elliott / standard
technical-analysis texts; we treat it as a heuristic overlay, not a law of
nature.

### 5.3 The confidence number

Confidence is a single scalar in $[0,1]$ (`build_setup`):

$$
\text{conf} = \min\bigl(0.95,\; 0.45 + 0.25 \cdot b + 0.15 \cdot S_z\bigr)
$$

where $b \in \{0.2, 0.4, 0.7\}$ is the bias score and $S_z$ is the chosen
zone's strength. Examples:

| bias $b$ | zone $S_z$ | conf |
|---|---|---|
| 0.7 | 1.0 | $\min(0.95, 0.45+0.175+0.15)=0.775$ |
| 0.7 | 0.5 | $0.45+0.175+0.075 = 0.70$ |
| 0.4 | 0.5 | $0.45+0.10+0.075 = 0.625$ |
| 0.2 | 0.0 | $0.45+0.05+0 = 0.50$ |

**Rationale.** The 0.45 base says "any setup that passed the geometry and R:R
filters starts at coin-flip-plus". The 0.25 weight on structure and 0.15 on zone
strength are the two things the engine actually measures; their sum (0.40) is
the maximum lift. The 0.95 ceiling exists because **no rule-based system should
claim near-certainty**, and an uncapped linear sum could exceed 1. The formula
is deliberately simple and fully auditable — there is no hidden model.

**What confidence is *not*.** It is **not** a win probability and must never be
presented as one ([§8](#8-honesty-rules)). It is an ordinal quality score for
ranking candidate setups against each other. Its only operational use is that
the agent keeps the highest-confidence setup across timeframes.

---

## 6. Setup construction

`build_setup(candles, timeframe, min_rr=1.5)` returns a `Setup` or `None`.
A `None` is a first-class result: the disciplined answer is often "no trade".

### 6.1 Preconditions

- At least **60** cleaned bars ($N \ge 60$). Rationale: EMA50 and ATR14 both need
  warm-up; below 60 the structure read is unreliable.
- $\text{ATR} > 0$ and finite.

If either fails → `None`.

### 6.2 Entry type and level

Entry type is always `"limit"`: the engine proposes a *passive* entry at the
zone edge, not a market chase.

- **Long** (bias bullish): choose the strongest support zone with
  $z.low < C_0$ (below current price). Entry $= z.high$ (the **upper** edge of
  the band — you are filled on the way *down* into the zone).
- **Short** (bias bearish): choose the strongest resistance zone with
  $z.high > C_0$ (above price). Entry $= z.low$ (the **lower** edge).

Selection is `max` by `(strength, edge)`; ties break toward the nearer edge.
If no zone qualifies in the bias direction → `None`.

**Rationale.** Entering at the zone edge nearest the market maximises the chance
the limit fills and minimises the distance to the invalidation. Entering at the
far edge would demand a deeper retracement that often never comes.

### 6.3 Stop placement — and why beyond 0.5×ATR

$$
\text{stop}_{\text{long}} = z.low - 0.5 \times \text{ATR}
\qquad
\text{stop}_{\text{short}} = z.high + 0.5 \times \text{ATR}
$$

**Rationale for the 0.5×ATR padding.** A stop placed *exactly* at the zone edge
sits on the level where, by construction, price is expected to probe and wick.
A single tick of noise or spread would take it out. Half an ATR is the
empirically reasonable "one wick" buffer: large enough to survive the normal
intrabar excursion that does not break the level, small enough that the risk
stays proportionate to the zone. It is a *volatility-scaled* buffer precisely
because the size of a normal wick is the current ATR, not a fixed number of
dollars. The engine's own tests assert this invariant
(`stop respects 0.5xATR padding`).

If the resulting risk $|\text{entry} - \text{stop}| \le 0$ → `None`.

### 6.4 Targets

Targets are pure **R multiples** of the risk:

$$
\text{long}: \;\; tp_1 = e + R,\;\; tp_2 = e + 2R,\;\; tp_3 = e + 3R
$$
$$
\text{short}: \;\; tp_1 = e - R,\;\; tp_2 = e - 2R,\;\; tp_3 = e - 3R
$$

with $R = |e - \text{stop}|$. **Rationale.** R-multiple targets make the reward
side regime-independent and make the track record directly comparable across
setups: a result is always reported in $R$, never in dollars. (A production
upgrade would anchor $tp_2$/$tp_3$ to the next opposing zone/liquidity pool;
the R-multiple form is the transparent baseline — see
[§11](#11-implementation-gaps).)

### 6.5 Minimum R:R

The setup's reported R:R is the **tp2** reward over risk:

$$
\text{R:R} = \frac{|tp_2 - e|}{|e - \text{stop}|}
$$

and the engine rejects the setup unless $\text{R:R} \ge \text{min\_rr}$
(default **1.5**). The API independently rejects anything below **1.0** at
ingest (`api/app.py`), a second, looser floor. **Rationale.** A 1.5 minimum on
tp2 means the *second* target alone pays 1.5× risk, so even a trade that only
reaches tp2 is profitable; requiring 2R for the *first* target would be
needlessly strict given the 1/2/3 ladder.

### 6.6 Invalidation and validity window

- **Invalidation** is published as a text condition, e.g. long:
  `"close below {stop}"`, short: `"close above {stop}"`. It is the human-facing
  statement of what makes the idea wrong.
- **Validity window.** `build_setup` does not set one; the **API** stamps
  `validity_until = now + validity_hours`, with `validity_hours` default **24**
  (allowed 1–168). If the entry is never touched before `validity_until`, the
  evaluator expires the setup ([§7](#7-evaluation-and-backtesting)).

### 6.7 Setup identity and idempotency

Identity is `symbol | timeframe | direction | entry | forming-bar-open-time`
hashed to `astra-analysis-<sha256[:32]>` (`agent.setup_idempotency_key`). The API
stores it as a `UNIQUE` key and returns the existing row on replay. **Rationale.**
Re-scanning the same still-forming bar must not create a duplicate; a genuinely
new bar with a new entry is a new setup.

### 6.8 Concurrent-open cap

The API caps concurrently open setups (`proposed` + `triggered`) at
`ASTRA_MAX_OPEN_SETUPS`, default **3**, returning HTTP 409 beyond it.
**Rationale.** Discipline by construction: the engine must choose its best
ideas, not flood the user. This mirrors the product rule "the AI waits for the
opportunity".

---

## 7. Evaluation and backtesting

### 7.1 Lifecycle

```
                 ┌──────────┐
   API ingest →  │ PROPOSED │──── validity_until elapsed ──► EXPIRED
                 └────┬─────┘
                      │ entry touched by a bar
                 ┌────▼─────┐
                 │TRIGGERED │
                 └────┬─────┘
        ┌─────────────┼───────────────┬────────────────┐
        ▼             ▼               ▼                ▼
    STOPPED      TP1_HIT ──►     TP2_HIT ──►      TP3_HIT
   (outcome_r=  (outcome_r=     (outcome_r=      (outcome_r=
      -1.00)        +1.00)          +2.00)           +3.00)
```

Status enum (DB): `proposed, triggered, tp1_hit, tp2_hit, tp3_hit, stopped,
breakeven, expired, invalidated, cancelled`. Every transition is written to
`setup_events` with `from_status, to_status, price, reason, at` — an append-only
audit trail ([§8](#8-honesty-rules)). Only `proposed` and `triggered` are "open".

### 7.2 Which bars are considered

The evaluator (`evaluate_one`) works oldest-first over the fetched window and
considers a bar iff **it is the newest (still-forming) bar, or its open time is
≥ the setup's `created_at`.** Rationale: a setup can only be acted on by price
that occurred after it was published — this is the anti-look-ahead guard for the
live scoreboard. The newest bar always counts because its high/low already
contain the live price.

### 7.3 Trigger rule

For a `proposed` setup, iterate the eligible bars in time order; the setup
triggers at the **first** bar whose range touches the entry:

$$
\text{long: } L \le e \qquad\text{short: } H \ge e
$$

On trigger: status → `triggered`, `triggered_at` set to that bar's open time, an
event logged at price $e$. If no bar touches the entry before `validity_until`
(system clock past the deadline), status → `expired`.

### 7.4 Stop-first inside a bar (conservative resolution)

Once `triggered`, for each eligible bar the evaluator checks the **stop before
any target**:

- long stopped iff $L \le \text{stop}$; short stopped iff $H \ge \text{stop}$.

If the stop is hit, the setup closes at the stop regardless of whether the same
bar's range also reached a target. **This is the single most important honesty
rule in the engine.** OHLC bars do not reveal intrabar path; assuming the
adverse move happened first is the *pessimistic* resolution. A backtest that
assumed the target first would overstate results; the engine refuses to.

If the stop was not hit, the evaluator checks targets in order $tp_1, tp_2,
tp_3$ and closes at the **highest target reached in that bar**:

- long $H \ge tp_i$ / short $L \le tp_i$.

Reaching $tp_1$ moves the setup to `tp1_hit` and **keeps it open** (a partial);
reaching the final target ($tp_3$) sets `closed_at`. (There is no explicit
breakeven or trailing logic in the shipped evaluator — see
[§11](#11-implementation-gaps).)

### 7.5 outcome_R computation

The realised R multiple at the closing event is

$$
\text{outcome\_R} = \frac{\text{signed move}}{|e - \text{stop}|},
\qquad
\text{signed move} = \begin{cases}
P - e & \text{long}\\ e - P & \text{short}
\end{cases}
$$

where $P$ is the closing price (`stop` for a stop-out, $tp_i$ for a target hit).
Rounded to 2dp. A stop-out is exactly $-1.00$; a $tp_1$ hit is $+1.00$; $tp_2$
$+2.00$; $tp_3$ $+3.00$. Zero risk returns $0.0$ (no divide-by-zero).

### 7.6 Backtester (offline, no look-ahead)

`engine/backtest.py` replays the engine's own logic over history:

1. Walk bars oldest-first; at bar $i \ge \text{WARMUP}=60$, call `build_setup` on
   a window of the most recent `LOOKBACK = 200` bars **ending at $i$** — no
   future bars.
2. If a setup appears, it enters on **bar $i+1$**, and only if that bar's range
   actually trades the entry ($L \le e \le H$); otherwise the setup is skipped,
   not counted.
3. Exit at the first of stop or $tp_1$; **ties resolve to the stop** (worst
   case). One position at a time; step is every 4th bar.
4. Reports `trades, wins, losses, win_rate, total_r, avg_r, max_drawdown_r`
   (drawdown as the worst peak-to-trough of the R equity curve).

**Honesty gate.** The backtester marks the sample `sample_adequate` only at
$\ge 30$ closed trades, and prints an explicit note below that. It also notes
the data source caps history (≈101 bars per timeframe), so a statistically
meaningful sample needs a longer-history feed. **Backtest numbers below 30
trades are reported but must never be quoted as performance**
([§8](#8-honesty-rules)).

---

## 8. Honesty rules

The product's promise is an *auditable* record, not a flattering one.

### 8.1 What we publish

- Rule-based scenarios with entry, stop, three targets, R:R, the factor list,
  the session, and the invalidation condition.
- The **published track record**, computed by SQL from the database — never
  typed by hand, never edited after the fact.

### 8.2 What we never claim

- **We never claim a win probability.** `confidence` is an ordinal quality
  score, not $P(\text{win})$, and is never labelled as such.
- **We never claim future returns, "signals that print money", or guaranteed
  outcomes.** Every setup carries an educational-analysis disclaimer.
- **We never fabricate, backfill or edit a published outcome.** Outcomes are
  written by the evaluator against real candles and appended to `setup_events`.
- **We never execute trades or touch user funds.** The engine outputs text; the
  user decides.
- **We never quote a backtest below the adequacy threshold** as evidence of edge.

### 8.3 How the public track record is computed

The public record is a **database view**, `public.track_record`
(`db/001_core_schema.sql`), over `setups WHERE published = true`:

```sql
select
  count(*) filter (where status in ('tp1_hit','tp2_hit','tp3_hit')) as wins,
  count(*) filter (where status = 'stopped')                      as losses,
  count(*) filter (where status = 'breakeven')                    as breakevens,
  count(*) filter (where status in ('proposed','triggered'))      as open,
  count(*)                                                        as total,
  round(avg(outcome_r) filter (where outcome_r is not null), 2)   as avg_r
from public.setups
where published = true;
```

Properties that make it trustworthy:

- **Only `published = true` rows count.** Unpublished (shadow-mode) setups are
  invisible to users — enforced by RLS policy `setups_read`
  (`db/002_security_fixes.sql`), which lets non-staff read only published rows.
  The engine therefore cannot "hide its losers" by simply not publishing them
  *after the fact*: publication is a gate applied before the outcome is known,
  and the view is a live aggregate.
- **`avg_r` is over rows with a non-null `outcome_r`** — i.e. closed trades only;
  open proposals do not dilute it.
- **`wins` counts partial and full targets alike** (tp1/tp2/tp3), so a `tp1_hit`
  that later stopped is counted as a win in this aggregate even though its final
  `status`/`outcome_r` reflect the later stop. This is a definitional subtlety
  and a known limitation ([§9](#9-known-limitations), [§11](#11-implementation-gaps)).
- **The API exposes the view read-only** (`GET /api/track-record`), with the view
  `REVOKE`d from direct writes and granted only `SELECT`.

---

## 9. Known limitations

Stated plainly. A skeptical reader should assume each is real until disproven.

1. **ATR is simple-mean, not Wilder-recursive.** Close to Wilder's ATR but not
   identical; documented in [§2.2](#22-smoothing-choice-and-honest-disclosure).
2. **No freshness decay, no reaction magnitude, no session weighting in zone
   strength.** The strength formula is a function of touches and tightness only.
3. **Broken zones are not detected.** A zone price has closed through is still
   reported until its pivots leave the working window.
4. **Fibonacci confluence is specified but not implemented.** The "four-input
   confluence" claim currently rests on two numeric inputs (structure + zone)
   plus two reported-but-unweighted inputs (liquidity, session).
5. **Liquidity and session do not enter the confidence number.** They are shown
   to the user as context, not scored.
6. **Confidence is ordinal, not calibrated.** There is no evidence that conf
   0.70 wins more often than 0.60. Until a calibration study exists, it is a
   ranking device only.
7. **OHLC path ambiguity.** Stop-first resolution is conservative but cannot
   know true intrabar order; a bar that hit both stop and tp3 is scored $-1R$.
   This understates some real outcomes — deliberately.
8. **Tick volume is not real volume.** Gold spot volume is decentralised; the
   engine does not use `v` in any signal, so it cannot detect genuine
   volume-confirmed levels.
9. **The data source is a third party and caps history (~101 bars/timeframe).**
   Samples are small; the backtester flags this. Results are sensitive to the
   feed's bar construction.
10. **Session boundaries are fixed UTC hours, not DST-aware market sessions.**
    "London" is 07:00–12:00 UTC year-round; the true London open shifts with
    DST. Session labels are approximations.
11. **The evaluator's bar-eligibility uses `created_at` from the store clock**,
    and session-extreme detection uses the system clock; clock skew or a store
    clock offset can misclassify a bar.
12. **One position at a time in the backtest, step 4.** Overlapping setups are
    dropped, so the backtest is a lower bound on trade count, not a portfolio
    simulation. No slippage, spread, commission, or swap is modelled — the
    engine's $-1R$ stop-out is optimistic relative to a real fill with spread.
13. **`wins` in `track_record` conflates partial and full.** A setup that hit
    tp1 then stopped counts in both `wins` and, via its final status, is not in
    `losses`; the aggregate can overstate the win rate relative to final R.
14. **No multi-timeframe confluence.** The agent picks one timeframe's best
    setup; it does not require a 4h and 1h view to agree.
15. **Small-sample overfitting risk in the parameters** ($k=2$, weights, 0.35/0.5
    ATR constants). These are reasoned defaults, not optimised values; they have
    not been walk-forward validated on a long-history feed.

---

## 10. Reproducibility checklist

To reproduce any published level or setup, a third party needs:

1. The exact candle series (BiQuote MT5 aggregate for `XAUUSD`, the stated
   timeframe, the stated count).
2. The parameters in [§12](#12-parameter-table).
3. This document's formulas, applied oldest-first after `_clean`.
4. The setup's `idempotency_key` to identify the exact bar it was formed on.

Given (1)–(4), the entry, stop, targets and zone bounds are deterministic. The
engine exposes `analyse()` which returns the full payload (price, ATR, bias,
session, zones, liquidity, setup, candles) as JSON for direct inspection.

---

## 11. Implementation gaps

This section lists places where **this document is stronger than the shipped
code**. It is the contract for future work; nothing here is claimed as done.

| # | Documented (§) | Shipped code | Gap |
|---|---|---|---|
| G1 | Wilder **recursive** ATR (§2.2) | simple mean of last 14 TRs | smoothing differs |
| G2 | Freshness decay $S\cdot e^{-\Delta/\lambda}$ (§3.5) | `last_touch` stored, unused in strength | not implemented |
| G3 | Reaction-magnitude factor (§3.6) | absent | not implemented |
| G4 | Session context in zone strength (§3.6) | session computed, not applied to zones | not implemented |
| G5 | Broken-zone detection + role reversal (§3.8) | absent | not implemented |
| G6 | Fibonacci confluence (§5.2) | absent | not implemented |
| G7 | Liquidity + session as numeric confidence inputs (§5.2) | reported as factors only | not implemented |
| G8 | Calibrated confidence (§9.6) | ordinal heuristic | not calibrated |
| G9 | Zone-anchored tp2/tp3 (§6.4) | fixed 2R/3R | not implemented |
| G10 | Breakeven/trailing management (§7.4) | no BE/trail transition | not implemented |
| G11 | DST-aware sessions (§9.10) | fixed UTC windows | approximation |
| G12 | Cost model (spread/commission/slippage) in backtest (§9.12) | absent | not implemented |
| G13 | `wins` = final positive R (§8.3) | `wins` counts any tp hit | definitional gap |
| G14 | ISO date parsing robustness (§4.2) | string-prefix match on `openTime` | fragile |
| G15 | Multi-timeframe agreement (§9.14) | single best timeframe | not implemented |

Each gap is a candidate for a versioned engine change; none should be silently
folded into the method description until the code changes and its tests pass.

---

## 12. Parameter table

| Parameter | Symbol | Value | Where | Source of the value |
|---|---|---|---|---|
| ATR period | $p$ | 14 | `analysis.atr` | Wilder (1978) default |
| Pivot lookback | $k$ | 2 | `swing_points` | engine default (tunable) |
| Zone tolerance | $\theta$ | $\max(0.35\cdot\text{ATR},\,0.40)$ | `find_zones` | reasoned, volatility-scaled |
| Liquidity tolerance | $\lambda$ | $\max(0.25\cdot\text{ATR},\,0.30)$ | `find_liquidity` | reasoned |
| Equal-high/low window | — | ≤ 11 bars ahead | `find_liquidity` | reasoned (time locality) |
| Zone relevance band | — | $\max(12\cdot\text{ATR},\,1\%\,C_0)$ | `relevant` | reasoned |
| Zone strength weights | — | 0.35 / 0.40 / 0.25 | `cluster_zones` | reasoned |
| Stop padding | — | $0.5\cdot\text{ATR}$ | `build_setup` | reasoned (one wick) |
| Targets | — | 1R / 2R / 3R | `build_setup` | convention |
| Min R:R (engine) | — | 1.5 (on tp2) | `build_setup` | reasoned |
| Min R:R (API) | — | 1.0 | `api/app.py` | hard floor |
| Min bars | $N$ | 60 | `build_setup` | EMA50 warm-up |
| Validity window | — | 24 h (1–168) | `api/app.py` | reasoned |
| Max open setups | — | 3 | `api/app.py` | product discipline |
| Backtest warm-up | — | 60 bars | `backtest.py` | = min bars |
| Backtest lookback | — | 200 bars | `backtest.py` | window size |
| Backtest step | — | 4 bars | `backtest.py` | compute economy |
| Backtest adequacy | — | ≥ 30 closed | `backtest.py` | small-sample guard |
| Round-number grid | step | \$25 (>1000) / \$1 | `find_liquidity` | quote granularity |

---

## 13. References

1. J. Welles Wilder Jr., *New Concepts in Technical Trading Systems*, Trend
   Research, 1978 — True Range and Average True Range (ch. 2); ATR as the
   volatility unit.
2. Standard fractal/pivot ("n-bar swing") convention as used in discretionary
   technical analysis; formalised here as the symmetric rolling-window rule of
   [§3.1](#31-swing-pivot-detection).
3. BiQuote public OHLC API — MT5-aggregated XAU/USD bars (`market.py`).
4. Internal: `deliveries/astra-trading/PLAN.md`, `PLAN-V2.md`, `AI-SETUPS.md`,
   `docs/SCOPE.md` — product constraints (honesty, auditability, no execution).

*Methodology version 1.0.0 — normative text; implementation gaps are listed,
not hidden.*
