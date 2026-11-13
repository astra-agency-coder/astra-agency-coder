#!/usr/bin/env python3
"""Astra Trading — engine fuzz test.

Feeds the analysis engine and the market parsing layer hostile input and asserts
the safety-critical invariants:

  * it must never raise (no crash, no ZeroDivisionError);
  * any setup it emits must have the stop on the CORRECT side of entry,
    targets on the correct side, ordered, and a finite, sane R:R;
  * no NaN / Inf may leak into an emitted setup.

Exit code is non-zero if a SAFETY invariant is violated (a setup emitted with a
wrong-side stop or an absurd/NaN R:R). Lower-level crashes on degenerate input
are reported as robustness findings and counted separately.

Run: python3 fuzz_test.py
"""
from __future__ import annotations

import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine"
sys.path.insert(0, str(ENGINE))

import analysis as A          # noqa: E402
import market as M            # noqa: E402
from market import Candle     # noqa: E402

SAFETY: list[str] = []        # invariant violations (critical)
CRASHES: list[str] = []       # unexpected exceptions (robustness)
NOTES: list[str] = []


def c(o, h, l, cl, t="2026-11-13T00:00:00Z", v=100):  # noqa: E741
    return Candle(t=t, o=o, h=h, l=l, c=cl, v=v)


def synth(n, start=2000.0, amp=5.0, drift=0.0, nan_at=(), inf_at=(), neg=False,
          dup_ts=False):
    out = []
    for i in range(n):
        mid = start + drift * i + amp * math.sin(i / 2.0)
        if neg:
            mid = -abs(mid)
        o, h, l, cl = mid, mid + amp * 0.4, mid - amp * 0.4, mid  # noqa: E741
        if i in nan_at:
            o = h = l = cl = float("nan")  # noqa: E741
        if i in inf_at:
            o = h = l = cl = float("inf")  # noqa: E741
        ts = "2026-11-13T00:00:00Z" if dup_ts else f"2026-11-13T{(i // 60) % 24:02d}:{i % 60:02d}:00Z"
        out.append(c(o, h, l, cl, t=ts))
    return out


# --------------------------------------------------------------------------- #
# invariant checks
# --------------------------------------------------------------------------- #
def finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def check_setup(label: str, s):
    if s is None:
        return
    where = f"{label}: setup emitted"
    for f in ("entry", "stop_loss", "tp1", "tp2", "tp3", "risk_reward"):
        v = getattr(s, f, None)
        if v is not None and not finite(v):
            SAFETY.append(f"{where}: {f}={v!r} is not finite")
    if s.direction == "long":
        if not (finite(s.stop_loss) and finite(s.entry) and s.stop_loss < s.entry):
            SAFETY.append(f"{where}: LONG stop {s.stop_loss!r} not below entry {s.entry!r}")
        if not (finite(s.tp1) and finite(s.tp2) and finite(s.tp3)
                and s.entry < s.tp1 <= s.tp2 <= s.tp3):
            SAFETY.append(f"{where}: LONG targets {s.tp1}/{s.tp2}/{s.tp3} not above/ordered vs entry {s.entry}")
    elif s.direction == "short":
        if not (finite(s.stop_loss) and finite(s.entry) and s.stop_loss > s.entry):
            SAFETY.append(f"{where}: SHORT stop {s.stop_loss!r} not above entry {s.entry!r}")
        if not (finite(s.tp1) and finite(s.tp2) and finite(s.tp3)
                and s.tp1 >= s.tp2 >= s.tp3 and s.tp3 < s.entry):
            SAFETY.append(f"{where}: SHORT targets {s.tp1}/{s.tp2}/{s.tp3} not below/ordered vs entry {s.entry}")
    else:
        SAFETY.append(f"{where}: unknown direction {s.direction!r}")
    rr = s.risk_reward
    if finite(rr):
        if rr <= 0 or rr > 1000:
            SAFETY.append(f"{where}: absurd R:R {rr!r}")
        if rr < 1.5 - 1e-9:
            SAFETY.append(f"{where}: R:R {rr!r} below the 1.5 floor build_setup promises")
    else:
        SAFETY.append(f"{where}: R:R {rr!r} is not finite")
    if not (finite(s.confidence) and 0 <= s.confidence <= 1):
        SAFETY.append(f"{where}: confidence {s.confidence!r} out of [0,1]")


def try_call(label: str, fn, *a, **k):
    """Call fn, record crashes; return (ok, value)."""
    try:
        return True, fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        CRASHES.append(f"{label}: {type(e).__name__}: {e}")
        return False, None


# --------------------------------------------------------------------------- #
# hostile case set
# --------------------------------------------------------------------------- #
CASES: list[tuple[str, list]] = [
    ("empty", []),
    ("single", [c(2000, 2001, 1999, 2000)]),
    ("two", [c(2000, 2001, 1999, 2000), c(2001, 2002, 2000, 2001)]),
    ("nan-prices", synth(80, nan_at=(3, 20, 55))),
    ("inf-prices", synth(80, inf_at=(10, 40))),
    ("all-nan", [c(float("nan"), float("nan"), float("nan"), float("nan")) for _ in range(80)]),
    ("all-inf", [c(float("inf"), float("inf"), float("inf"), float("inf")) for _ in range(80)]),
    ("dup-timestamps", synth(80, dup_ts=True)),
    ("zero-prices", [c(0, 0, 0, 0) for _ in range(80)]),
    ("huge-prices", synth(80, start=1e9, amp=1e6)),
    ("negative-prices", synth(80, neg=True)),
    ("flat", [c(2000, 2000, 2000, 2000) for _ in range(80)]),
    ("inverted-highlow", [c(2000, 1990, 2010, 2000) for _ in range(80)]),
    ("monotonic-up", [c(1000 + i, 1001 + i, 999 + i, 1000 + i) for i in range(80)]),
    ("monotonic-down", [c(3000 - i, 3001 - i, 2999 - i, 3000 - i) for i in range(80)]),
    ("huge-count", synth(20000, drift=0.05)),
    ("mixed-nan-inf", synth(120, nan_at=(1, 2, 3, 60), inf_at=(30, 31, 90))),
]


