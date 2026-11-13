#!/usr/bin/env python3
"""Build every Astra Trading brand asset: SVGs, brand sheet, checks.json."""
from __future__ import annotations

import json
from pathlib import Path

import cairosvg

from brandlib import contrast, ingot_a_svg, text_path_d, wcag_grade
from palette import REF, SYS, TEXT_PAIRS, resolve
from svgkit import Canvas

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

# ---- font files ----------------------------------------------------------- #
SG = "SpaceGrotesk-var.ttf"
PS = "IBMPlexSans-var.ttf"
PA = "IBMPlexSansArabic-SemiBold.ttf"
PA_MED = "IBMPlexSansArabic-Medium.ttf"
PA_REG = "IBMPlexSansArabic-Regular.ttf"
PM = "IBMPlexMono-Medium.ttf"

# ---- colours -------------------------------------------------------------- #
GOLD = REF["gold-300"]
GOLD_BRAND = REF["gold-500"]
GOLD_DEEP = REF["gold-700"]
BRIGHT = REF["gold-100"]
BG = REF["neutral-3"]
SURF1 = REF["neutral-8"]
SURF2 = REF["neutral-12"]
INK = REF["neutral-90"]
MUTED = REF["neutral-70"]
SUBTLE = REF["neutral-60"]
OUTLINE = REF["neutral-20"]
BULL = REF["bull-400"]
BEAR = REF["bear-400"]
FLAT = REF["flat-400"]
VIOLET = REF["violet-300"]
VIOLET7 = REF["violet-700"]

WORD_EN = "ASTRA TRADING"
WORD_TR = "ASTRA TRADING"
AR_NAME = "أسترا تريدينغ"
AR_DESC = "تحليل الذهب الفني"
TR_DESC = "ÖLÇÜLÜ ALTIN ANALİZİ · DEĞER ŞEFFAFLIĞI"


def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")
    return path


def render(svg_path: Path, png_path: Path, scale: float = 2.0, w=None, h=None):
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=scale,
                     output_width=w, output_height=h)


# --------------------------------------------------------------------------- #
# 1. Mark files
# --------------------------------------------------------------------------- #
def build_mark_files():
    # logo-mark.svg — primary mark on transparent (gold + bright facet)
    write(ROOT / "logo-mark.svg",
          ingot_a_svg(512, {"a": GOLD, "facet": BRIGHT}, bg=None))
    # logo-mono.svg — single colour, inherits `color` (defaults to light ink)
    mono = ingot_a_svg(512, {"a": "currentColor"}, bg=None)
    mono = mono.replace('<svg xmlns', '<svg style="color:#EEF0F7" xmlns', 1)
    write(ROOT / "logo-mono.svg", mono)
    # logo-mark-bright.svg — mark for light backgrounds (deep gold)
    write(ROOT / "logo-mark-onlight.svg",
          ingot_a_svg(512, {"a": GOLD_DEEP, "facet": GOLD_BRAND}, bg=None))


# --------------------------------------------------------------------------- #
# 2. Primary lockup
# --------------------------------------------------------------------------- #
def _cap_ratio(font, weight=None):
    """cap-height / em, measured from the letter H."""
    _d, _w, bb = text_path_d("H", font, 1000.0, weight=weight)
    return (bb[3] - bb[1]) / 1000.0


def _mark_group(x, y, size, a=GOLD, facet=BRIGHT):
    inner = ingot_a_svg(512, {"a": a, "facet": facet}).split(">", 1)[1].replace("</svg>", "")
    s = size / 512.0
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.6f})">'
            f'{inner}</g>')


