#!/usr/bin/env python3
"""ASTRA brand identity builder (Creative dept / astra-ccr).

One geometry source drives every output, so the SVG suite and the raster
renders cannot drift apart. The wordmark is converted to vector outlines with
fontTools, so the logos carry no font dependency.

Run:  python3 build_brand.py
Writes: *.svg, *.png, tokens.json, BRAND.md  (all in this directory)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cairosvg
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent

FONTS = {
    "serif-bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "sans-bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
_font_cache: dict[str, TTFont] = {}


# --------------------------------------------------------------------------- #
# Design tokens — single source of truth. Every system value aliases a ref value.
# --------------------------------------------------------------------------- #
TOKENS = {
    "meta": {
        "name": "AI ASTRA AGENCY — Brand & Design Tokens",
        "version": "2.0.1",
        "owner": "astra-ccr (Creative)",
        "date": "2026-11-13",
        "structure_studied_from": [
            "https://m3.material.io/foundations/design-tokens/overview",
            "https://m3.material.io/styles/color/roles",
            "https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-ref-palette.scss",
            "https://carbondesignsystem.com/elements/color/overview/",
            "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
            "https://support.google.com/youtube/answer/72431",
        ],
        "note": "Two-tier token model (ref ramp -> system roles), the same shape as "
                "published Material 3 / Carbon taxonomies. Palette and scale values "
                "are ASTRA's own. Every color.sys value resolves to a color.ref entry.",
    },
    "color": {
        "ref": {
            # violet — primary brand ramp
            "violet-10": "#1A0B2E", "violet-20": "#2D1450", "violet-30": "#41206F",
            "violet-40": "#5A2EA6", "violet-50": "#7643CC", "violet-60": "#9163E3",
            "violet-70": "#AD88EA", "violet-80": "#C9B0F0", "violet-90": "#E4D7F7",
            "violet-95": "#F2ECFB", "violet-99": "#FBF8FF",
            # cyan — secondary / star
            "cyan-10": "#032329", "cyan-20": "#0D4F5C", "cyan-40": "#0D7D8F",
            "cyan-60": "#39B5C6", "cyan-80": "#8FDBE4", "cyan-90": "#C6EEF3",
            # gold — tertiary accent
            "gold-10": "#3D2A00", "gold-20": "#6E4D00", "gold-40": "#9A6A00",
            "gold-60": "#E0A52A", "gold-80": "#F5D488", "gold-90": "#FBE9C0",
            # neutral
            "neutral-0": "#000000", "neutral-6": "#0B0A12", "neutral-10": "#131217",
            "neutral-12": "#1C1B20", "neutral-17": "#2B2930", "neutral-20": "#313036",
            "neutral-30": "#47464C", "neutral-40": "#5F5E63", "neutral-50": "#7A797E",
            "neutral-60": "#949499", "neutral-70": "#AFAFB4", "neutral-80": "#CBC9CF",
            "neutral-90": "#E6E1E9", "neutral-95": "#F1EEF5", "neutral-98": "#F8F6FA",
            "neutral-99": "#FDFBFE", "neutral-100": "#FFFFFF",
            # state
            "red-40": "#B3261E", "red-80": "#F2B8B5",
            "green-40": "#146C2E", "green-80": "#A6E7B5",
        },
        "sys": {
            "light": {
                "primary": "violet-40", "on-primary": "neutral-100",
                "primary-container": "violet-90", "on-primary-container": "violet-20",
                "secondary": "cyan-40", "on-secondary": "neutral-100",
                "secondary-container": "cyan-90", "on-secondary-container": "cyan-10",
                "tertiary": "gold-40", "on-tertiary": "neutral-100",
                "tertiary-container": "gold-90", "on-tertiary-container": "gold-10",
                "error": "red-40", "on-error": "neutral-100", "error-container": "red-80",
                "success": "green-40", "on-success": "neutral-100",
                "background": "neutral-99", "on-background": "neutral-12",
                "surface": "neutral-99", "on-surface": "neutral-12",
                "surface-variant": "neutral-90", "on-surface-variant": "neutral-30",
                "outline": "neutral-50", "outline-variant": "neutral-80",
                "inverse-surface": "neutral-20", "inverse-on-surface": "neutral-95",
                "inverse-primary": "violet-80",
            },
            "dark": {
                "primary": "violet-80", "on-primary": "violet-20",
                "primary-container": "violet-30", "on-primary-container": "violet-90",
                "secondary": "cyan-80", "on-secondary": "cyan-10",
                "secondary-container": "cyan-20", "on-secondary-container": "cyan-90",
                "tertiary": "gold-80", "on-tertiary": "gold-10",
                "tertiary-container": "gold-20", "on-tertiary-container": "gold-90",
                "error": "red-80", "on-error": "gold-10", "error-container": "red-40",
                "success": "green-80", "on-success": "violet-10",
                "background": "neutral-6", "on-background": "neutral-90",
                "surface": "neutral-6", "on-surface": "neutral-90",
                "surface-variant": "neutral-30", "on-surface-variant": "neutral-80",
                "outline": "neutral-60", "outline-variant": "neutral-30",
                "inverse-surface": "neutral-90", "inverse-on-surface": "neutral-20",
                "inverse-primary": "violet-40",
            },
        },
    },
    "typography": {
        "font": {
            "brand": {"family": "DejaVu Serif", "role": "headlines, logo lockups",
                      "substitute_for": "licensed brand serif (high-contrast transitional)",
                      "weights": {"regular": 400, "bold": 700}},
            "plain": {"family": "DejaVu Sans", "role": "UI, body, captions",
                      "substitute_for": "licensed UI sans", "weights": {"regular": 400, "bold": 700}},
            "mono": {"family": "DejaVu Sans Mono", "role": "code, data", "weights": {"regular": 400}},
        },
        "scale": {
            "display-large":  {"size": 57, "line-height": 64, "tracking": -0.5, "weight": 700, "font": "brand"},
            "display-medium": {"size": 45, "line-height": 52, "tracking": -0.25, "weight": 700, "font": "brand"},
            "display-small":  {"size": 36, "line-height": 44, "tracking": 0.0,  "weight": 700, "font": "brand"},
            "headline-large": {"size": 32, "line-height": 40, "tracking": 0.0,  "weight": 700, "font": "brand"},
            "headline-medium":{"size": 28, "line-height": 36, "tracking": 0.0,  "weight": 700, "font": "brand"},
            "headline-small": {"size": 24, "line-height": 32, "tracking": 0.0,  "weight": 700, "font": "brand"},
            "title-large":    {"size": 22, "line-height": 28, "tracking": 0.0,  "weight": 700, "font": "plain"},
            "title-medium":   {"size": 16, "line-height": 24, "tracking": 0.15, "weight": 700, "font": "plain"},
            "title-small":    {"size": 14, "line-height": 20, "tracking": 0.1,  "weight": 700, "font": "plain"},
            "body-large":     {"size": 16, "line-height": 24, "tracking": 0.5,  "weight": 400, "font": "plain"},
            "body-medium":    {"size": 14, "line-height": 20, "tracking": 0.25, "weight": 400, "font": "plain"},
            "body-small":     {"size": 12, "line-height": 16, "tracking": 0.4,  "weight": 400, "font": "plain"},
            "label-large":    {"size": 14, "line-height": 20, "tracking": 0.1,  "weight": 700, "font": "plain"},
            "label-medium":   {"size": 12, "line-height": 16, "tracking": 0.5,  "weight": 700, "font": "plain"},
            "label-small":    {"size": 11, "line-height": 16, "tracking": 0.5,  "weight": 700, "font": "plain"},
        },
    },
    "spacing": {"base": 4, "scale": {"0": 0, "1": 4, "2": 8, "3": 12, "4": 16, "5": 24,
                                     "6": 32, "7": 48, "8": 64, "9": 96, "10": 128}},
    "radius": {"scale": {"none": 0, "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 28, "full": 9999}},
    "breakpoints": {"compact": 0, "medium": 600, "expanded": 905, "large": 1240, "xlarge": 1440},
}


def resolve_sys(scheme: str) -> dict[str, str]:
    """Resolve system roles to hex via the ref ramp (the two-tier model)."""
    ref = TOKENS["color"]["ref"]
    return {k: ref[v] for k, v in TOKENS["color"]["sys"][scheme].items()}


# --------------------------------------------------------------------------- #
# Vector geometry
# --------------------------------------------------------------------------- #
MARK_VB = 512

# "A" as a single chevron polygon: outer apex -> outer baseline -> inner baseline
# -> inner apex -> inner baseline -> outer baseline.
A_CHEVRON = ("M 256,56 L 480,456 L 400,456 L 256,236 L 112,456 L 32,456 Z")


def star_path(cx: float, cy: float, r_out: float, r_in: float,
              points: int = 4, rot: float = -90.0) -> str:
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * (180.0 / points))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"


# The star sits in the counter (the opening) of the A.
STAR = star_path(256, 330, 58, 18)


def _font(key: str) -> TTFont:
    if key not in _font_cache:
        _font_cache[key] = TTFont(FONTS[key])
    return _font_cache[key]


def text_to_path(font_key: str, text: str, size: float, tracking: float = 0.0):
    """Outline `text` to an SVG path string; return (d, advance, bbox)."""
    font = _font(font_key)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upem = font["head"].unitsPerEm
    scale = size / upem
    parts, x = [], 0.0
    xmin = ymin = 1e9
    xmax = ymax = -1e9
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            x += size * 0.5
            continue
        g = gs[gname]
        pen = SVGPathPen(gs)
        g.draw(TransformPen(pen, Transform(scale, 0, 0, -scale, x, 0)))
        d = pen.getCommands()
        if d:
            parts.append(d)
        bp = BoundsPen(gs)
        g.draw(TransformPen(bp, Transform(scale, 0, 0, -scale, x, 0)))
        if bp.bounds:
            xmin, ymin = min(xmin, bp.bounds[0]), min(ymin, bp.bounds[1])
            xmax, ymax = max(xmax, bp.bounds[2]), max(ymax, bp.bounds[3])
        x += g.width * scale + tracking
    return " ".join(parts), x, (xmin, ymin, xmax, ymax)


# --------------------------------------------------------------------------- #
# SVG composers
# --------------------------------------------------------------------------- #
def mark_svg(chevron: str, star: str, bg: str | None = None, size: int = MARK_VB) -> str:
    bg_rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" role="img" aria-label="AI ASTRA AGENCY mark">'
        f'<title>AI ASTRA AGENCY mark</title>{bg_rect}'
        f'<path d="{A_CHEVRON}" fill="{chevron}"/>'
        f'<path d="{STAR}" fill="{star}"/></svg>'
    )


def lockup_svg(chevron: str, star: str, text_fill: str, name: str = "AI ASTRA AGENCY",
               size: float = 92.0, tracking: float = 4.0, mark_h: float = 150.0,
               gap: float = 46.0, pad: float = 12.0) -> str:
    d, adv, (xmin, ymin, xmax, ymax) = text_to_path("serif-bold", name, size, tracking)
    text_w = xmax - xmin
    text_h = ymax - ymin
    mark_scale = mark_h / MARK_VB
    total_w = pad * 2 + mark_h + gap + text_w
    total_h = pad * 2 + mark_h
    baseline_y = pad + (mark_h + text_h) / 2 - ymin  # vertically centre text on mark
    tx = pad + mark_h + gap - xmin
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_w:.1f} {total_h:.1f}" '
        f'width="{total_w:.1f}" height="{total_h:.1f}" '
        f'role="img" aria-label="AI ASTRA AGENCY logo">'
        f'<title>AI ASTRA AGENCY logo</title>'
        f'<g transform="translate({pad},{pad}) scale({mark_scale:.5f})">'
        f'<path d="{A_CHEVRON}" fill="{chevron}"/><path d="{STAR}" fill="{star}"/></g>'
        f'<path d="{d}" transform="translate({tx:.2f},{baseline_y:.2f})" fill="{text_fill}"/>'
        f'</svg>'
    )


def write(name: str, content: str) -> Path:
    p = HERE / name
    p.write_text(content, encoding="utf-8")
    return p


def raster(svg: str, png_name: str, w: int, h: int, bg: str | None) -> Path:
    p = HERE / png_name
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(p),
                     output_width=w, output_height=h, background_color=bg)
    return p


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def main() -> None:
    L, D = resolve_sys("light"), resolve_sys("dark")

    # ---- tokens.json ---------------------------------------------------- #
    tokens = json.loads(json.dumps(TOKENS))
    tokens["color"]["sys_resolved"] = {"light": L, "dark": D}
    tokens["brand"] = {
        "name": "AI ASTRA AGENCY",
        "tagline": "Build what's next.",
        "positioning": "An autonomous AI-agent-run digital agency.",
        "tone": ["modern", "technical", "trustworthy", "cosmic"],
        "logo": {
            "mark": "A chevron (the letter A) with a four-point star in its counter.",
            "clear_space": "0.5 x mark height on every side",
            "min_size_px": {"mark": 24, "favicon": 16, "lockup_height": 28},
        },
        "services": ["Web & app build", "AI automation", "Video & design", "Digital products"],
    }
    write("tokens.json", json.dumps(tokens, indent=2) + "\n")

    # ---- logo suite (SVG) ----------------------------------------------- #
    # Mark, light background (violet A, cyan star)
    write("astra-mark-light.svg", mark_svg(L["primary"], L["secondary"]))
    # Mark, dark background (light-violet A, light-cyan star)
    write("astra-mark-dark.svg", mark_svg(D["primary"], D["secondary"]))
    # Mono variants
    write("astra-mark-mono-black.svg", mark_svg("#000000", "#000000"))
    write("astra-mark-mono-white.svg", mark_svg("#FFFFFF", "#FFFFFF"))
    # Primary mark alias (light) for convenience
    write("astra-mark.svg", mark_svg(L["primary"], L["secondary"]))

    # Horizontal lockups
    write("astra-lockup-horizontal-light.svg",
          lockup_svg(L["primary"], L["secondary"], L["on-surface"]))
    write("astra-lockup-horizontal-dark.svg",
          lockup_svg(D["primary"], D["secondary"], D["on-surface"]))
    # Wordmark only (no mark)
    d, adv, (xmin, ymin, xmax, ymax) = text_to_path("serif-bold", "AI ASTRA AGENCY", 92, 4.0)
    write("astra-wordmark-light.svg",
          f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{xmin:.1f} {ymin:.1f} '
          f'{xmax - xmin:.1f} {ymax - ymin:.1f}" width="{xmax - xmin:.1f}" '
          f'height="{ymax - ymin:.1f}" role="img" aria-label="AI ASTRA AGENCY">'
          f'<path d="{d}" fill="{L["on-surface"]}"/></svg>')
    write("astra-wordmark-dark.svg",
          f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{xmin:.1f} {ymin:.1f} '
          f'{xmax - xmin:.1f} {ymax - ymin:.1f}" width="{xmax - xmin:.1f}" '
          f'height="{ymax - ymin:.1f}" role="img" aria-label="AI ASTRA AGENCY">'
          f'<path d="{d}" fill="{D["on-surface"]}"/></svg>')

    # ---- logo raster renders (PNG) -------------------------------------- #
    mk_l = mark_svg(L["primary"], L["secondary"])
    mk_d = mark_svg(D["primary"], D["secondary"])
    lock_l = lockup_svg(L["primary"], L["secondary"], L["on-surface"])
    lock_d = lockup_svg(D["primary"], D["secondary"], D["on-surface"])

    raster(mk_l, "logo-mark-light-1024.png", 1024, 1024, None)
    raster(mk_d, "logo-mark-dark-1024.png", 1024, 1024, None)
    raster(mark_svg(L["primary"], L["secondary"]), "logo-mark-on-light-1024.png", 1024, 1024, L["surface"])
    raster(mark_svg(D["primary"], D["secondary"]), "logo-mark-on-dark-1024.png", 1024, 1024, D["surface"])
    raster(mark_svg("#000000", "#000000"), "logo-mark-mono-black-1024.png", 1024, 1024, "#FFFFFF")
    raster(mark_svg("#FFFFFF", "#FFFFFF"), "logo-mark-mono-white-1024.png", 1024, 1024, "#000000")
    raster(lock_l, "logo-lockup-light-2000x300.png", 2000, 300, L["surface"])
    raster(lock_d, "logo-lockup-dark-2000x300.png", 2000, 300, D["surface"])
    raster(lock_l, "logo-lockup-light-transparent-2000x300.png", 2000, 300, None)
    raster(lock_d, "logo-lockup-dark-transparent-2000x300.png", 2000, 300, None)

    print("brand assets written to", HERE)


if __name__ == "__main__":
    main()
