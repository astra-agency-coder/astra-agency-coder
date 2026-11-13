"use client";

import { useEffect, useState } from "react";

/** Thin gold progress line under the nav. Purely decorative, aria-hidden. */
export default function ScrollProgress() {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      setPct(h > 0 ? Math.min(1, window.scrollY / h) : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="fixed inset-x-0 top-0 z-[60] h-px origin-left bg-gradient-to-r from-gold-deep via-gold-bright to-gold-soft"
      style={{ transform: `scaleX(${pct})`, transformOrigin: "0% 50%" }}
    />
  );
}
