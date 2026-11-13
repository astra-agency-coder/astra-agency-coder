"use client";

import { useEffect, useState } from "react";

type Tick = { bid: number; ask: number; mid: number; spread: number; source: string };

/**
 * Renders the captured tick and, if the API is reachable, refreshes it.
 * The initial paint always uses the snapshot, so the component never shows
 * empty state on a static export.
 */
export default function LiveTick({
  initial,
  labels,
}: {
  initial: Tick;
  labels: { bid: string; ask: string; spread: string; source: string };
}) {
  const [tick, setTick] = useState<Tick>(initial);
  const [prev, setPrev] = useState<number>(initial.mid);
  const [fetched, setFetched] = useState(false);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const r = await fetch("/api/tick", { cache: "no-store" });
        if (!r.ok) return;
        const j = (await r.json()) as Tick;
        if (!alive || typeof j.mid !== "number") return;
        setPrev((p) => (tick.mid !== j.mid ? tick.mid : p));
        setTick(j);
        setFetched(true);
      } catch {
        /* keep the snapshot */
      }
    };
    poll();
    const id = setInterval(poll, 20000);
    return () => {
      alive = false;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const up = tick.mid >= prev;
  const cls = up ? "tick-up" : "tick-down";
  const arrow = up ? "▲" : "▼";

  return (
    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-4">
      <Cell label={labels.bid} value={tick.bid.toFixed(2)} cls={cls} arrow={arrow} />
      <Cell label={labels.ask} value={tick.ask.toFixed(2)} />
      <Cell label={labels.spread} value={tick.spread.toFixed(3)} />
      <Cell
        label={labels.source}
        value={tick.source}
        sub={fetched ? "live" : "snapshot"}
        small
      />
    </div>
  );
}

function Cell({
  label,
  value,
  cls,
  arrow,
  sub,
  small,
}: {
  label: string;
  value: string;
  cls?: string;
  arrow?: string;
  sub?: string;
  small?: boolean;
}) {
  return (
    <div className="bg-ink-3/80 px-4 py-3">
      <div className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{label}</div>
      <div className={`mono mt-1 ${small ? "text-[0.8rem]" : "text-lg"} ${cls ?? "text-snow"}`}>
        {arrow && <span className="me-1 text-[0.7em]">{arrow}</span>}
        {value}
      </div>
      {sub && <div className="mono mt-0.5 text-[0.6rem] text-fog-dim">{sub}</div>}
    </div>
  );
}
