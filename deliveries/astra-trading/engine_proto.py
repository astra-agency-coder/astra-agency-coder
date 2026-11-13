#!/usr/bin/env python3
"""Astra Trading — analysis prototype on REAL gold data (XAUUSD / COMEX GC=F).

Honest scope: this is a *technical analysis engine*, not a signal service.
It computes structure (support/resistance), liquidity levels, session ranges,
volatility (ATR) and a plain-language bias. No profit promises, no advice.

Run:  python3 engine_proto.py [--interval 1h] [--range 1mo]
Out:  astra-trading-chart.png  + a printed analysis summary
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
SYMBOL = "GC=F"  # COMEX gold front-month — the price XAUUSD spot tracks


def fetch(symbol: str, interval: str, rng: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={rng}&interval={interval}"
    req = urllib.request.Request(url, headers=UA)
    res = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    ts, o, h, l, c = res["timestamp"], q["open"], q["high"], q["low"], q["close"]
    rows = [(t, oo, hh, ll, cc) for t, oo, hh, ll, cc in zip(ts, o, h, l, c)
            if None not in (oo, hh, ll, cc)]
    return {"meta": res["meta"], "rows": rows}


def atr(rows, period=14) -> float:
    trs = []
    for i in range(1, len(rows)):
        _, _, h, l, _ = rows[i]
        pc = rows[i - 1][4]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return float(np.mean(trs[-period:])) if trs else 0.0


def swing_points(rows, left=3, right=3):
    highs, lows = [], []
    for i in range(left, len(rows) - right):
        _, _, h, l, _ = rows[i]
        win = rows[i - left:i + right + 1]
        if h == max(w[2] for w in win):
            highs.append((rows[i][0], h))
        if l == min(w[3] for w in win):
            lows.append((rows[i][0], l))
    return highs, lows


def cluster(levels, tol):
    """Group nearby price levels into zones; return (mid, touches)."""
    zones = []
    for ts, price in sorted(levels, key=lambda x: x[1]):
        for z in zones:
            if abs(price - z["mid"]) <= tol:
                z["pts"].append(price)
                z["mid"] = float(np.mean(z["pts"]))
                z["touches"] += 1
                break
        else:
            zones.append({"mid": price, "pts": [price], "touches": 1, "first_ts": ts})
    return sorted(zones, key=lambda z: -z["touches"])


def session_of(ts: int) -> str:
    hr = datetime.fromtimestamp(ts, tz=timezone.utc).hour
    if 0 <= hr < 7:
        return "Asia"
    if 7 <= hr < 12:
        return "London"
    if 12 <= hr < 21:
        return "New York"
    return "Late"


def analyse(rows):
    last = rows[-1][4]
    a = atr(rows)
    highs, lows = swing_points(rows)
    tol = max(a * 0.6, last * 0.0015)
    res = [z for z in cluster(highs, tol) if z["mid"] > last]
    sup = [z for z in cluster(lows, tol) if z["mid"] < last]
    sess = {}
    for t, o, h, l, c in rows:
        d = sess.setdefault(session_of(t), {"hi": h, "lo": l})
        d["hi"], d["lo"] = max(d["hi"], h), min(d["lo"], l)
    closes = np.array([r[4] for r in rows])
    sma = float(np.mean(closes[-50:])) if len(closes) >= 50 else float(np.mean(closes))
    slope = float(np.polyfit(range(min(50, len(closes))), closes[-50:], 1)[0])
    bias = "bullish" if last > sma and slope > 0 else "bearish" if last < sma and slope < 0 else "ranging"
    return {
        "last": last, "atr": a, "sma50": sma, "bias": bias, "slope": slope,
        "resistance": res[:3], "support": sup[:3], "sessions": sess,
        "high_52": max(r[2] for r in rows), "low_52": min(r[3] for r in rows),
    }


def draw(rows, info, out="astra-trading-chart.png"):
    n = len(rows)
    x = np.arange(n)
    o = np.array([r[1] for r in rows]); h = np.array([r[2] for r in rows])
    l = np.array([r[3] for r in rows]); c = np.array([r[4] for r in rows])

    fig, ax = plt.subplots(figsize=(15, 8), facecolor="#0B0A12")
    ax.set_facecolor("#0B0A12")
    up, dn = "#7FE7DC", "#F08A9B"
    for i in range(n):
        col = up if c[i] >= o[i] else dn
        ax.vlines(x[i], l[i], h[i], color=col, linewidth=0.7, alpha=.85)
        ax.vlines(x[i], min(o[i], c[i]), max(o[i], c[i]), color=col, linewidth=3.2, alpha=.95)

    for z in info["resistance"]:
        ax.axhspan(z["mid"] - info["atr"] * .18, z["mid"] + info["atr"] * .18, color="#F08A9B", alpha=.16, zorder=0)
        ax.axhline(z["mid"], color="#F08A9B", lw=.9, ls="--", alpha=.8)
        ax.text(n * .995, z["mid"], f"  R {z['mid']:.1f} ({z['touches']}x)", color="#F08A9B", fontsize=9, va="center", ha="left")
    for z in info["support"]:
        ax.axhspan(z["mid"] - info["atr"] * .18, z["mid"] + info["atr"] * .18, color="#7FE7DC", alpha=.16, zorder=0)
        ax.axhline(z["mid"], color="#7FE7DC", lw=.9, ls="--", alpha=.8)
        ax.text(n * .995, z["mid"], f"  S {z['mid']:.1f} ({z['touches']}x)", color="#7FE7DC", fontsize=9, va="center", ha="left")

    ax.axhline(info["last"], color="#F5D488", lw=1.4, alpha=.95)
    ax.text(n * .995, info["last"], f"  {info['last']:.1f}", color="#F5D488", fontsize=11, fontweight="bold", va="bottom", ha="left")

    step = max(1, n // 10)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([datetime.fromtimestamp(rows[i][0], tz=timezone.utc).strftime("%b %d %H:%M") for i in range(0, n, step)], color="#A29DAF", fontsize=8)
    ax.tick_params(colors="#A29DAF", labelsize=8)
    for s in ax.spines.values():
        s.set_color("#2a2733")
    ax.set_xlim(-2, n + n * .12)
    ax.set_title(f"Astra Trading — {SYMBOL} structure analysis   |   bias: {info['bias'].upper()}   |   ATR {info['atr']:.2f}", color="#EDE9F3", fontsize=13, pad=14, loc="left")
    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor="#0B0A12")
    print(f"chart -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", default="1h")
    ap.add_argument("--range", default="1mo")
    a = ap.parse_args()
    rows = fetch(SYMBOL, a.interval, a.range)["rows"]
    info = analyse(rows)
    print(f"\nAstra Trading prototype — {SYMBOL} @ {a.interval}/{a.range}")
    print(f"  bars            : {len(rows)}")
    print(f"  last price      : {info['last']:.2f}")
    print(f"  ATR(14)         : {info['atr']:.2f}")
    print(f"  SMA50           : {info['sma50']:.2f}")
    print(f"  structure bias  : {info['bias']}")
    print(f"  range           : {info['low_52']:.1f} .. {info['high_52']:.1f}")
    print("  resistance      :", ", ".join(f"{z['mid']:.1f}({z['touches']}x)" for z in info["resistance"]) or "-")
    print("  support         :", ", ".join(f"{z['mid']:.1f}({z['touches']}x)" for z in info["support"]) or "-")
    print("  session ranges  :")
    for s, d in info["sessions"].items():
        print(f"     {s:10} {d['lo']:.1f} .. {d['hi']:.1f}  ({d['hi']-d['lo']:.1f} wide)")
    print("\n  NOTE: technical structure only — not investment advice.\n")
    draw(rows, info)


if __name__ == "__main__":
    main()