def _lockup(x, y, mark_h=150.0, gap_ratio=0.34, word=WORD_EN, font=SG, weight=600,
            tracking=0.035, mark_a=GOLD, mark_facet=BRIGHT, ink=INK, rule=GOLD,
            with_rule=True):
    """Return (svg_fragment, width, height) for a horizontal lockup at (x,y).

    Mark height = mark_h; wordmark cap height = 0.60 * mark_h.
    """
    cap = 0.60 * mark_h
    size = cap / _cap_ratio(font, weight)
    _d, ww, bb = text_path_d(word, font, size, weight=weight, tracking=tracking)
    gap = mark_h * gap_ratio
    tx = x + mark_h + gap
    baseline = y + mark_h / 2.0 + cap / 2.0
    frag = [_mark_group(x, y, mark_h, mark_a, mark_facet)]
    frag.append(f'<g transform="translate({tx:.2f} {baseline:.2f})" fill="{ink}">'
                + text_path_d(word, font, size, weight=weight, tracking=tracking)[0]
                + "</g>")
    if with_rule:
        ry = baseline + mark_h * 0.14
        frag.append(f'<line x1="{tx:.2f}" y1="{ry:.2f}" x2="{tx+ww:.2f}" y2="{ry:.2f}" '
                    f'stroke="{rule}" stroke-width="{mark_h*0.016:.2f}" opacity="0.85"/>')
        for i in range(5):
            txx = tx + ww * i / 4.0
            hgt = mark_h * 0.05 if i in (0, 4) else mark_h * 0.03
            frag.append(f'<line x1="{txx:.2f}" y1="{ry:.2f}" x2="{txx:.2f}" '
                        f'y2="{ry+hgt:.2f}" stroke="{rule}" '
                        f'stroke-width="{mark_h*0.012:.2f}" opacity="0.85"/>')
    width = mark_h + gap + ww
    height = mark_h + (mark_h * 0.14 + mark_h * 0.05) if with_rule else mark_h
    return "".join(frag), width, height


def build_primary():
    pad = 30.0
    frag, w, h = _lockup(0, 0, mark_h=150.0)
    W, H = w + pad * 2, h + pad * 2
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {H:.2f}" '
           f'width="{W:.2f}" height="{H:.2f}" role="img" '
           f'aria-label="Astra Trading"><title>Astra Trading</title>'
           f'<g transform="translate({pad:.2f} {pad:.2f})">{frag}</g></svg>')
    write(ROOT / "logo-primary.svg", svg)


# --------------------------------------------------------------------------- #
# 3. Wordmarks (three scripts)
# --------------------------------------------------------------------------- #
def build_wordmark(name, lines, wpad=16.0, vpad=14.0):
    """lines: list of dicts(text, font, size, weight, fill, dir, script, lang, tracking)"""
    W = 0.0
    for ln in lines:
        _d, w, _b = text_path_d(ln["text"], ln["font"], ln["size"],
                                weight=ln.get("weight"), direction=ln.get("dir", "ltr"),
                                script=ln.get("script"), language=ln.get("lang"),
                                tracking=ln.get("tracking", 0.0))
        W = max(W, w)
    W += wpad * 2
    c = Canvas(W, 10, "none")
    c.parts.clear()
    y = vpad
    heights = []
    for ln in lines:
        size = ln["size"]
        _d, w, bbox = text_path_d(ln["text"], ln["font"], size, weight=ln.get("weight"),
                                  direction=ln.get("dir", "ltr"), script=ln.get("script"),
                                  language=ln.get("lang"), tracking=ln.get("tracking", 0.0))
        y += -bbox[1] + 2  # ascend to top of glyphs
        x = wpad
        anchor = "start"
        if ln.get("dir") == "rtl" or ln.get("rtl"):
            x = W - wpad
            anchor = "end"
        c.text(x, y, ln["text"], ln["font"], size, ln["fill"], weight=ln.get("weight"),
               direction=ln.get("dir", "ltr"), script=ln.get("script"),
               language=ln.get("lang"), anchor=anchor, tracking=ln.get("tracking", 0.0),
               bg=BG, purpose=f"wordmark {name}")
        y += 8 + size * 0.18  # gap before next line
        heights.append(size)
    H = y + vpad
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.2f} {H:.2f}" '
           f'width="{W:.2f}" height="{H:.2f}" role="img" aria-label="Astra Trading wordmark">'
           f'<title>Astra Trading — {name} wordmark</title>' + "".join(c.parts) + "</svg>")
    write(ROOT / f"wordmark-{name}.svg", svg)
    return W, H


