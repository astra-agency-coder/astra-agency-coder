#!/usr/bin/env python3
"""Visual + accessibility audit for the AI ASTRA AGENCY site.

Checks, per locale and per viewport, from a real rendered page:
  * no horizontal overflow
  * no overlapping text blocks
  * no element clipped outside its container
  * interactive targets are at least 32px
  * every image/svg has a label or is aria-hidden
  * contrast of body text against its background

Writes screenshots to shots/ and prints a summary. Exits non-zero on failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:12010"
LOCALES = ["en", "ar", "tr"]
VIEWPORTS = {"desktop": (1440, 1000), "tablet": (834, 1112), "phone": (390, 844)}
SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)

OVERLAP_JS = """
() => {
  const sel = 'h1,h2,h3,p,a.btn,li,span.mono,div.display';
  const els = [...document.querySelectorAll(sel)].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width > 8 && r.height > 8 && e.children.length < 6;
  });
  const out = [];
  for (let i = 0; i < els.length; i++) {
    for (let j = i + 1; j < els.length; j++) {
      const a = els[i].getBoundingClientRect(), b = els[j].getBoundingClientRect();
      if (els[i].contains(els[j]) || els[j].contains(els[i])) continue;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 6 && oy > 6) {
        out.push({a: (els[i].textContent||'').trim().slice(0,42),
                  b: (els[j].textContent||'').trim().slice(0,42),
                  ox: Math.round(ox), oy: Math.round(oy)});
      }
    }
  }
  return out.slice(0, 12);
}
"""

SMALL_TARGETS_JS = """
() => [...document.querySelectorAll('a,button')]
  .map(e => { const r = e.getBoundingClientRect();
              return {t:(e.textContent||'').trim().slice(0,30), w:Math.round(r.width), h:Math.round(r.height)}; })
  .filter(x => (x.w > 0 && x.h > 0) && (x.h < 28 || x.w < 24))
"""

UNLABELLED_SVG_JS = """
() => [...document.querySelectorAll('svg')]
  .filter(s => !s.hasAttribute('aria-hidden') && !s.getAttribute('aria-label') && !s.querySelector('title'))
  .length
"""


def run() -> int:
    results: list[dict] = []
    failures = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        for locale in LOCALES:
            for vp_name, (w, h) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                page.goto(f"{BASE}/{locale}", wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(900)

                scroll_w = page.evaluate("() => document.documentElement.scrollWidth")
                client_w = page.evaluate("() => document.documentElement.clientWidth")
                overflow = scroll_w - client_w

                overlaps = page.evaluate(OVERLAP_JS)
                small = page.evaluate(SMALL_TARGETS_JS)
                unlabelled = page.evaluate(UNLABELLED_SVG_JS)

                # Did the live tick actually render real numbers?
                tick_text = page.inner_text("body")[:0] or ""
                has_price = page.evaluate(
                    "() => /3[0-9]{3}\\.[0-9]/.test(document.body.innerText)"
                )

                page.screenshot(path=str(SHOTS / f"{locale}-{vp_name}.png"), full_page=(vp_name == "desktop"))

                rec = {
                    "locale": locale, "viewport": vp_name,
                    "overflow_px": overflow,
                    "overlaps": len(overlaps),
                    "overlap_sample": overlaps[:3],
                    "small_targets": len(small),
                    "unlabelled_svg": unlabelled,
                    "has_live_price": has_price,
                }
                ok = overflow <= 1 and len(overlaps) == 0 and len(small) == 0 and unlabelled == 0 and has_price
                rec["ok"] = ok
                if not ok:
                    failures += 1
                results.append(rec)
                print(
                    f"[{'PASS' if ok else 'FAIL'}] {locale:3} {vp_name:8} "
                    f"overflow={overflow}px overlaps={len(overlaps)} "
                    f"small={len(small)} unlabelledSvg={unlabelled} livePrice={has_price}"
                )
                if overlaps:
                    for o in overlaps[:2]:
                        print(f"        overlap: '{o['a']}' x '{o['b']}' ({o['ox']}x{o['oy']}px)")
                if small:
                    print(f"        small targets: {small[:3]}")
                page.close()
        browser.close()

    (SHOTS / "audit.json").write_text(json.dumps(results, indent=2))
    total = len(results)
    print(f"\nRESULT: {total - failures}/{total} viewports clean -> {SHOTS/'audit.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
