#!/usr/bin/env python3
"""Sync the approved landing mockup into the product and wire its CTAs.

The design team owns design/landing-mockup.html. This keeps web/index.html
identical except for the links that must reach the real product. Idempotent:
running it twice produces the same bytes.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "design" / "landing-mockup.html"
DST = ROOT / "web" / "index.html"

t = SRC.read_text()
t = t.replace('href="#pricing" data-i18n="nav.cta"',
              'href="/deck.html" data-i18n="nav.cta"')
t = re.sub(r'<a class="btn btn--primary" href="#pricing">(\s*<span data-i18n="hero.ctaPrimary">)',
           r'<a class="btn btn--primary" href="/deck.html">\1', t)
t = t.replace('<a class="btn btn--ghost" href="#top" data-i18n="price.free.cta">',
              '<a class="btn btn--ghost" href="/deck.html" data-i18n="price.free.cta">')
DST.write_text(t)

n = t.count('href="/deck.html"')
print(f"synced {SRC.name} -> {DST.name} ({len(t)} bytes, {n} deck links)")
sys.exit(0 if n >= 3 else 1)
