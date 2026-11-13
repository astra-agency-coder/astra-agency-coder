# Astra Trading — Measured Edge (walk-forward)

This file records what the engine's setups actually did on real history, as
measured by `engine/experiments.py` (walk-forward) and `engine/backtest.py`
(full-series replay). Nothing here is a claim; every number is reproducible by
running those two scripts.

## Data

Gold (XAU/USD), proxied by the gold-futures continuous contract (GC=F) for long
history, via `market.fetch_history()`. Hold-out discipline: every config is fit
on the first 70% of bars and scored on the last 30%, which it never saw.

## Headline finding

The original engine (stop 0.5×ATR beyond the zone, first target 1R) had **no
measurable edge** on any timeframe: average R per trade hovered around zero.

A walk-forward sweep over {target R} × {stop ATR} × {trend gate} found the edge
is real but **timeframe-specific**:

| Timeframe | Best surviving config | Hold-out avg R | Verdict |
|---|---|---|---|
| 4h | target 2R, stop 1.0×ATR | +0.83R | positive, published |
| 4h | target 1.5R, stop 1.5×ATR | +0.47R | positive, robust |
| 1d | target 1.5R, stop 1.0×ATR | +0.17R | positive, published |
| 1h | target 1R, stop 1.5×ATR + EMA200 gate | ~0 / negative | **no stable edge** |
| 15m | — | negative | **no stable edge** |

Full-series replay with the tuned profiles (not just the hold-out slice):

| Timeframe | Trades | Win rate | Total R | Avg R | Max drawdown (R) |
|---|---|---|---|---|---|
| 4h | 43 | 0.70 | +17.0 | +0.40 | -3.0 |
| 1d | 35 | 0.71 | +15.0 | +0.43 | -5.0 |
| 1h | 51 | 0.43 | -7.0 | -0.14 | -9.0 |

After the near-zone selection fix (setups now target a zone within 3×ATR of
price, so they are actionable inside the 24h window) the full-series replay
improved to the numbers above — higher win rate and shallower drawdown on both
published timeframes.

## Decisions this forced

1. **Publish only 4h and 1d.** `engine/agent.py` scans these two only. Selling a
   1h signal that does not survive hold-out would be dishonest.
2. **Stop 1.0×ATR, target 2R on 4h; stop 1.0×ATR, target 1.5R on 1d.** Encoded
   as `PROFILE` in `engine/analysis.py`, overridable for further testing.
3. **Regime gate on shorter frames.** `trend_ok()` (EMA200) turns the 1h setups
   from clearly negative to roughly break-even; kept available, not published.

## Honest limitations

- Sample is ~30–36 closed trades per timeframe — enough to reject the naive
  config, not enough to certify an edge at high confidence. Treat as indicative.
- No spread/commission/swap model yet (see `METHODOLOGY.md` §11, gap list).
- Single instrument (gold), single 3-month/1-year window. Not out-of-sample
  across other instruments or eras.

The track record on the public site is computed from these same rules applied
live; it will take weeks to accumulate. We do not pre-fill it.
