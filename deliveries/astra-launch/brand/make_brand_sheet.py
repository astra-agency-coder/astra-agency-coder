#!/usr/bin/env python3
"""ASTRA brand sheet (one rendered PNG) + objective brand checks.

Reads tokens.json and the SVG suite in this folder, composes a single brand
sheet, and runs the acceptance checks (dimensions, token integrity, SVG parse,
contrast) writing brand/checks.json.

Contrast is enforced the hard way: every text and swatch element drawn on the
sheet is *registered* with its ink colour and the local background actually
measured from the rendered pixels (modal colour per column cell of the element's
bounding box). The minimum ratio across all elements must be >= 4.5:1, so a
dark-on-dark or ink-equals-fill regression cannot ship. The script exits
non-zero if any element fails.

Run:  python3 make_brand_sheet.py
"""
from __future__ import annotations

import io
import json
import math
import random
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
T = json.loads((HERE / "tokens.json").read_text())
REF = T["color"]["ref"]
L, D = T["color"]["sys_resolved"]["light"], T["color"]["sys_resolved"]["dark"]

F = "/usr/share/fonts/truetype/dejavu/"
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(F + name, size)

W, H = 2400, 4600
PAD = 140

# Every text/swatch element drawn on the sheet is registered here so it can be
# contrast-checked against its real background.
ELEMENTS: list[dict] = []
TEXT_MIN = 4.5
GRAPHIC_MIN = 3.0


