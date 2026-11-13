type Setup = {
  symbol: string;
  direction: string;
  entry: number;
  stop_loss: number;
  tp1: number;
  tp2: number;
  tp3: number;
  risk_reward: number;
  confidence: number;
  factors: string[];
  invalidation: string;
  session: string;
};

export default function SetupCard({
  setup,
  labels,
}: {
  setup: Setup | null;
  labels: {
    setup: string;
    entry: string;
    stop: string;
    targets: string;
    rr: string;
    confidence: string;
    factors: string;
    invalidation: string;
    session: string;
  };
}) {
  if (!setup) {
    return (
      <div className="panel panel--lift sheen p-6">
        <div className="mono text-[0.66rem] tracking-[0.2em] text-fog-dim uppercase">{labels.setup}</div>
        <p className="mt-3 text-sm text-fog">—</p>
      </div>
    );
  }

  const short = setup.direction === "short";
  const tone = short ? "text-bear" : "text-bull";
  const conf = Math.round(setup.confidence * 100);

  return (
    <div className="panel panel--lift sheen p-6">
      <div className="flex items-center justify-between gap-4">
        <div className="mono text-[0.66rem] tracking-[0.2em] text-fog-dim uppercase">{labels.setup}</div>
        <span className={`tag ${short ? "" : "tag--bull"}`}>
          <span className={tone}>{setup.direction.toUpperCase()}</span>
          <span className="text-fog-dim">·</span>
          <span className="text-fog">{setup.symbol}</span>
        </span>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        <Stat label={labels.entry} value={setup.entry.toFixed(2)} />
        <Stat label={labels.stop} value={setup.stop_loss.toFixed(2)} tone="text-bear" />
        <Stat label={labels.rr} value={`${setup.risk_reward.toFixed(1)}:1`} tone="text-gold-bright" />
      </div>

      <div className="mt-4">
        <div className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{labels.targets}</div>
        <div className="mono mt-2 flex flex-wrap gap-2 text-sm">
          <span className="tag tag--bull">{setup.tp1.toFixed(2)}</span>
          <span className="tag tag--bull">{setup.tp2.toFixed(2)}</span>
          <span className="tag tag--bull">{setup.tp3.toFixed(2)}</span>
        </div>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between">
          <span className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">
            {labels.confidence}
          </span>
          <span className="mono text-xs text-gold-bright">{conf}%</span>
        </div>
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-line">
          <div
            className="h-full rounded-full bg-gradient-to-r from-gold to-gold-bright"
            style={{ width: `${conf}%` }}
          />
        </div>
      </div>

      <div className="hairline mt-5 pt-4">
        <div className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{labels.factors}</div>
        <ul className="mt-2 space-y-1.5">
          {setup.factors.slice(0, 5).map((f) => (
            <li key={f} className="flex gap-2 text-[0.82rem] leading-relaxed text-fog">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-gold" aria-hidden="true" />
              {f}
            </li>
          ))}
        </ul>
      </div>

      <div className="hairline mt-4 flex items-center justify-between pt-3 text-[0.75rem]">
        <span className="text-fog-dim">
          {labels.invalidation}: <span className="mono text-fog">{setup.invalidation}</span>
        </span>
        <span className="mono text-fog-dim">{setup.session}</span>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-ink-2/60 px-3 py-2.5">
      <div className="mono text-[0.58rem] tracking-[0.16em] text-fog-dim uppercase">{label}</div>
      <div className={`mono mt-1 text-base ${tone ?? "text-snow"}`}>{value}</div>
    </div>
  );
}