def build_wordmarks():
    build_wordmark("en", [
        {"text": WORD_EN, "font": SG, "size": 96, "weight": 600, "fill": INK,
         "tracking": 0.035},
        {"text": "GOLD MARKET ANALYSIS", "font": PM, "size": 24, "fill": GOLD,
         "tracking": 0.28},
    ])
    build_wordmark("ar", [
        {"text": AR_NAME, "font": PA, "size": 96, "fill": INK, "dir": "rtl",
         "script": "Arab", "lang": "ar"},
        {"text": AR_DESC, "font": PA_MED, "size": 34, "fill": GOLD, "dir": "rtl",
         "script": "Arab", "lang": "ar"},
    ])
    build_wordmark("tr", [
        {"text": WORD_TR, "font": SG, "size": 96, "weight": 600, "fill": INK,
         "tracking": 0.035},
        {"text": TR_DESC, "font": PS, "size": 26, "weight": 500, "fill": GOLD,
         "tracking": 0.02},
    ])


# --------------------------------------------------------------------------- #
# 4. Favicon (must be legible at 16 px)
# --------------------------------------------------------------------------- #
def build_favicon():
    S = 32
    inner = ingot_a_svg(512, {"a": GOLD, "facet": BRIGHT}).split(">", 1)[1].replace("</svg>", "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" '
           f'width="{S}" height="{S}" role="img" aria-label="Astra Trading">'
           f'<title>Astra Trading</title>'
           f'<rect width="{S}" height="{S}" rx="7" fill="{BG}"/>'
           f'<rect x="0.5" y="0.5" width="{S-1}" height="{S-1}" rx="6.5" fill="none" '
           f'stroke="{GOLD_BRAND}" stroke-width="1" opacity="0.55"/>'
           f'<g transform="translate({S*0.5:.2f} {S*0.5:.2f}) scale({S*0.70/512:.5f}) '
           f'translate(-256 -256)">{inner}</g></svg>')
    write(ROOT / "favicon.svg", svg)


