"use client";

import { useMemo, useState } from "react";

type Candle = { t: string; o: number; h: number; l: number; c: number; v: number };

const W = 1000;
const H = 380;
const VH = 64; // volume strip height, drawn beneath the candles
const PAD = { t: 18, r: 16, b: 26, l: 16 };

/**
 * Renders the real captured candle series. No smoothing, no invented points:
 * every rect and line is a value from the engine's own output.
 */
export default function CandleChart({
  series,
  zones,
  liquidity,
  label,
}: {
  series: Record<string, Candle[]>;
  zones: number;
  liquidity: number;
  label: string;
}) {
  const [tf, setTf] = useState<"1h" | "4h" | "1d">("1h");
  const candles = useMemo(() => [...(series[tf] ?? [])].reverse(), [series, tf]);

  const geo = useMemo(() => {
    if (candles.length === 0) return null;
    const hi = Math.max(...candles.map((c) => c.h));
    const lo = Math.min(...candles.map((c) => c.l));
    const span = hi - lo || 1;
    const innerW = W - PAD.l - PAD.r;
    const innerH = H - PAD.t - PAD.b - VH;
    const bw = innerW / candles.length;
    const y = (p: number) => PAD.t + ((hi - p) / span) * innerH;
    const vmax = Math.max(...candles.map((c) => c.v), 1);
    return { hi, lo, bw, y, innerW, innerH, vmax };
  }, [candles]);

  if (!geo) return null;

  const { hi, lo, bw, y, innerH, vmax } = geo;
  const gridLines = 4;
  const vTop = PAD.t + innerH + 10;

  return (
    <div className="relative">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="pulse" aria-hidden="true" />
          <span className="mono text-[0.68rem] tracking-[0.2em] text-fog-dim uppercase">{label}</span>
        </div>
        <div className="flex gap-1" role="tablist" aria-label="Timeframe">
          {(["1h", "4h", "1d"] as const).map((k) => (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={tf === k}
              onClick={() => setTf(k)}
              className={`tap mono rounded-md px-2.5 text-[0.66rem] tracking-wider transition-colors ${
                tf === k ? "bg-gold/15 text-gold-bright" : "text-fog-dim hover:text-snow"
              }`}
            >
              {k.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label={`XAUUSD ${tf} candles, ${candles.length} bars`}
        preserveAspectRatio="xMidYMid meet"
      >
        {Array.from({ length: gridLines + 1 }).map((_, i) => {
          const yy = PAD.t + (i / gridLines) * innerH;
          const price = hi - (i / gridLines) * (hi - lo);
          return (
            <g key={i}>
              <line x1={PAD.l} x2={W - PAD.r} y1={yy} y2={yy} stroke="#23232f" strokeWidth="1" />
              <text x={W - PAD.r} y={yy - 4} textAnchor="end" fill="#8a90a6" fontSize="11" fontFamily="var(--font-mono)">
                {price.toFixed(1)}
              </text>
            </g>
          );
        })}

        {candles.map((c, i) => {
          const cx = PAD.l + i * bw + bw / 2;
          const up = c.c >= c.o;
          const col = up ? "#16c79a" : "#ff4d6d";
          const bodyTop = y(Math.max(c.o, c.c));
          const bodyBot = y(Math.min(c.o, c.c));
          const bodyH = Math.max(1, bodyBot - bodyTop);
          const bwid = Math.max(1.2, bw * 0.62);
          return (
            <g key={c.t}>
              <line x1={cx} x2={cx} y1={y(c.h)} y2={y(c.l)} stroke={col} strokeWidth="1" opacity="0.85" />
              <rect
                x={cx - bwid / 2}
                y={bodyTop}
                width={bwid}
                height={bodyH}
                fill={up ? col : col}
                opacity={up ? 0.9 : 0.95}
                rx="0.5"
              />
            </g>
          );
        })}

        <line
          x1={PAD.l}
          x2={W - PAD.r}
          y1={y(candles[candles.length - 1].c)}
          y2={y(candles[candles.length - 1].c)}
          stroke="#e8c766"
          strokeWidth="1"
          strokeDasharray="4 4"
          opacity="0.75"
        />

        {candles.map((c, i) => {
          const cx = PAD.l + i * bw + bw / 2;
          const up = c.c >= c.o;
          const hgt = Math.max(1, (c.v / vmax) * (VH - 6));
          const bwid = Math.max(1.2, bw * 0.62);
          return (
            <rect
              key={`v-${c.t}`}
              x={cx - bwid / 2}
              y={vTop + (VH - 6 - hgt)}
              width={bwid}
              height={hgt}
              fill={up ? "#16c79a" : "#ff4d6d"}
              opacity="0.28"
            />
          );
        })}
      </svg>

      <div className="mono mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[0.68rem] text-fog-dim">
        <span>H {hi.toFixed(2)}</span>
        <span>L {lo.toFixed(2)}</span>
        <span className="text-fog">{zones} zones</span>
        <span className="text-fog">{liquidity} liquidity pools</span>
      </div>
    </div>
  );
}
