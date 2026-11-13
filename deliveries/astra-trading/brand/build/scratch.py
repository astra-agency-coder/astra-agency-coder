#!/usr/bin/env python3
"""Scratch: render mark + wordmarks to PNG for visual inspection."""
import cairosvg
from brandlib import ingot_a_svg, text_path_d, advance_width

OUT = "/tmp/scratch"
import os
os.makedirs(OUT, exist_ok=True)

GOLD = "#E8C766"
GOLD2 = "#C9A227"
BG = "#07070C"
INK = "#EEF0F7"

mark = ingot_a_svg(512, {"a": GOLD, "facet": "#FBF3DA"}, bg=BG, title="Astra Trading mark")
open(f"{OUT}/mark.svg", "w").write(mark)

# wordmark EN
d, w, bb = text_path_d("ASTRA TRADING", "SpaceGrotesk-var.ttf", 64, weight=600,
                       tracking=0.08)
wm = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}" height="80" '
      f'viewBox="0 0 {w:.1f} 80"><rect width="{w:.1f}" height="80" fill="{BG}"/>'
      f'<g transform="translate(0 60)" fill="{INK}">{d}</g></svg>')
open(f"{OUT}/wm_en.svg", "w").write(wm)

# wordmark AR
d2, w2, bb2 = text_path_d("أسترا تريدنغ", "IBMPlexSansArabic-SemiBold.ttf", 64,
                          direction="rtl", script="Arab", language="ar")
wm2 = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w2:.1f}" height="100" '
       f'viewBox="0 0 {w2:.1f} 100"><rect width="{w2:.1f}" height="100" fill="{BG}"/>'
       f'<g transform="translate(0 74)" fill="{INK}">{d2}</g></svg>')
open(f"{OUT}/wm_ar.svg", "w").write(wm2)

# wordmark TR
d3, w3, bb3 = text_path_d("ALTIN IŞIĞINDA ÖLÇÜLÜ ANALİZ", "IBMPlexSans-var.ttf", 40, weight=500)
wm3 = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w3:.1f}" height="60" '
       f'viewBox="0 0 {w3:.1f} 60"><rect width="{w3:.1f}" height="60" fill="{BG}"/>'
       f'<g transform="translate(0 44)" fill="{GOLD}">{d3}</g></svg>')
open(f"{OUT}/wm_tr.svg", "w").write(wm3)

for n in ("mark", "wm_en", "wm_ar", "wm_tr"):
    cairosvg.svg2png(url=f"{OUT}/{n}.svg", write_to=f"{OUT}/{n}.png", scale=2)
    print("rendered", n)
print("widths:", w, w2, w3)