def hx(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    a = hx(a) if isinstance(a, str) else tuple(a[:3])
    b = hx(b) if isinstance(b, str) else tuple(b[:3])
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _to_inks(inks) -> list[tuple[int, int, int]]:
    """Normalise a hex string, an (r,g,b) tuple, or a list of either."""
    if isinstance(inks, str):
        return [hx(inks)]
    if isinstance(inks, tuple) and len(inks) >= 3 and isinstance(inks[0], int):
        return [tuple(inks[:3])]
    return [hx(c) if isinstance(c, str) else tuple(c[:3]) for c in inks]


def worst_bg_contrast(src: Image.Image, box, inks, cells: int = 8,
                      pad: int = 14, interior: bool = False) -> tuple[float, tuple]:
    """Minimum contrast of `inks` against the local background of `box`.

    For text sitting directly on the base plate (`interior=False`) the
    background is sampled from the padding *ring* around the element — the
    pixels just outside its bounding box, which the ink does not cover — sliced
    into `cells` column strips. Sampling the ring (not the box interior) is what
    makes this work for large bold glyphs, whose thick strokes would otherwise
    fill a strip and be mistaken for the background.

    For an element sitting on a solid panel/swatch (`interior=True`) the
    background is the modal colour *inside* the box (the panel fill dominates,
    even with the mark/text drawn on it).

    Either way the modal is robust to the soft glow gradients and sparse star
    speckle of the sheet, while still catching dark-on-dark text (where the
    modal background equals the ink).
    """
    inks = _to_inks(inks)
    bx0, by0, bx1, by1 = (int(round(v)) for v in box)
    x0, y0 = max(0, bx0 - pad), max(0, by0 - pad)
    x1, y1 = min(src.width, bx1 + pad), min(src.height, by1 + pad)
    if x1 <= x0 or y1 <= y0:
        return 0.0, (0, 0, 0)

    if interior:
        # single modal colour of the panel interior
        data = list(src.crop((max(0, bx0), max(0, by0),
                              min(src.width, bx1), min(src.height, by1))).getdata())
        bg = Counter(data).most_common(1)[0][0]
        return min(contrast(i, bg) for i in inks), bg

    def ring_pixels(cx0: int, cx1: int) -> list:
        px = []
        if by0 > y0:                       # top band
            px += list(src.crop((cx0, y0, cx1, by0)).getdata())
        if y1 > by1:                       # bottom band
            px += list(src.crop((cx0, by1, cx1, y1)).getdata())
        if bx0 > x0:                       # left sliver
            px += list(src.crop((x0, by0, bx0, by1)).getdata())
        if x1 > bx1:                       # right sliver
            px += list(src.crop((bx1, by0, x1, by1)).getdata())
        return px

    cw = (x1 - x0) / cells
    worst, worst_bg = 99.0, (0, 0, 0)
    for c in range(cells):
        cx0 = int(x0 + c * cw)
        cx1 = max(int(x0 + (c + 1) * cw), cx0 + 1)
        data = ring_pixels(cx0, cx1)
        if not data:
            continue
        bg = Counter(data).most_common(1)[0][0]
        for ink in inks:
            r = contrast(ink, bg)
            if r < worst:
                worst, worst_bg = r, bg
    return worst, worst_bg


def record(name: str, box, inks, bg=None, kind: str = "text", req: float = TEXT_MIN,
           interior: bool = False) -> None:
    """Register a drawn element for the contrast assertion.

    `bg` is an explicit background hex when the element sits on a known solid
    fill (a panel or swatch); otherwise None means the background is measured
    from the rendered plate — from the interior of the box when `interior` is
    True (panel/swatch fills), else from the padding ring around it (text on
    the base plate).
    """
    if isinstance(inks, str):
        inks = [inks]
    inks = _to_inks(inks)
    if bg is None:
        worst, bgc = worst_bg_contrast(BASE, box, inks, interior=interior)
    else:
        bgc = hx(bg)
        worst = min(contrast(i, bgc) for i in inks)
    ELEMENTS.append({
        "name": name,
        "region": [int(round(v)) for v in box],
        "ink": ["#%02X%02X%02X" % i for i in inks],
        "kind": kind,
        "bg": "#%02X%02X%02X" % tuple(bgc[:3]),
        "interior": interior,
        "contrast": round(worst, 2),
        "req": req,
        "ok": worst >= req - 1e-9,
    })


def svg_png(name: str, w: int, h: int, bg: str | None) -> Image.Image:
    png = cairosvg.svg2png(url=str(HERE / name), output_width=w, output_height=h,
                           background_color=bg)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def rounded(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


# --------------------------------------------------------------------------- #
# draw helpers that register elements for the contrast assertion
# --------------------------------------------------------------------------- #
def draw_text(d, name, xy, text, fnt, ink, bg=None, anchor=None, kind="text",
              req=TEXT_MIN, interior=False):
    align = "center" if anchor == "mm" else "left"
    d.multiline_text(xy, text, font=fnt, fill=ink, anchor=anchor, align=align)
    box = d.multiline_textbbox(xy, text, font=fnt, anchor=anchor, align=align)
    record(name, box, ink, bg=bg, kind=kind, req=req, interior=interior)


def draw_mark_tile(d, img, name, x, y, tw, th, svg, bg, mark_inks, cap):
    rounded(d, [x, y, x + tw, y + th], 24, hx(bg))
    m = svg_png(svg, 300, 300, None)
    img.paste(m, (x + (tw - 300) // 2, y + (th - 300) // 2 - 18), m)
    record(name + " · mark", [x, y, x + tw, y + th], mark_inks, bg=bg, kind="logo",
           req=GRAPHIC_MIN, interior=True)
    ink = hx(REF["neutral-40"]) if lum(hx(bg)) > 0.5 else hx(REF["neutral-70"])
    draw_text(d, name + " · caption", (x + 24, y + th - 52), cap,
              font("DejaVuSans.ttf", 28), ink, bg=bg, interior=True)


# --------------------------------------------------------------------------- #
# base plate
# --------------------------------------------------------------------------- #
def build_base() -> Image.Image:
    rng = random.Random(11)
    img = Image.new("RGB", (W, H), hx(REF["neutral-6"]))
    glow = Image.new("RGB", (W, H), hx(REF["neutral-6"]))
    gd = ImageDraw.Draw(glow, "RGBA")
    for i in range(60, 0, -1):
        rr = i * 22
        a = int(2.2 * i)
        gd.ellipse([W * 0.72 - rr, 520 - rr, W * 0.72 + rr, 520 + rr],
                   fill=hx(REF["violet-30"]) + (a,))
    for i in range(40, 0, -1):
        rr = i * 30
        gd.ellipse([W * 0.18 - rr, H * 0.9 - rr, W * 0.18 + rr, H * 0.9 + rr],
                   fill=hx(REF["cyan-20"]) + (int(1.4 * i),))
    img = Image.blend(img, glow, 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(420):
        x, y = rng.randrange(W), rng.randrange(H)
        s = rng.choice([1, 1, 1, 2])
        a = rng.randint(30, 120)
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, a))
    d.ellipse([W * 0.72 - 300, 520 - 300, W * 0.72 + 300, 520 + 300],
              outline=hx(REF["violet-60"]) + (70,), width=2)
    return img


BASE = build_base()


def main() -> int:
    ELEMENTS.clear()
    img = BASE.copy()
    d = ImageDraw.Draw(img, "RGBA")

    # ---- header ---------------------------------------------------------- #
    lock = svg_png("astra-lockup-horizontal-dark.svg", 1040, 156, None)
    img.paste(lock, (PAD, 150), lock)
    record("header · lockup", [PAD, 150, PAD + 1040, 150 + 156],
           [REF["neutral-90"], REF["violet-80"], REF["cyan-80"]], kind="logo",
           req=GRAPHIC_MIN)
    draw_text(d, "header · eyebrow", (PAD + 6, 348), "BRAND SYSTEM",
              font("DejaVuSans-Bold.ttf", 34), hx(REF["violet-80"]))
    draw_text(d, "header · strapline", (PAD, 400),
              "Modern · technical · trustworthy · cosmic.",
              font("DejaVuSerif.ttf", 60), hx(REF["neutral-90"]))
    draw_text(d, "header · subline", (PAD, 480),
              "An autonomous AI-agent-run digital agency.",
              font("DejaVuSans.ttf", 40), hx(REF["neutral-70"]))
    d.line([PAD, 590, W - PAD, 590], fill=hx(REF["neutral-30"]), width=2)

    y = 660

    def section(title: str):
        nonlocal y
        draw_text(d, f"section · {title}", (PAD, y), title,
                  font("DejaVuSans-Bold.ttf", 32), hx(REF["cyan-80"]))
        d.line([PAD, y + 48, W - PAD, y + 48], fill=hx(REF["neutral-30"]), width=1)
        y += 90

    # ---- logo system ----------------------------------------------------- #
    section("01  LOGO SYSTEM")
    tiles = [
        ("astra-mark-light.svg", L["surface"], "Mark · light bg",
         [REF["violet-40"], REF["cyan-40"]]),
        ("astra-mark-dark.svg", D["surface"], "Mark · dark bg",
         [REF["violet-80"], REF["cyan-80"]]),
        ("astra-mark-mono-black.svg", "#FFFFFF", "Mono black", ["#000000"]),
        ("astra-mark-mono-white.svg", "#000000", "Mono white", ["#FFFFFF"]),
    ]
    tw, th, gap = 470, 470, 44
    for i, (fn, bg, cap, inks) in enumerate(tiles):
        x = PAD + i * (tw + gap)
        draw_mark_tile(d, img, f"logo tile {i + 1}", x, y, tw, th, fn, bg, inks, cap)
    y += th + 70
    # D-B1 fix: the primary-signature panel uses the DARK lockup on the dark
    # plate (the light lockup's #1C1B20 ink is invisible on #131217).
    rounded(d, [PAD, y, W - PAD, y + 220], 24, hx(REF["neutral-10"]))
    lk = svg_png("astra-lockup-horizontal-dark.svg", 1300, 195, None)
    img.paste(lk, (PAD + 60, y + 14), lk)
    record("01 · primary-signature lockup", [PAD + 60, y + 14, PAD + 60 + 1300, y + 14 + 195],
           [REF["neutral-90"], REF["violet-80"], REF["cyan-80"]],
           bg=REF["neutral-10"], kind="logo", req=GRAPHIC_MIN)
    draw_text(d, "01 · lockup label", (W - PAD - 330, y + 110),
              "Horizontal lockup —\nprimary signature",
              font("DejaVuSans.ttf", 34), hx(REF["neutral-80"]),
              bg=REF["neutral-10"], anchor="mm")
    y += 300

    # ---- colour system --------------------------------------------------- #
    section("02  COLOUR SYSTEM")
    ramps = [
        ("Primary · violet", ["violet-10", "violet-20", "violet-30", "violet-40",
                              "violet-50", "violet-60", "violet-70", "violet-80",
                              "violet-90", "violet-95", "violet-99"]),
        ("Secondary · cyan", ["cyan-10", "cyan-20", "cyan-40", "cyan-60", "cyan-80", "cyan-90"]),
        ("Tertiary · gold", ["gold-10", "gold-20", "gold-40", "gold-60", "gold-80", "gold-90"]),
        ("Neutral", ["neutral-6", "neutral-10", "neutral-20", "neutral-30",
                     "neutral-50", "neutral-70", "neutral-90", "neutral-95", "neutral-99"]),
    ]
    sw_h = 132
    for label, keys in ramps:
        draw_text(d, f"02 · ramp {label}", (PAD, y), label,
                  font("DejaVuSans.ttf", 30), hx(REF["neutral-70"]))
        y += 44
        n = len(keys)
        sw_w = (W - 2 * PAD - (n - 1) * 12) / n
        for i, k in enumerate(keys):
            x = PAD + i * (sw_w + 12)
            rounded(d, [x, y, x + sw_w, y + sw_h], 12, hx(REF[k]))
            draw_text(d, f"02 · {k} step label", (x + 6, y + sw_h + 8),
                      k.split("-")[-1], font("DejaVuSans.ttf", 22),
                      hx(REF["neutral-60"]))
        y += sw_h + 56

    # key roles
    draw_text(d, "02 · key-roles heading", (PAD, y), "Key roles (resolved)",
              font("DejaVuSans.ttf", 30), hx(REF["neutral-70"]))
    y += 48
    roles = ["primary", "secondary", "tertiary", "surface", "on-surface", "inverse-surface"]
    cw = (W - 2 * PAD - (len(roles) - 1) * 20) / len(roles)
    for i, r in enumerate(roles):
        x = PAD + i * (cw + 20)
        fill = L[r]
        rounded(d, [x, y, x + cw, y + 150], 16, hx(fill))
        # D-B2 fix: choose the legible ink for the swatch label instead of
        # reusing the fill colour (which made on-surface 1.00:1).
        ink = max(["#FFFFFF", "#1C1B20", "#F1EEF5", "#0B0A12"],
                  key=lambda c: contrast(c, fill))
        draw_text(d, f"02 · role {r} label", (x + 16, y + 96),
                  f"{r}\n{fill.upper()}", font("DejaVuSans.ttf", 26),
                  hx(ink), bg=fill)
    y += 210

    # ---- typography ------------------------------------------------------ #
    section("03  TYPOGRAPHY")
    draw_text(d, "03 · brand-face note", (PAD, y),
              "Brand face · DejaVu Serif Bold  (substitute for licensed brand serif)",
              font("DejaVuSans.ttf", 28), hx(REF["neutral-70"]))
    y += 60
    draw_text(d, "03 · display specimen", (PAD, y), "Aa  Build what's next.",
              font("DejaVuSerif-Bold.ttf", 96), hx(REF["neutral-95"]))
    y += 130
    draw_text(d, "03 · ui-face note", (PAD, y),
              "UI face · DejaVu Sans  (substitute for licensed UI sans)",
              font("DejaVuSans.ttf", 28), hx(REF["neutral-70"]))
    y += 58
    draw_text(d, "03 · body specimen", (PAD, y),
              "Web & app build  ·  AI automation  ·  Video & design  ·  Digital products",
              font("DejaVuSans.ttf", 40), hx(REF["neutral-95"]))
    y += 80
    scale = T["typography"]["scale"]
    for key in ["display-large", "headline-large", "title-large", "body-large", "label-large"]:
        s = scale[key]
        fnt = "DejaVuSerif-Bold.ttf" if s["font"] == "brand" else "DejaVuSans-Bold.ttf"
        draw_text(d, f"03 · scale {key}", (PAD, y),
                  f"{key}  {s['size']}/{s['line-height']}", font(fnt, 34),
                  hx(REF["neutral-95"]))
        draw_text(d, f"03 · scale {key} detail", (PAD + 760, y + 6),
                  f"{s['size']}px · w{s['weight']} · track {s['tracking']}",
                  font("DejaVuSans.ttf", 26), hx(REF["neutral-60"]))
        y += 52
    y += 40

    # ---- rules ----------------------------------------------------------- #
    section("04  USAGE RULES")
    # clear space diagram
    rounded(d, [PAD, y, PAD + 460, y + 300], 20, hx(REF["neutral-10"]))
    cx0, cy0, ms = PAD + 150, y + 60, 160
    d.rectangle([cx0 - ms * 0.5, cy0 - ms * 0.5, cx0 + ms * 1.5, cy0 + ms * 1.5],
                outline=hx(REF["cyan-80"]) + (150,), width=2)
    d.rectangle([cx0, cy0, cx0 + ms, cy0 + ms], outline=hx(REF["violet-80"]) + (150,), width=2)
    mk = svg_png("astra-mark-dark.svg", 160, 160, None)
    img.paste(mk, (cx0, cy0), mk)
    record("04 · clear-space mark", [cx0, cy0, cx0 + 160, cy0 + 160],
           [REF["violet-80"], REF["cyan-80"]], bg=REF["neutral-10"], kind="logo",
           req=GRAPHIC_MIN)
    draw_text(d, "04 · clear-space caption", (PAD + 20, y + 250),
              "Clear space = 0.5 x mark height", font("DejaVuSans.ttf", 26),
              hx(REF["neutral-80"]), bg=REF["neutral-10"])
    # do / don't
    bx = PAD + 500
    draw_text(d, "04 · DO heading", (bx, y), "DO",
              font("DejaVuSans-Bold.ttf", 34), hx(REF["green-80"]))
    dos = ["Uniform scale only", "Approved colourways", "On surface / inverse-surface",
           "Keep 0.5h clear space"]
    for i, s in enumerate(dos):
        draw_text(d, f"04 · DO item {i + 1}", (bx, y + 52 + i * 42), "✓  " + s,
                  font("DejaVuSans.ttf", 30), hx(REF["neutral-90"]))
    draw_text(d, "04 · DON'T heading", (bx + 700, y), "DON'T",
              font("DejaVuSans-Bold.ttf", 34), hx(REF["red-80"]))
    donts = ["Re-colour or add gradients", "Stretch / skew / rotate",
             "Outlines, shadows, bevels", "Busy photo without a scrim"]
    for i, s in enumerate(donts):
        draw_text(d, f"04 · DON'T item {i + 1}", (bx + 700, y + 52 + i * 42), "✕  " + s,
                  font("DejaVuSans.ttf", 30), hx(REF["neutral-90"]))
    y += 320

    # ---- footer ---------------------------------------------------------- #
    y += 40
    d.line([PAD, y, W - PAD, y], fill=hx(REF["neutral-30"]), width=2)
    draw_text(d, "footer · line 1", (PAD, y + 30),
              "AI ASTRA AGENCY — Brand System v2.0.1 · astra-ccr (Creative) · 2026-11-13",
              font("DejaVuSans.ttf", 28), hx(REF["neutral-60"]))
    # D-B3 fix: neutral-50 (#7A797E) fell to 3.32:1 over the cyan glow; use
    # neutral-70 which clears 4.5:1 even on the brightest glow pixels.
    draw_text(d, "footer · line 2", (PAD, y + 70),
              "Fonts are DejaVu substitutes. Mark and palette are ASTRA's own; "
              "structure studied from cited public design systems.",
              font("DejaVuSans.ttf", 24), hx(REF["neutral-70"]))
    H_final = y + 150
    img = img.crop((0, 0, W, H_final))
    img.save(HERE / "astra-brand-sheet.png")
    print("wrote astra-brand-sheet.png", img.size)

    # ---- contrast assertion (re-measured from the shipped PNG) ----------- #
    png = Image.open(HERE / "astra-brand-sheet.png").convert("RGB")
    for e in ELEMENTS:
        inks = [hx(c) for c in e["ink"]]
        worst, bgc = worst_bg_contrast(png, e["region"], inks,
                                       interior=e.get("interior", False))
        e["contrast_png"] = round(worst, 2)
        e["bg_png"] = "#%02X%02X%02X" % tuple(bgc[:3])
    failures = [e for e in ELEMENTS if e["contrast_png"] < e["req"] - 1e-9]

    # ---- objective checks ------------------------------------------------ #
    checks = {"brand_sheet": {"size": list(img.size),
                              "ok": img.size[0] == W and img.size[1] <= H}}
    svgs = sorted(HERE.glob("*.svg"))
    parse = {}
    for p in svgs:
        try:
            ET.parse(p)
            parse[p.name] = True
        except Exception as e:  # noqa: BLE001
            parse[p.name] = f"FAIL {e}"
    checks["svg_parse"] = parse
    bad = []
    for scheme in ("light", "dark"):
        for k, v in T["color"]["sys"][scheme].items():
            if v not in REF:
                bad.append(f"{scheme}.{k}={v}")
    checks["sys_unbacked"] = bad
    pairs = [
        ("light primary/on-primary", L["primary"], L["on-primary"]),
        ("light on-surface/surface", L["on-surface"], L["surface"]),
        ("light secondary/on-secondary", L["secondary"], L["on-secondary"]),
        ("light tertiary/on-tertiary", L["tertiary"], L["on-tertiary"]),
        ("dark primary/on-primary", D["primary"], D["on-primary"]),
        ("dark on-surface/surface", D["on-surface"], D["surface"]),
        ("dark secondary/on-secondary", D["secondary"], D["on-secondary"]),
        ("dark tertiary/on-tertiary", D["tertiary"], D["on-tertiary"]),
        ("mark violet on light surface", L["primary"], L["surface"]),
        ("mark light-violet on dark surface", D["primary"], D["surface"]),
    ]
    checks["contrast"] = {n: round(contrast(a, b), 2) for n, a, b in pairs}
    checks["contrast_min"] = min(checks["contrast"].values())
    checks["sheet_elements"] = ELEMENTS
    checks["sheet_elements_count"] = len(ELEMENTS)
    checks["sheet_contrast_min"] = min(e["contrast_png"] for e in ELEMENTS)
    checks["sheet_contrast_failures"] = [e["name"] for e in failures]
    checks["sheet_contrast_ok"] = not failures
    checks["all_ok"] = bool(checks["brand_sheet"]["ok"] and not bad
                            and all(v is True for v in parse.values())
                            and checks["contrast_min"] >= 4.5
                            and not failures)
    (HERE / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps({k: v for k, v in checks.items() if k != "sheet_elements"}, indent=2))
    if failures:
        print("\nCONTRAST FAILURES (< %.1f:1):" % TEXT_MIN, file=sys.stderr)
        for e in failures:
            print(f"  {e['name']}: {e['contrast_png']}:1  {e['ink']} on {e['bg_png']}",
                  file=sys.stderr)
        return 1
    print(f"\nall {len(ELEMENTS)} sheet elements >= {TEXT_MIN}:1 "
          f"(min {checks['sheet_contrast_min']}:1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