# --------------------------------------------------------------------------- #
# 5. Brand sheet
# --------------------------------------------------------------------------- #
def build_sheet():
    W, H = 2000, 3000
    c = Canvas(W, H, BG)
    M = 96.0

    def section(y, num, title, sub=""):
        c.text(M, y, num, PM, 22, GOLD, bg=BG, purpose="section number")
        c.text(M + 58, y, title, SG, 40, INK, weight=600, bg=BG, purpose="section title")
        if sub:
            c.text(M + 58, y + 30, sub, PS, 19, MUTED, weight=400, bg=BG,
                   purpose="section sub")
        c.line(M, y + 56, W - M, y + 56, OUTLINE, 1.5)
        return y + 96

    def panel(x, y, w, h, fill=SURF1, stroke=OUTLINE, rx=14):
        c.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.2, rx=rx)

    def mark_at(x, y, size, a=GOLD, facet=BRIGHT):
        c.raw(f'<g transform="translate({x:.2f} {y:.2f})">'
              + ingot_a_svg(512, {"a": a, "facet": facet}).split(">", 1)[1].replace("</svg>", "")
              + "</g>")

    # ---------------- header ---------------- #
    mark_at(M, 70, 92)
    c.text(M + 118, 112, "Astra Trading", SG, 52, INK, weight=600, bg=BG, purpose="title")
    c.text(M + 120, 146, "BRAND IDENTITY — v1.0  ·  product brand of AI ASTRA AGENCY",
           PM, 20, GOLD, bg=BG, purpose="subtitle")
    c.text(W - M, 112, "XAU/USD · Gold, decoded.", PS, 24, MUTED, anchor="end",
           bg=BG, purpose="tagline")
    c.text(W - M, 146, "ar · en · tr", PM, 20, VIOLET, anchor="end", bg=BG,
           purpose="languages")
    c.line(M, 182, W - M, 182, GOLD_BRAND, 2.0, op=0.7)

    # ---------------- 01 concept ---------------- #
    y = section(238, "01", "Concept — “The Ingot A”",
                "signal in the noise · the measured element · Au, atomic number 79")
    # big mark
    panel(M, y, 420, 420)
    mark_at(M + 60, y + 60, 300)
    c.text(M + 210, y + 400, "the mark", PM, 18, MUTED, anchor="middle", bg=SURF1,
           purpose="caption")
    # construction breakdown
    cx = M + 460
    c.text(cx, y + 28, "Construction — three exact primitives, no curves", PS, 22,
           INK, weight=500, bg=BG, purpose="h3")
    prims = [
        ("the left leg", "one diagonal — direction, the trend", GOLD),
        ("the right leg", "a vertical bullion (Au bar) — the measured element", GOLD),
        ("the crossbar", "a gauge tick that runs past the leg — the read-out", INK),
    ]
    py = y + 60
    for label, desc, col in prims:
        c.rect(cx, py, 34, 34, fill=col, rx=6)
        c.text(cx + 50, py + 24, label, PS, 21, INK, weight=600, bg=BG, purpose="prim label")
        c.text(cx + 50, py + 48, desc, PS, 17, MUTED, bg=BG, purpose="prim desc")
        py += 84
    # concepts explored
    c.text(cx, py + 6, "Concepts explored", PS, 22, INK, weight=500, bg=BG, purpose="h3")
    py += 40
    concepts = [
        ("A", "Signal Waveform", "rejected — reads as generic “audio/telecom”, weak at 16 px", FLAT),
        ("B", "Precision Caliper", "rejected — too mechanical, hard to own as a single glyph", FLAT),
        ("C", "The Ingot A", "CHOSEN — a letterform AND a bullion AND a gauge", GOLD),
    ]
    for letter, name, note, col in concepts:
        c.circle(cx + 17, py + 15, 17, fill="none", stroke=col, sw=2.0)
        c.text(cx + 17, py + 22, letter, PM, 18, col, anchor="middle", bg=BG,
               purpose="concept letter")
        c.text(cx + 50, py + 14, name, PS, 20, INK, weight=600, bg=BG, purpose="concept name")
        c.text(cx + 50, py + 36, note, PS, 16, MUTED, bg=BG, purpose="concept note")
        py += 62
    # rationale box
    panel(cx + 470, y, W - M - (cx + 470), 420, fill=SURF2)
    c.text(cx + 500, y + 44, "Why C", PM, 20, GOLD, bg=SURF2, purpose="h3")
    rationale = [
        "It is a letterform first: at 16 px it still",
        "reads as “A”, so the brand survives the",
        "smallest favicon without the wordmark.",
        "",
        "It is an object second: the right leg is a",
        "gold bullion — the asset itself, rendered as",
        "a measured element, not a cartoon coin.",
        "",
        "It is an instrument third: the crossbar is a",
        "gauge tick that runs past the leg — the",
        "read-out. Credibility over hype.",
        "",
        "Three straight-edged primitives, unioned",
        "exactly, so the geometry is provable and",
        "scales losslessly to any size.",
    ]
    ry = y + 82
    for line in rationale:
        if line:
            c.text(cx + 500, ry, line, PS, 18, INK if not line.startswith(("It is", "Three")) else INK,
                   bg=SURF2, purpose="rationale")
        ry += 24

    # ---------------- 02 logo suite ---------------- #
    y = section(720, "02", "Logo suite", "lockups · mark · mono · favicon · clear space")
    # primary lockup on dark
    panel(M, y, 1180, 250)
    c.raw(f'<g transform="translate({M+48:.2f} {y+58:.2f})">'
          + _lockup_inner(mark_h=118.0) + "</g>")
    c.text(M + 48, y + 232, "logo-primary.svg — default signature, dark background",
           PM, 17, MUTED, bg=SURF1, purpose="caption")
    # mark + mono + favicon
    panel(M + 1210, y, W - M - (M + 1210), 250)
    mark_at(M + 1234, y + 40, 152)
    mark_at(M + 1420, y + 40, 152, a="#FFFFFF", facet="#FFFFFF")
    c.raw(f'<g transform="translate({M+1606:.2f} {y+40:.2f})">'
          + _favicon_inner(152) + "</g>")
    c.text(M + 1234, y + 228, "logo-mark", PM, 15, MUTED, bg=SURF1, purpose="caption")
    c.text(M + 1420, y + 228, "logo-mono", PM, 15, MUTED, bg=SURF1, purpose="caption")
    c.text(M + 1606, y + 228, "favicon", PM, 15, MUTED, bg=SURF1, purpose="caption")

    y2 = y + 290
    # clear space diagram
    panel(M, y2, 700, 300)
    cs_mark = 120
    cs_pad = cs_mark * 0.5
    gx = M + 70
    gy = y2 + 60
    c.rect(gx - cs_pad, gy - cs_pad, cs_mark + cs_pad * 2, cs_mark + cs_pad * 2,
           fill="none", stroke=GOLD, sw=1.5, rx=6)
    c.rect(gx, gy, cs_mark, cs_mark, fill="none", stroke=OUTLINE, sw=1.0)
    mark_at(gx, gy, cs_mark)
    c.text(gx + cs_mark / 2, gy + cs_mark / 2, "h", PM, 20, GOLD, anchor="middle",
           bg=SURF1, purpose="clearspace h", opacity=0.9)
    c.text(M + 420, y2 + 90, "Clear space = 0.5 × h", PS, 22, INK, weight=600, bg=SURF1,
           purpose="cs title")
    for i, ln in enumerate(["Nothing enters the dashed zone:",
                            "no type, no image edge, no",
                            "second logo. h = mark height."]):
        c.text(M + 420, y2 + 126 + i * 26, ln, PS, 17, MUTED, bg=SURF1, purpose="cs note")
    # minimum sizes
    c.text(M + 420, y2 + 228, "Minimum sizes", PS, 20, INK, weight=600, bg=SURF1,
           purpose="min title")
    c.text(M + 420, y2 + 256, "mark 16 px · lockup 120 px wide · print 10 mm",
           PS, 17, MUTED, bg=SURF1, purpose="min note")
    # misuse
    panel(M + 730, y2, W - M - (M + 730), 300, fill=SURF2)
    c.text(M + 770, y2 + 44, "Don't", PM, 20, BEAR, bg=SURF2, purpose="dont title")
    donts = ["stretch or squash the mark",
             "rotate, outline or add a drop shadow",
             "place gold on mid-grey (no contrast)",
             "recolour the gold outside the palette",
             "crop the mark or break the 0.5h zone"]
    for i, d in enumerate(donts):
        c.text(M + 770, y2 + 84 + i * 30, "—  " + d, PS, 18, INK, bg=SURF2, purpose="dont item")
    c.text(M + 770, y2 + 258, "Do: use the approved colourways, scale uniformly,",
           PS, 17, BULL, bg=SURF2, purpose="do note")
    c.text(M + 770, y2 + 280, "keep the clear space, prefer the mark at small sizes.",
           PS, 17, BULL, bg=SURF2, purpose="do note2")

    # ---------------- 03 colour ---------------- #
    y = section(1400, "03", "Colour system",
                "gold as a measured element · bull / bear / flat · every pair measured")
    # gold ramp
    c.text(M, y + 10, "Gold ramp (Au)", PM, 19, GOLD, bg=BG, purpose="h3")
    gold_steps = ["gold-100", "gold-200", "gold-300", "gold-400", "gold-500",
                  "gold-600", "gold-700", "gold-800", "gold-900"]
    sw = 118
    for i, k in enumerate(gold_steps):
        x = M + i * (sw + 10)
        c.rect(x, y + 30, sw, 90, fill=REF[k], rx=8)
        # pick the ink with the higher contrast against this swatch
        ink = REF["neutral-3"] if contrast(REF[k], REF["neutral-3"]) >= contrast(REF[k], INK) else INK
        c.text(x + sw / 2, y + 84, k.replace("gold-", ""), PM, 16, ink,
               anchor="middle", bg=REF[k], purpose="gold step")
    # neutral + violet
    c.text(M, y + 160, "Neutrals & the inherited accent", PM, 19, MUTED, bg=BG, purpose="h3")
    neut = ["neutral-3", "neutral-5", "neutral-8", "neutral-12", "neutral-20",
            "neutral-40", "neutral-60", "neutral-70", "neutral-90", "violet-300", "violet-700"]
    for i, k in enumerate(neut):
        x = M + i * (sw + 10)
        c.rect(x, y + 180, sw, 70, fill=REF[k], rx=8,
               stroke=OUTLINE if k in ("neutral-3", "neutral-5") else None, sw=1)
        lab = REF[k].lstrip("#")
        c.text(x + sw / 2, y + 268, lab, PM, 14, MUTED, anchor="middle", bg=BG,
               purpose="neutral hex", register=False)

    # semantic chart language + mini chart
    cy = y + 300
    c.text(M, cy, "Semantic chart language", PM, 19, GOLD, bg=BG, purpose="h3")
    sem = [("BULL", BULL, "candles up / demand"), ("BEAR", BEAR, "candles down / supply"),
           ("FLAT", FLAT, "indecision / range"), ("GOLD", GOLD, "XAU price line")]
    for i, (nm, col, desc) in enumerate(sem):
        x = M + i * 300
        c.rect(x, cy + 22, 64, 64, fill=col, rx=10)
        c.text(x + 80, cy + 48, nm, PM, 20, INK, bg=BG, purpose="sem name")
        c.text(x + 80, cy + 72, desc, PS, 16, MUTED, bg=BG, purpose="sem desc")
    # mini candlestick chart panel
    panel(M, cy + 110, 1180, 240, fill=REF["neutral-5"])
    c.text(M + 20, cy + 140, "XAU/USD · illustrative", PM, 15, MUTED, bg=REF["neutral-5"],
           purpose="chart caption")
    import random
    random.seed(7)
    n = 26
    bw = 26
    bx = M + 40
    base = cy + 320
    price = 0.0
    for i in range(n):
        o = price
        d = random.uniform(-1, 1)
        cl = o + d
        hi = max(o, cl) + random.uniform(0, 0.6)
        lo = min(o, cl) - random.uniform(0, 0.6)
        col = BULL if cl >= o else BEAR
        x = bx + i * (bw + 8)
        scale = 62.0
        yh = base - hi * scale
        yl = base - lo * scale
        yo = base - o * scale
        ycl = base - cl * scale
        c.line(x + bw / 2, yh, x + bw / 2, yl, col, 2.0)
        top = min(yo, ycl)
        c.rect(x, top, bw, max(2.0, abs(ycl - yo)), fill=col, rx=2)
        price = cl
    c.rect(M, cy + 110, 1180, 240, fill="none", stroke=OUTLINE, sw=1.2, rx=14)
    # contrast table
    tx = M + 1210
    panel(tx, cy + 110, W - M - tx, 240, fill=SURF2)
    c.text(tx + 30, cy + 150, "Measured contrast (WCAG)", PM, 19, GOLD, bg=SURF2,
           purpose="h3")
    rows = [
        ("body ink / page", INK, BG),
        ("secondary / page", MUTED, BG),
        ("gold link / page", GOLD, BG),
        ("ink / gold button", REF["neutral-3"], GOLD),
        ("bull / chart", BULL, REF["neutral-5"]),
        ("bear / chart", BEAR, REF["neutral-5"]),
        ("violet accent / page", VIOLET, BG),
    ]
    ry = cy + 184
    for label, fg, bg in rows:
        r = contrast(fg, bg)
        c.text(tx + 30, ry, label, PS, 16, INK, bg=SURF2, purpose="ct label")
        c.text(tx + 340, ry, f"{r:.2f}:1", PM, 16, GOLD, anchor="end", bg=SURF2,
               purpose="ct ratio")
        c.text(tx + 370, ry, wcag_grade(r, False), PM, 16, BULL if r >= 4.5 else BEAR,
               bg=SURF2, purpose="ct grade")
        ry += 26

    # ---------------- 04 typography ---------------- #
    y = section(2060, "04", "Typography", "open-licence (OFL) · Latin · Arabic · Turkish · data")
    ty = y + 20
    # Latin display
    c.text(M, ty + 40, "Aa", SG, 96, INK, weight=700, bg=BG, purpose="type specimen")
    c.text(M + 170, ty + 6, "Space Grotesk", PS, 26, INK, weight=600, bg=BG, purpose="type name")
    c.text(M + 170, ty + 32, "Display & wordmark · OFL · Space Grotesk", PS, 16, MUTED,
           bg=BG, purpose="type note")
    c.text(M + 170, ty + 56, "ABCDEFGHIJKLMNOPQRSTUVWXYZ  0123456789", PM, 18, GOLD,
           bg=BG, purpose="type glyphs")
    # Arabic (RTL — text starts at the right edge of its column)
    c.text(M + 1120, ty + 46, "أسترا", PA, 84, INK, direction="rtl", script="Arab",
           language="ar", anchor="end", bg=BG, purpose="arabic specimen")
    c.text(M + 1180, ty + 6, "IBM Plex Sans Arabic", PS, 26, INK, weight=600, bg=BG,
           purpose="type name ar")
    c.text(M + 1180, ty + 32, "Arabic UI & wordmark · OFL · proper RTL joining", PS, 16,
           MUTED, bg=BG, purpose="type note ar")
    c.text(M + 1180, ty + 62, "ابتثجحخدذرزسشصضطظعغفقكلمنهوي ٠١٢٣٤٥٦٧٨٩", PA_REG, 18, GOLD,
           direction="rtl", script="Arab", language="ar", anchor="end",
           bg=BG, purpose="type glyphs ar")
    # Turkish line (must show ğ ş ı İ ö ü ç)
    c.text(M, ty + 150, "Türkçe — ğ ş ı İ ö ü ç", PS, 30, INK, weight=500, bg=BG,
           purpose="turkish specimen")
    c.text(M, ty + 182, "ÖLÇÜLÜ ALTIN ANALİZİ · ŞEFFAF GEÇMİŞ · DEĞİŞKEN", PM, 20, GOLD,
           bg=BG, purpose="turkish upper")
    # data/mono
    c.text(M + 900, ty + 150, "JetBrains-style data", PS, 26, INK, weight=600, bg=BG,
           purpose="type name mono")
    c.text(M + 900, ty + 178, "IBM Plex Mono · numbers, R:R, prices, code · OFL", PS, 16,
           MUTED, bg=BG, purpose="type note mono")
    c.text(M + 900, ty + 206, "1.2345   R:R 1:2.5   −0.42%   4,820.50", PM, 20, GOLD,
           bg=BG, purpose="mono sample")

    # ---------------- 05 wordmarks ---------------- #
    y = section(2330, "05", "Wordmarks in three scripts",
                "Arabic is designed RTL — connected letterforms, not a mirrored Latin hack")
    pw = 560
    panel(M, y, pw, 210)
    c.raw(_wm_place("en", M + 30, y + 34, pw - 60, 130))
    c.text(M + 30, y + 190, "wordmark-en.svg", PM, 16, MUTED, bg=SURF1, purpose="caption")
    panel(M + 590, y, pw, 210)
    c.raw(_wm_place("ar", M + 620, y + 30, pw - 60, 134))
    c.text(M + 620, y + 190, "wordmark-ar.svg · RTL, connected", PM, 16, MUTED, bg=SURF1,
           purpose="caption")
    panel(M + 1180, y, W - M - (M + 1180), 210)
    c.raw(_wm_place("tr", M + 1210, y + 34, W - M - (M + 1180) - 60, 130))
    c.text(M + 1210, y + 190, "wordmark-tr.svg", PM, 16, MUTED, bg=SURF1, purpose="caption")

    # ---------------- footer ---------------- #
    fy = H - 90
    c.line(M, fy - 40, W - M, fy - 40, OUTLINE, 1.5)
    c.text(M, fy, "Astra Trading — Brand Identity v1.0 · AI ASTRA AGENCY (Creative, astra-ccr) · "
                  "2026-11-13 · OFL fonts: Space Grotesk, IBM Plex Sans / Sans Arabic / Mono",
           PS, 17, MUTED, bg=BG, purpose="footer")
    c.text(W - M, fy, "gold, decoded.", PM, 17, GOLD, anchor="end", bg=BG, purpose="footer tag")

    svg = c.svg()
    write(ROOT / "brand-sheet.svg", svg)
    failures = c.contrast_failures()
    return c, failures


