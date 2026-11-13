# Critique — Astra Trading mark (`logo-mark.svg`)

Measured by rasterising the current file at 512 px and by reading the path
coordinates directly. Numbers below are in the SVG's own 512-unit space.

Benchmarked against **Stripe** (single, mathematically-derived geometry),
**Linear** (one idea, perfectly reduced, flawless optical balance) and
**Revolut** (bold, weight-matched, crisp at any size).

1. **Unequal leg weights.** The vertical bar is **92 u** wide (x 346→438) but the
   left diagonal measures **105 u** horizontally. A ~13 u / 12 % mismatch — the
   two legs read as different weights, which the eye catches instantly.
2. **Crossbar is not weight-matched.** The crossbar is **42 u** tall (y 296→338)
   against the bar's **92 u** width — 2.2× thinner. It reads as a wafer, not the
   "gauge tick" of equal weight the concept claims.
3. **The bar is broken, not solid.** The crossbar cuts a 42 u gap through the
   vertical bar (bar spans y 66→296 and 338→452). `BRAND.md` §1 calls the right
   leg "a solid vertical bar … a gold bullion"; here it is two stacked blocks.
4. **One-sided, oversized tick.** The crossbar runs out to x = **492** while the
   bar's right edge is **438** — a **54 u** arm (~59 % of the bar width) sticking
   out to the right, with no counterpart on the left (there it merges into the
   leg). The "tick" is asymmetric and top-heavy.
5. **Optical centring is wrong.** Ink bbox is x **55.5→491** (centre 273) and
   y **50.2→473.8** (centre 262) inside a box centred at 256 → the mark sits
   down-and-right. Side margins are **L 55 / R 20** (Δ35) and **T 50 / B 38** (Δ12).
6. **No clear space defined in-file.** Ink reaches x = 491, i.e. **21 u** from the
   right edge; the bar is effectively flush right. There is no 0.5×height
   clear-space box as §6 of `BRAND.md` promises.
7. **Un-snapped, arbitrary junction.** The leg/crossbar junction is at
   **(231.95, 296)** in an otherwise integer grid, and the leg's inner edge
   (340.5→346) nearly coincides with the bar's left edge (346) over y 93.8→296,
   leaving a ~5 u sliver instead of a clean corner.
8. **Inconsistent apex.** The roof (259.5, 50.2)→(340.5, 93.8) sits at **28.3°**
   from horizontal while the main diagonal is **61.8°** from horizontal — the two
   top edges differ by ~90° with mismatched slopes. Worse, the bar's top-left
   corner (346, 66) lies *above* the roof line (y ≈ 96.8 at x = 346), leaving a
   small stray nub at the top.
9. **Skewed foot.** The foot cut (55.5, 430.2)→(136.5, 473.8) is **not
   perpendicular** to the leg axis, so the terminal is a parallelogram rather
   than a clean square-cut foot.
10. **No shared baseline.** The leg's lowest point is y = **473.8** but the bar's
    is y = **452** — a **21.8 u** mismatch. The letter does not sit on a line and
    looks tilted/floaty.
11. **Accidental aspect ratio.** The ink box is **436.5 × 423.6** (wider than tall
    by ~13 u). For a balanced letterform that reads as an accident, not a choice.
12. **Decorative cap with no geometric logic.** The two-tone cap
    (346, 66)→(438, 120) is a 92 × 54 block on the bar top unrelated to the
    stroke weight; at 16 px it collapses to a ~1.7 px dot that muddies the
    silhouette.

**Summary:** the concept is sound, but the execution is not weight-matched, not
centred, not snapped to a grid, and the "solid bullion" is visually broken. It
would not survive next to Stripe/Linear/Revolut, which are all built from one
provable geometry with a single stroke weight.
