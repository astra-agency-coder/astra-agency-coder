import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale, LOCALES, LOCALE_LABEL, type Locale } from "@/lib/i18n";
import { getDict } from "@/lib/dictionaries";
import { company, departments, facts, marketSnapshot, workforce } from "@/lib/facts";
import Nav from "@/components/Nav";
import RevealObserver from "@/components/RevealObserver";
import ScrollProgress from "@/components/ScrollProgress";
import CandleChart from "@/components/CandleChart";
import LiveTick from "@/components/LiveTick";
import SetupCard from "@/components/SetupCard";

export function generateStaticParams() {
  return LOCALES.map((lang) => ({ lang }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}): Promise<Metadata> {
  const { lang } = await params;
  const locale: Locale = isLocale(lang) ? lang : "en";
  const t = getDict(locale);
  return { title: t.meta.title, description: t.meta.description };
}

export default async function Home({ params }: { params: Promise<{ lang: string }> }) {
  const { lang } = await params;
  if (!isLocale(lang)) notFound();
  const t = getDict(lang);

  const a1 = marketSnapshot.analysis["1h"];
  const tick = marketSnapshot.tick as unknown as {
    bid: number; ask: number; mid: number; spread: number; source: string;
  };
  const setup = a1.setup as unknown as Parameters<typeof SetupCard>[0]["setup"];
  const biasDir = (a1.bias as { direction: string }).direction;
  const captured = new Date(marketSnapshot.captured_at).toISOString().replace("T", " ").slice(0, 16);

  const heroMetrics = [
    { label: t.metrics[0].label, value: `${facts.readiness.passed}/${facts.readiness.total}`, note: t.metrics[0].note },
    { label: t.metrics[1].label, value: `${facts.repos.ok}/${facts.repos.total}`, note: t.metrics[1].note },
    { label: t.metrics[2].label, value: `${facts.engine.passed}/${facts.engine.total}`, note: t.metrics[2].note },
    { label: t.metrics[3].label, value: `${facts.roster.agents}`, note: t.metrics[3].note },
  ];

  const langs = LOCALES.map((code) => ({ code, label: LOCALE_LABEL[code] }));
  const links = [
    { href: "#platform", label: t.nav.platform },
    { href: "#method", label: t.nav.method },
    { href: "#team", label: t.nav.team },
    { href: "#work", label: t.nav.work },
    { href: "#contact", label: t.nav.contact },
  ];

  return (
    <>
      <RevealObserver />
      <ScrollProgress />
      <Nav links={links} cta={t.nav.cta} locale={lang} brand={company.name} langs={langs} />

      <main id="top">
        {/* ── HERO ─────────────────────────────────────────── */}
        <section className="relative overflow-hidden pt-36 pb-24 sm:pt-44">
          <div className="rule-grid absolute inset-0" aria-hidden="true" />
          <div className="shell relative">
            <p className="eyebrow reveal">{t.hero.badge}</p>
            <h1 className="display reveal mt-6 text-[clamp(2.6rem,8vw,6.2rem)]" style={{ ["--d" as string]: "60ms" }}>
              <span className="block text-snow">{t.hero.titleA}</span>
              <span className="gold-text block">{t.hero.titleB}</span>
            </h1>
            <p
              className="reveal mt-8 max-w-2xl text-[1.02rem] leading-relaxed text-fog sm:text-[1.12rem]"
              style={{ ["--d" as string]: "120ms" }}
            >
              {t.hero.lede}
            </p>
            <div className="reveal mt-10 flex flex-wrap items-center gap-3" style={{ ["--d" as string]: "180ms" }}>
              <a className="btn btn--gold" href="#platform">
                {t.hero.ctaPrimary}
                <span aria-hidden="true">→</span>
              </a>
              <a className="btn btn--ghost" href="#method">
                {t.hero.ctaSecondary}
              </a>
            </div>

            <div className="reveal mt-16 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line lg:grid-cols-4" style={{ ["--d" as string]: "240ms" }}>
              {heroMetrics.map((m) => (
                <div key={m.label} className="bg-ink-2/70 px-5 py-6">
                  <div className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{m.label}</div>
                  <div className="display mt-2 text-3xl text-gold-bright sm:text-4xl">{m.value}</div>
                  <div className="mt-2 text-[0.78rem] leading-snug text-fog-dim">{m.note}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── MARQUEE ──────────────────────────────────────── */}
        <div className="marquee border-y border-line py-4" aria-hidden="true">
          <div className="marquee__track mono text-[0.78rem] tracking-[0.22em] text-fog-dim uppercase">
            {Array.from({ length: 2 }).map((_, k) => (
              <span key={k} className="flex gap-12">
                {company.stack.concat(["XAUUSD", "RTL", "ar · en · tr"]).map((s) => (
                  <span key={s}>{s} ✦</span>
                ))}
              </span>
            ))}
          </div>
        </div>

        {/* ── PLATFORM ─────────────────────────────────────── */}
        <section id="platform" className="scroll-mt-24 py-24 sm:py-32">
          <div className="shell">
            <SectionHead eyebrow={t.platform.eyebrow} title={t.platform.title} lede={t.platform.lede} />

            <div className="reveal mt-12 grid gap-5 lg:grid-cols-[1.55fr_1fr]">
              <div className="panel panel--lift p-5 sm:p-7">
                <LiveTick
                  initial={tick}
                  labels={{ bid: t.platform.bid, ask: t.platform.ask, spread: t.platform.spread, source: t.platform.source }}
                />
                <div className="mt-7">
                  <CandleChart
                    series={marketSnapshot.series as unknown as Record<string, { t: string; o: number; h: number; l: number; c: number; v: number }[]>}
                    zones={a1.zones as number}
                    liquidity={a1.liquidity as number}
                    label={t.platform.liveLabel}
                  />
                </div>
                <div className="hairline mt-6 grid grid-cols-2 gap-4 pt-5 sm:grid-cols-4">
                  <Mini label={t.platform.bias} value={biasDir} />
                  <Mini label={t.platform.atr} value={String(a1.atr)} />
                  <Mini label={t.platform.zones} value={String(a1.zones)} />
                  <Mini label={t.platform.liquidity} value={String(a1.liquidity)} />
                </div>
              </div>

              <div className="flex flex-col gap-5">
                <SetupCard
                  setup={setup}
                  labels={{
                    setup: t.platform.setup,
                    entry: t.platform.entry,
                    stop: t.platform.stop,
                    targets: t.platform.targets,
                    rr: t.platform.rr,
                    confidence: t.platform.confidence,
                    factors: t.platform.factors,
                    invalidation: t.platform.invalidation,
                    session: t.platform.session,
                  }}
                />
                <p className="text-[0.75rem] leading-relaxed text-fog-dim">
                  <span className="mono">{t.platform.updated}: {captured} UTC</span>
                  <br />
                  {t.platform.disclaimer}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ── METHOD ───────────────────────────────────────── */}
        <section id="method" className="scroll-mt-24 border-y border-line bg-ink-2/40 py-24 sm:py-32">
          <div className="shell">
            <SectionHead eyebrow={t.method.eyebrow} title={t.method.title} lede={t.method.lede} />
            <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-2 lg:grid-cols-4">
              {t.method.steps.map((s, i) => (
                <li key={s.n} className="reveal bg-ink-3/60 p-6" style={{ ["--d" as string]: `${i * 70}ms` }}>
                  <span className="mono text-[0.7rem] tracking-[0.2em] text-gold-bright">{s.n}</span>
                  <h3 className="display mt-4 text-xl text-snow">{s.title}</h3>
                  <p className="mt-3 text-[0.86rem] leading-relaxed text-fog">{s.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ── TEAM ─────────────────────────────────────────── */}
        <section id="team" className="scroll-mt-24 py-24 sm:py-32">
          <div className="shell">
            <SectionHead eyebrow={t.team.eyebrow} title={t.team.title} lede={t.team.lede} />

            <div className="reveal mt-10 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line lg:grid-cols-4">
              <Big label={t.team.agents} value={workforce.agents} />
              <Big label={t.team.departments} value={workforce.departments} />
              <Big label={t.team.managers} value={workforce.managers} />
              <Big label={t.team.repos} value={workforce.privateRepos} />
            </div>

            <div className="reveal panel mt-6 overflow-hidden">
              <div className="hidden grid-cols-[1.1fr_1fr_0.6fr] gap-4 border-b border-line px-6 py-3 md:grid">
                <span className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{t.team.managerLabel}</span>
                <span className="mono text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{t.team.repoLabel}</span>
                <span className="mono text-end text-[0.62rem] tracking-[0.18em] text-fog-dim uppercase">{t.team.peopleLabel}</span>
              </div>
              <ul>
                {departments.map((d) => (
                  <li
                    key={d.key}
                    className="grid grid-cols-1 gap-2 border-b border-line px-6 py-4 last:border-0 hover:bg-ink-4/40 md:grid-cols-[1.1fr_1fr_0.6fr] md:items-center md:gap-4"
                  >
                    <span className="flex items-center gap-2.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-gold" aria-hidden="true" />
                      <span className="mono text-[0.82rem] text-snow">{d.manager}</span>
                    </span>
                    <span className="mono text-[0.78rem] text-fog-dim">{d.repo}</span>
                    <span className="mono text-[0.78rem] text-fog md:text-end">{d.headcount}</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="reveal mt-4 text-[0.78rem] text-fog-dim">{t.team.note}</p>
          </div>
        </section>

        {/* ── QUALITY ──────────────────────────────────────── */}
        <section className="border-y border-line bg-ink-2/40 py-24 sm:py-32">
          <div className="shell">
            <SectionHead eyebrow={t.quality.eyebrow} title={t.quality.title} lede={t.quality.lede} />
            <div className="reveal mt-12 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
              {t.quality.rows.map((r) => (
                <div key={r.label} className="bg-ink-3/60 px-6 py-6">
                  <div className="flex items-center justify-between gap-3">
                    <div className="mono text-[0.66rem] tracking-[0.16em] text-fog-dim uppercase">{r.label}</div>
                    <span
                      className={`mono text-[0.58rem] tracking-wider uppercase ${
                        r.state === "ok" ? "text-bull" : "text-bear"
                      }`}
                    >
                      {r.state === "ok" ? t.quality.verified : t.quality.blockedLabel}
                    </span>
                  </div>
                  <div className={`display mt-3 text-2xl ${r.state === "ok" ? "text-bull" : "text-bear"}`}>
                    {r.value}
                  </div>
                </div>
              ))}
            </div>
            <p className="reveal mt-5 max-w-3xl text-[0.8rem] leading-relaxed text-fog-dim">
              {t.quality.blockedNote}
            </p>
          </div>
        </section>

        {/* ── WORK ─────────────────────────────────────────── */}
        <section id="work" className="scroll-mt-24 py-24 sm:py-32">
          <div className="shell">
            <SectionHead eyebrow={t.work.eyebrow} title={t.work.title} lede={t.work.lede} />
            <div className="mt-12 grid gap-5 lg:grid-cols-3">
              {t.work.items.map((w, i) => (
                <article
                  key={w.name}
                  className="panel panel--lift reveal flex flex-col p-6"
                  style={{ ["--d" as string]: `${i * 80}ms` }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="mono text-[0.66rem] tracking-[0.16em] text-fog-dim uppercase">{w.kind}</span>
                    {i === 0 && (
                      <span className="tag tag--bull">
                        <span className="pulse" aria-hidden="true" />
                        {t.work.live}
                      </span>
                    )}
                  </div>
                  <h3 className="display mt-4 text-2xl text-snow">{w.name}</h3>
                  <p className="mt-3 flex-1 text-[0.88rem] leading-relaxed text-fog">{w.body}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {w.stack.map((s) => (
                      <span key={s} className="tag">{s}</span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── CONTACT ──────────────────────────────────────── */}
        <section id="contact" className="scroll-mt-24 border-t border-line py-24 sm:py-32">
          <div className="shell">
            <div className="panel panel--lift sheen relative overflow-hidden p-8 sm:p-14">
              <div className="rule-grid absolute inset-0 opacity-40" aria-hidden="true" />
              <div className="relative max-w-2xl">
                <p className="eyebrow">{t.contact.eyebrow}</p>
                <h2 className="display mt-5 text-[clamp(1.9rem,4.6vw,3.4rem)] text-snow">{t.contact.title}</h2>
                <p className="mt-5 text-[1rem] leading-relaxed text-fog">{t.contact.lede}</p>
                <div className="mt-9 flex flex-wrap items-center gap-4">
                  <a className="btn btn--gold" href="mailto:hello@astra.agency">
                    {t.contact.cta}
                    <span aria-hidden="true">→</span>
                  </a>
                  <span className="mono text-[0.74rem] text-fog-dim">{t.contact.note}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line py-10">
        <div className="shell flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <p className="mono text-[0.7rem] tracking-[0.14em] text-fog-dim">
            © {company.founded} {company.name} · {t.footer.rights}
          </p>
          <p className="text-[0.72rem] text-fog-dim">{t.footer.builtBy}</p>
          <div className="flex items-center gap-2">
            <span className="mono text-[0.66rem] text-fog-dim">{t.footer.lang}:</span>
            {LOCALES.map((code) => (
              <a
                key={code}
                href={`/${code}`}
                className={`tap mono text-[0.7rem] no-underline ${code === lang ? "text-gold-bright" : "text-fog-dim hover:text-snow"}`}
              >
                {LOCALE_LABEL[code]}
              </a>
            ))}
          </div>
        </div>
      </footer>
    </>
  );
}

function SectionHead({ eyebrow, title, lede }: { eyebrow: string; title: string; lede: string }) {
  return (
    <header className="reveal max-w-3xl">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="display mt-4 text-[clamp(1.9rem,4.6vw,3.4rem)] text-snow">{title}</h2>
      <p className="mt-5 text-[1rem] leading-relaxed text-fog">{lede}</p>
    </header>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mono text-[0.6rem] tracking-[0.16em] text-fog-dim uppercase">{label}</div>
      <div className="mono mt-1 text-sm text-snow">{value}</div>
    </div>
  );
}

function Big({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-ink-2/70 px-6 py-7">
      <div className="display text-4xl text-gold-bright">{value}</div>
      <div className="mono mt-2 text-[0.66rem] tracking-[0.16em] text-fog-dim uppercase">{label}</div>
    </div>
  );
}