def _lockup_inner(mark_h=150.0, ink=INK, mark_a=GOLD):
    frag, _w, _h = _lockup(0, 0, mark_h=mark_h, ink=ink, mark_a=mark_a)
    return frag


def _favicon_inner(size=170.0, radius_ratio=0.219):
    """Render the favicon tile at `size` px using its real 32px construction."""
    S = 32.0
    inner = ingot_a_svg(512, {"a": GOLD, "facet": BRIGHT}).split(">", 1)[1].replace("</svg>", "")
    k = size / S
    return (f'<g transform="scale({k:.5f})">'
            f'<rect width="{S}" height="{S}" rx="{S*radius_ratio:.2f}" fill="{BG}"/>'
            f'<rect x="0.5" y="0.5" width="{S-1}" height="{S-1}" rx="{S*radius_ratio-0.5:.2f}" '
            f'fill="none" stroke="{GOLD_BRAND}" stroke-width="1" opacity="0.55"/>'
            f'<g transform="translate({S/2} {S/2}) scale({S*0.72/512:.5f}) translate(-256 -256)">'
            f'{inner}</g></g>')


def _wm_inner(name):
    svg = (ROOT / f"wordmark-{name}.svg").read_text(encoding="utf-8")
    return svg.split(">", 1)[1].replace("</svg>", "")


def _wm_place(name, x, y, max_w, max_h):
    """Embed wordmark-<name>.svg scaled to fit (max_w, max_h), left-aligned."""
    svg = (ROOT / f"wordmark-{name}.svg").read_text(encoding="utf-8")
    vb = svg.split('viewBox="', 1)[1].split('"', 1)[0].split()
    w, h = float(vb[2]), float(vb[3])
    k = min(max_w / w, max_h / h)
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})">'
            + svg.split(">", 1)[1].replace("</svg>", "") + "</g>")


def main():
    build_mark_files()
    build_primary()
    build_wordmarks()
    build_favicon()
    c, failures = build_sheet()
    render(ROOT / "brand-sheet.svg", ROOT / "brand-sheet.png", scale=1.0)
    # sheet size check
    from PIL import Image
    im = Image.open(ROOT / "brand-sheet.png")
    print("brand-sheet.png", im.size)
    print("sheet text elements:", len(c.elements))
    print("sheet contrast failures:", len(failures))
    for f in failures:
        print("  FAIL", f["text"][:40], f["ratio"], f["purpose"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
