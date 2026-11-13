# Critique — Astra Trading mark (`logo-mark.svg`)

Measured by rasterising the current file at 512 px and by reading the path
coordinates directly. Numbers below are in the SVG's own 512-unit space and were
**verified** (perpendicular widths, angles and baselines computed, not eyeballed).

Benchmarked against **Stripe** (one mathematically-derived geometry), **Linear**
(one idea, perfectly reduced, flawless optical balance) and **Revolut** (bold,
weight-matched, crisp at any size).

First, what is **already right** (to be fair): the two legs *are* weight-matched —
the diagonal's **perpendicular** width is **91.99 u** and the bar is **92 u**. The
roof chamfer *is* perpendicular to the leg axis (28.3° vs the leg's 118.2°). So the
concept is sound; the faults are in the junctions, centring and one proportion.

Verified problems:

1. **Crossbar is not weight-matched.** The crossbar is **42 u** tall (y 296→338)
   against a **92 u** stroke — **2.19×** thinner. It reads as a wafer, not the
   "gauge tick" of comparable weight the concept promises.
2. **Crossbar overshoots asymmetrically.** It runs out to x = **492** while the
   bar's right edge is **438** — a **54 u** arm (**59 %** of the stroke) on the
   right, with no counterpart on the left. The "tick" is lopsided.
3. **The mark is off-centre.** Ink bbox is x **55→491**, y **50→474** → centre
   **(273, 262)** inside a 256-centred box. Side margins are **L 55 / R 20** (Δ35)
   and **T 50 / B 38** (Δ12): it sits low and right.
4. **No clear space is defined.** Ink reaches x = **491**, i.e. **21 u** from the
   right edge — the bar is effectively flush right. `BRAND.md` §6 promises a
   0.5 × height clear space; the file has none.
5. **Two different baselines.** The leg's lowest point is y = **473.8** but the
   bar's is y = **452** — a **21.8 u** mismatch. The letter does not sit on a line.
6. **Skewed foot.** The foot cut (55.5, 430.2)→(136.5, 473.8) is **not
   perpendicular** to the leg axis (axis · foot = **−44**, should be 0), so the
   terminal is a parallelogram, not a clean square-cut foot.
7. **Bar-top nub above the roof.** The bar's top-left corner is at y = **66**, but
   the roof line only reaches y ≈ **96.8** at x = 346 — the bar pokes **30.8 u**
   above the roof, a stray nub.
8. **Roof is narrower than the stroke.** The roof chamfer spans **81 u**
   horizontally (x 259.5→340.5) against a 92 u stroke, and stops **5.5 u** short of
   the bar (x 346), so the apex is under-sized and detached from the bar.
9. **Right silhouette is defined by the thin tick.** The rightmost extent (x 492)
   is the **crossbar**, not the bullion bar (438) — the visual weight on the right
   is carried by the weakest element.
10. **Un-snapped junction.** The leg/crossbar junction is **(231.95, 296)** in an
    otherwise integer grid — grid drift that makes the geometry non-provable.
11. **Accidental aspect ratio.** The ink box is **436.5 × 423.6** (wider than tall
    by 13 u) — an accident, not a chosen proportion.
12. **Cap with no geometric module.** The two-tone cap is 92 × **54** u; the 54 has
    no relation to the 42 crossbar or the 92 stroke, and at 16 px it collapses to
    ~1.7 px, muddying the silhouette (the mono file drops it entirely).

**Summary:** the concept and the leg weights are fine, but the crossbar
proportion, the centring, the two baselines, the skewed foot and the bar nub mean
the mark would not hold up next to Stripe/Linear/Revolut. Fix those, keep the
"Ingot A".
