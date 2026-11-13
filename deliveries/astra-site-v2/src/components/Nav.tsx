"use client";

import { useEffect, useState } from "react";

export default function Nav({
  links,
  cta,
  locale,
  brand,
  langs,
}: {
  links: { href: string; label: string }[];
  cta: string;
  locale: string;
  brand: string;
  langs: { code: string; label: string }[];
}) {
  const [stuck, setStuck] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="nav" data-stuck={stuck}>
      <div className="shell flex items-center justify-between gap-6 py-4">
        <a href="#top" className="tap gap-3 no-underline" aria-label={brand}>
          <svg width="26" height="26" viewBox="0 0 64 64" aria-hidden="true">
            <path
              d="M32 3 L37.5 26.5 L61 32 L37.5 37.5 L32 61 L26.5 37.5 L3 32 L26.5 26.5 Z"
              fill="url(#navmark)"
            />
            <defs>
              <linearGradient id="navmark" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#F3E2AE" />
                <stop offset="0.55" stopColor="#E8C766" />
                <stop offset="1" stopColor="#C9A227" />
              </linearGradient>
            </defs>
          </svg>
          <span className="mono text-[0.78rem] tracking-[0.22em] text-fog">AI&nbsp;ASTRA</span>
        </a>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
          {links.map((l) => (
            <a key={l.href} className="nav__link" href={l.href}>
              {l.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-1 sm:flex" role="group" aria-label="Language">
            {langs.map((l) => (
              <a
                key={l.code}
                href={`/${l.code}`}
                aria-current={l.code === locale ? "true" : undefined}
                className={`tap tap--pill mono rounded-full text-[0.68rem] tracking-widest no-underline transition-colors ${
                  l.code === locale
                    ? "bg-gold text-[#17130a]"
                    : "text-fog-dim hover:text-snow"
                }`}
              >
                {l.code.toUpperCase()}
              </a>
            ))}
          </div>
          <a href="#contact" className="btn btn--gold hidden text-[0.82rem] sm:inline-flex">
            {cta}
          </a>
          <button
            type="button"
            className="tap md:hidden"
            aria-expanded={open}
            aria-label="Menu"
            onClick={() => setOpen((v) => !v)}
          >
            <span className="flex flex-col items-center gap-1.5">
              <span className="block h-px w-6 bg-snow" />
              <span className="block h-px w-6 bg-snow" />
            </span>
          </button>
        </div>
      </div>

      {open && (
        <div className="shell md:hidden">
          <div className="panel mb-4 flex flex-col gap-1 p-3">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="rounded-lg px-3 py-2.5 text-sm text-fog no-underline hover:bg-ink-4 hover:text-snow"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </a>
            ))}
            <a href="#contact" className="btn btn--gold mt-1 justify-center" onClick={() => setOpen(false)}>
              {cta}
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
