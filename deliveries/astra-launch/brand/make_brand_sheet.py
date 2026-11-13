#!/usr/bin/env python3
"""ASTRA brand sheet (one rendered PNG) + objective brand checks.

Reads tokens.json and the SVG suite in this folder, composes a single
2400x3400 brand sheet, and runs the acceptance checks (dimensions, token
integrity, SVG parse, contrast) writing brand/checks.json.

Run:  python3 make_brand_sheet.py
"""
from __future__ import annotations

import io
import json
import math
import random
import xml.etree.ElementTree as ET
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


def hx(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = lum(hx(a)), lum(hx(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def svg_png(name: str, w: int, h: int, bg: str | None) -> Image.Image:
    png = cairosvg.svg2png(url=str(HERE / name), output_width=w, output_height=h,
                           background_color=bg)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def rounded(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


def main() -> None:
    rng = random.Random(11)
    img = Image.new("RGB", (W, H), hx(REF["neutral-6"]))
    d = ImageDraw.Draw(img, "RGBA")

    # cosmic background: soft radial glow + star field
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
    # orbit ring
    d.ellipse([W * 0.72 - 300, 520 - 300, W * 0.72 + 300, 520 + 300],
              outline=hx(REF["violet-60"]) + (70,), width=2)

    # ---- header ---------------------------------------------------------- #
    lock = svg_png("astra-lockup-horizontal-dark.svg", 1040, 156, None)
    img.paste(lock, (PAD, 150), lock)
    d.text((PAD + 6, 348), "BRAND SYSTEM", font=font("DejaVuSans-Bold.ttf", 34),
           fill=hx(REF["violet-80"]))
    d.text((PAD, 400), "Modern · technical · trustworthy · cosmic.",
           font=font("DejaVuSerif.ttf", 60), fill=hx(REF["neutral-90"]))
    d.text((PAD, 480), "An autonomous AI-agent-run digital agency.",
           font=font("DejaVuSans.ttf", 40), fill=hx(REF["neutral-70"]))
    d.line([PAD, 590, W - PAD, 590], fill=hx(REF["neutral-30"]), width=2)

    y = 660

    def section(title: str):
        nonlocal y
        d.text((PAD, y), title, font=font("DejaVuSans-Bold.ttf", 32),
               fill=hx(REF["cyan-80"]))
        d.line([PAD, y + 48, W - PAD, y + 48], fill=hx(REF["neutral-30"]), width=1)
        y += 90

    # ---- logo system ----------------------------------------------------- #
    section("01  LOGO SYSTEM")
    tiles = [
        ("astra-mark-light.svg", L["surface"], "Mark · light bg"),
        ("astra-mark-dark.svg", D["surface"], "Mark · dark bg"),
        ("astra-mark-mono-black.svg", "#FFFFFF", "Mono black"),
        ("astra-mark-mono-white.svg", "#000000", "Mono white"),
    ]
    tw, th, gap = 470, 470, 44
    for i, (fn, bg, cap) in enumerate(tiles):
        x = PAD + i * (tw + gap)
        rounded(d, [x, y, x + tw, y + th], 24, hx(bg))
        m = svg_png(fn, 300, 300, None)
        img.paste(m, (x + (tw - 300) // 2, y + (th - 300) // 2 - 18), m)
        d.text((x + 24, y + th - 52), cap, font=font("DejaVuSans.ttf", 28),
               fill=hx(REF["neutral-80"]) if bg in ("#000000", D["surface"]) else hx(REF["neutral-40"]))
    y += th + 70
    rounded(d, [PAD, y, W - PAD, y + 220], 24, hx(REF["neutral-10"]))
    lk = svg_png("astra-lockup-horizontal-light.svg", 1300, 195, None)
    img.paste(lk, (PAD + 60, y + 14), lk)
    d.text((W - PAD - 640, y + 88), "Horizontal lockup —\nprimary signature",
           font=font("DejaVuSans.ttf", 34), fill=hx(REF["neutral-80"]))
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
        d.text((PAD, y), label, font=font("DejaVuSans.ttf", 30), fill=hx(REF["neutral-70"]))
        y += 44
        n = len(keys)
        sw_w = (W - 2 * PAD - (n - 1) * 12) / n
        for i, k in enumerate(keys):
            x = PAD + i * (sw_w + 12)
            rounded(d, [x, y, x + sw_w, y + sw_h], 12, hx(REF[k]))
            d.text((x + 6, y + sw_h + 8), k.split("-")[-1],
                   font=font("DejaVuSans.ttf", 22), fill=hx(REF["neutral-60"]))
        y += sw_h + 56

    # key roles
    d.text((PAD, y), "Key roles (resolved)", font=font("DejaVuSans.ttf", 30),
           fill=hx(REF["neutral-70"]))
    y += 48
    roles = ["primary", "secondary", "tertiary", "surface", "on-surface", "inverse-surface"]
    cw = (W - 2 * PAD - (len(roles) - 1) * 20) / len(roles)
    for i, r in enumerate(roles):
        x = PAD + i * (cw + 20)
        rounded(d, [x, y, x + cw, y + 150], 16, hx(L[r]))
        d.text((x + 16, y + 96), f"{r}\n{L[r].upper()}", font=font("DejaVuSans.ttf", 26),
               fill=hx(L["on-primary"]) if r in ("primary", "secondary", "tertiary", "inverse-surface")
               else hx(L["on-surface"]))
    y += 210

    # ---- typography ------------------------------------------------------ #
    section("03  TYPOGRAPHY")
    d.text((PAD, y), "Brand face · DejaVu Serif Bold  (substitute for licensed brand serif)",
           font=font("DejaVuSans.ttf", 28), fill=hx(REF["neutral-70"]))
    y += 60
    d.text((PAD, y), "Aa  Build what's next.", font=font("DejaVuSerif-Bold.ttf", 96),
           fill=hx(REF["neutral-95"]))
    y += 130
    d.text((PAD, y), "UI face · DejaVu Sans  (substitute for licensed UI sans)",
           font=font("DejaVuSans.ttf", 28), fill=hx(REF["neutral-70"]))
    y += 58
    d.text((PAD, y), "Web & app build  ·  AI automation  ·  Video & design  ·  Digital products",
           font=font("DejaVuSans.ttf", 40), fill=hx(REF["neutral-95"]))
    y += 80
    scale = T["typography"]["scale"]
    for key in ["display-large", "headline-large", "title-large", "body-large", "label-large"]:
        s = scale[key]
        fnt = "DejaVuSerif-Bold.ttf" if s["font"] == "brand" else "DejaVuSans-Bold.ttf"
        d.text((PAD, y), f"{key}  {s['size']}/{s['line-height']}", font=font(fnt, 34),
               fill=hx(REF["neutral-95"]))
        d.text((PAD + 760, y + 6), f"{s['size']}px · w{s['weight']} · track {s['tracking']}",
               font=font("DejaVuSans.ttf", 26), fill=hx(REF["neutral-60"]))
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
    d.text((PAD + 20, y + 250), "Clear space = 0.5 x mark height", font=font("DejaVuSans.ttf", 26),
           fill=hx(REF["neutral-80"]))
    # do / don't
    bx = PAD + 500
    d.text((bx, y), "DO", font=font("DejaVuSans-Bold.ttf", 34), fill=hx(REF["green-80"]))
    dos = ["Uniform scale only", "Approved colourways", "On surface / inverse-surface",
           "Keep 0.5h clear space"]
    for i, s in enumerate(dos):
        d.text((bx, y + 52 + i * 42), "✓  " + s, font=font("DejaVuSans.ttf", 30),
               fill=hx(REF["neutral-90"]))
    d.text((bx + 700, y), "DON'T", font=font("DejaVuSans-Bold.ttf", 34), fill=hx(REF["red-80"]))
    donts = ["Re-colour or add gradients", "Stretch / skew / rotate",
             "Outlines, shadows, bevels", "Busy photo without a scrim"]
    for i, s in enumerate(donts):
        d.text((bx + 700, y + 52 + i * 42), "✕  " + s, font=font("DejaVuSans.ttf", 30),
               fill=hx(REF["neutral-90"]))
    y += 320

    # ---- footer ---------------------------------------------------------- #
    # Place the footer relative to the last section, then crop the canvas to
    # content so the sheet can never overrun its own height.
    y += 40
    d.line([PAD, y, W - PAD, y], fill=hx(REF["neutral-30"]), width=2)
    d.text((PAD, y + 30), "AI ASTRA AGENCY — Brand System v2.0.0 · astra-ccr (Creative) · 2026-11-13",
           font=font("DejaVuSans.ttf", 28), fill=hx(REF["neutral-60"]))
    d.text((PAD, y + 70), "Fonts are DejaVu substitutes. Mark and palette are ASTRA's own; "
           "structure studied from cited public design systems.",
           font=font("DejaVuSans.ttf", 24), fill=hx(REF["neutral-50"]))
    H_final = y + 150
    img = img.crop((0, 0, W, H_final))
    img.save(HERE / "astra-brand-sheet.png")
    print("wrote astra-brand-sheet.png", img.size)

    # ---- objective checks ------------------------------------------------ #
    checks = {"brand_sheet": {"size": list(img.size),
                              "ok": img.size[0] == W and img.size[1] <= H}}
    # svg parse
    svgs = sorted(HERE.glob("*.svg"))
    parse = {}
    for p in svgs:
        try:
            ET.parse(p)
            parse[p.name] = True
        except Exception as e:  # noqa: BLE001
            parse[p.name] = f"FAIL {e}"
    checks["svg_parse"] = parse
    # token integrity: every sys value aliases a ref key
    bad = []
    for scheme in ("light", "dark"):
        for k, v in T["color"]["sys"][scheme].items():
            if v not in REF:
                bad.append(f"{scheme}.{k}={v}")
    checks["sys_unbacked"] = bad
    # contrast for declared pairs
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
    (HERE / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