def run_case(label: str, candles):
    """Run the whole pipeline over one hostile candle set."""
    atr_ok, a = try_call(f"{label}:atr", A.atr, candles)
    try_call(f"{label}:ema", A.ema, [x.c for x in candles], 21)
    try_call(f"{label}:sma", A.sma, [x.c for x in candles], 50)
    try_call(f"{label}:swing_points", A.swing_points, candles)
    try_call(f"{label}:cluster_zones", A.cluster_zones, [(i, 2000.0 + i, "t") for i in range(5)], "support", 1.0)
    try_call(f"{label}:bias", A.bias, candles)
    try_call(f"{label}:find_zones", A.find_zones, candles, None)
    try_call(f"{label}:find_liquidity", A.find_liquidity, candles, 1.0 if not atr_ok else a)
    try_call(f"{label}:session_context", A.session_context, datetime.now(timezone.utc))
    ok, s = try_call(f"{label}:build_setup", A.build_setup, candles, "1h")
    if ok:
        check_setup(label, s)
    # analyse() end-to-end with a stubbed market fetch (offline)
    orig = M.fetch_candles
    M.fetch_candles = lambda *a, **k: candles
    try:
        try_call(f"{label}:analyse", A.analyse, "XAUUSD", "1h", 300)
    finally:
        M.fetch_candles = orig


def run_random_fuzz(seed=20261113, n=2000):
    rng = random.Random(seed)
    for i in range(n):
        length = rng.choice([0, 1, 2, 5, 59, 60, 61, 200])
        candles = []
        base = rng.choice([0.0, 1.0, 2000.0, 1e9, -50.0])
        for j in range(length):
            o = base + rng.uniform(-10, 10)
            h = o + rng.uniform(-5, 5)
            l = o - rng.uniform(-5, 5)  # noqa: E741  (may invert on purpose)
            cl = o + rng.uniform(-5, 5)
            # randomly inject NaN / Inf
            if rng.random() < 0.03:
                o = h = l = cl = float("nan")  # noqa: E741
            if rng.random() < 0.03:
                o = h = l = cl = float("inf")  # noqa: E741
            candles.append(c(o, h, l, cl, t=f"2026-11-13T{j % 24:02d}:{j % 60:02d}:00Z"))
        ok, s = try_call(f"fuzz[{i}]", A.build_setup, candles, rng.choice(["5m", "1h", "4h"]))
        if ok:
            check_setup(f"fuzz[{i}]", s)


def run_market_parse_fuzz():
    """market._parse must tolerate hostile payloads without crashing."""
    payloads = [
        ("bars-missing", {}),
        ("bars-none", {"bars": None}),
        ("bars-not-list", {"bars": {"a": 1}}),
        ("bars-strings", {"bars": [{"open": "x", "high": "y", "low": "z", "close": "w"}]}),
        ("bars-missing-keys", {"bars": [{"high": 1}]}),
        ("bars-nan-str", {"bars": [{"open": "nan", "high": "nan", "low": "nan", "close": "nan"}]}),
        ("bars-inf-str", {"bars": [{"open": "inf", "high": "inf", "low": "inf", "close": "inf"}]}),
        ("bars-empty-dict", {"bars": [{}]}),
        ("payload-is-list", [{"open": 1}]),
        ("payload-is-none", None),
        ("payload-is-str", "nope"),
    ]
    for label, p in payloads:
        ok, out = try_call(f"market._parse[{label}]", M._parse, p)
        if ok and out is not None and len(out) > 0:
            NOTES.append(f"market._parse[{label}] accepted {len(out)} bars (tolerated)")


# --------------------------------------------------------------------------- #
def main() -> int:
    print("== hostile fixed cases ==")
    for label, candles in CASES:
        run_case(label, candles)
    print(f"  {len(CASES)} cases run")

    print("== random fuzz (2000 iterations, seeded) ==")
    run_random_fuzz()
    print("  done")

    print("== market._parse hostile payloads ==")
    run_market_parse_fuzz()

    # de-dup
    def uniq(xs):
        seen, out = set(), []
        for x in xs:
            k = x.split(":", 1)[-1][:120]
            if k in seen:
                continue
            seen.add(k)
            out.append(x)
        return out

    safety = uniq(SAFETY)
    crashes = uniq(CRASHES)
    print("\n== results ==")
    print(f"  SAFETY violations (wrong-side stop / absurd R:R / NaN leak): {len(safety)}")
    for x in safety[:40]:
        print(f"    SAFETY  {x}")
    print(f"  unexpected crashes (robustness): {len(crashes)}")
    for x in crashes[:40]:
        print(f"    CRASH   {x}")
    for n in NOTES:
        print(f"    note    {n}")

    print(f"\nRESULT safety_violations={len(safety)} crashes={len(crashes)}")
    return 1 if safety else 0


if __name__ == "__main__":
    raise SystemExit(main())
