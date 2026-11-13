#!/usr/bin/env python3
"""Astra Trading brand build library.

Pure-stdlib + Pillow/fontTools/uharfbuzz helpers:
  * WCAG relative-luminance contrast math
  * HarfBuzz shaping -> SVG outline paths (RTL/LTR, any OFL font)
  * parametric "Ingot A" mark geometry -> SVG path data
Nothing here writes files; build_brand.py does.
"""
from __future__ import annotations

import functools
import math
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = Path(__file__).resolve().parent.parent / "fonts"


# --------------------------------------------------------------------------- #
# Colour
# --------------------------------------------------------------------------- #
def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore


def rel_luminance(h: str) -> float:
    r, g, b = ( _srgb_to_lin(c) for c in hex_to_rgb(h) )
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def wcag_grade(ratio: float, large: bool = False) -> str:
    """AA needs 3.0 for large text / graphics, 4.5 for normal text. AAA 7/4.5."""
    if ratio >= 7.0 or (large and ratio >= 4.5):
        return "AAA"
    if ratio >= 4.5 or (large and ratio >= 3.0):
        return "AA"
    if large and ratio >= 3.0:
        return "AA-large"
    return "FAIL"


# --------------------------------------------------------------------------- #
# Fonts: variable instancing + HarfBuzz shaping -> SVG outlines
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=32)
def _load(path_str: str, weight: int | None):
    """Return (static_bytes, TTFont, glyphSet, upem).

    Variable fonts are pinned to a single `weight` and re-serialised to static
    bytes so HarfBuzz shaping and the fontTools outliner operate on the exact
    same font (no advance/outline mismatch).
    """
    font = TTFont(path_str)
    if weight is not None and "fvar" in font:
        axes = {a.axisTag: weight for a in font["fvar"].axes if a.axisTag == "wght"}
        if axes:
            font = instancer.instantiateVariableFont(font, axes, inplace=False,
                                                     updateFontNames=False)
    import io
    buf = io.BytesIO()
    font.save(buf)
    static = buf.getvalue()
    # reload a clean copy for outlining from the serialised static bytes
    font2 = TTFont(io.BytesIO(static))
    upem = font2["head"].unitsPerEm
    return static, font2, font2.getGlyphSet(), upem


def shape(text: str, font_file: str, weight: int | None = None,
          direction: str = "ltr", script: str | None = None,
          language: str | None = None):
    """Shape `text`; return (glyph_names, xs, ys, advances, upem)."""
    static, _font, _gs, upem = _load(str(FONTS / font_file), weight)
    face = hb.Face(static)
    hbfont = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = direction
    if script:
        buf.script = script
    if language:
        buf.language = language
    hb.shape(hbfont, buf)
    names, xs, ys, adv = [], [], [], []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        names.append(hbfont.glyph_to_string(info.codepoint))
        xs.append(pos.x_offset)
        ys.append(pos.y_offset)
        adv.append(pos.x_advance)
    return names, xs, ys, adv, upem


def text_path_d(text: str, font_file: str, size: float, weight: int | None = None,
                direction: str = "ltr", script: str | None = None,
                language: str | None = None, tracking: float = 0.0):
    """Return (path_d, width, bbox) where bbox = (x0,y0,x1,y1) in SVG user units.

    Origin is the baseline start; +y is *down* (SVG). `tracking` is extra
    advance per glyph in px.
    """
    _static, font, gs, upem = _load(str(FONTS / font_file), weight)
    names, xs, ys, adv, upem = shape(text, font_file, weight, direction, script, language)
    scale = size / upem
    pen_x = 0.0
    parts: list[str] = []
    all_pts: list[tuple[float, float]] = []
    for i, name in enumerate(names):
        gname = name
        if gname not in gs:
            gname = ".notdef"
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}")
        try:
            gs[gname].draw(pen)
        except Exception:
            pass
        d = pen.getCommands()
        ox = (pen_x + xs[i]) * scale
        oy = -ys[i] * scale
        # per-glyph transform: scale + y-flip, then translate
        if d:
            parts.append(f'<g transform="translate({ox:.3f} {oy:.3f}) scale({scale:.6f} {-scale:.6f})"><path d="{d}"/></g>')
            # track extents cheaply via glyph bounds
            try:
                bp = BoundsPen(gs)
                gs[gname].draw(bp)
                gb = bp.bounds  # font units, y-up
                if gb:
                    x0, y0, x1, y1 = gb
                    for (px, py) in ((x0, y0), (x1, y1), (x0, y1), (x1, y0)):
                        all_pts.append((ox + px * scale, oy - py * scale))
            except Exception:
                pass
        pen_x += adv[i] + tracking * upem
    width = pen_x * scale
    if all_pts:
        bbox = (min(p[0] for p in all_pts), min(p[1] for p in all_pts),
                max(p[0] for p in all_pts), max(p[1] for p in all_pts))
    else:
        bbox = (0.0, 0.0, width, 0.0)
    return "".join(parts), width, bbox


def text_metrics(text: str, font_file: str, size: float, weight: int | None = None,
                 direction: str = "ltr", script: str | None = None,
                 language: str | None = None, tracking: float = 0.0):
    """Return (width, bbox) without building path data (fast for layout)."""
    names, xs, ys, adv, upem = shape(text, font_file, weight, direction, script, language)
    scale = size / upem
    pen_x = sum(adv) + tracking * upem * len(names)
    return pen_x * scale, None


def advance_width(text: str, font_file: str, size: float, weight: int | None = None,
                  direction: str = "ltr", script: str | None = None,
                  language: str | None = None, tracking: float = 0.0) -> float:
    w, _ = text_metrics(text, font_file, size, weight, direction, script, language, tracking)
    return w


# --------------------------------------------------------------------------- #
# The mark: "The Ingot A"  (parametric, in a 0..S x 0..S box)
# --------------------------------------------------------------------------- #
_GEOM_CACHE: dict[float, dict] = {}


def _poly(coords, u):
    return [(x * u, y * u) for (x, y) in coords]


def _poly_to_d(poly, holes=()):
    def ring(pts):
        return ("M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z")
    return " ".join(ring(poly.exterior.coords) for _ in [0]) if hasattr(poly, "exterior") \
        else "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in poly) + " Z"


def ingot_a_paths(S: float = 512.0):
    """Return dict layer -> svg path `d` for "The Ingot A", in a 0..S box.

    Built with exact boolean geometry (shapely), so the letterform is provably
    an "A": a diagonal left leg + a vertical right leg joined at the apex,
    with a horizontal crossbar that runs past the right leg as a gauge tick.
    All edges are straight — no curve commands.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    u = S / 512.0
    # ---- left leg: parallelogram centred on the line (300,72)->(96,452), t=92
    left = Polygon(_poly([(259.5, 50.2), (340.5, 93.8), (136.5, 473.8), (55.5, 430.2)], u))
    # ---- right leg: vertical bar (the bullion), x 346..438
    right = Polygon(_poly([(346, 66), (438, 66), (438, 452), (346, 452)], u))
    # ---- crossbar / gauge tick: spans both legs and runs past the right leg
    bar = Polygon(_poly([(178, 296), (492, 296), (492, 338), (178, 338)], u))
    a = unary_union([left, right, bar])
    # ---- facet: bright top band on the right leg (measured element highlight)
    facet = Polygon(_poly([(346, 66), (438, 66), (438, 120), (346, 120)], u))

    def d(geom):
        g = geom if geom.geom_type == "Polygon" else list(geom.geoms)[0]
        return _poly_to_d(g)

    return {"a": d(a), "facet": d(facet)}


def ingot_a_svg(size: int, fill_map: dict[str, str], bg: str | None = None,
                title: str = "Astra Trading") -> str:
    P = ingot_a_paths(float(size))
    body = "".join(
        f'<path d="{P[k]}" fill="{fill_map[k]}" fill-rule="evenodd"/>'
        for k in ("a", "facet") if k in fill_map
    )
    rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
            f'width="{size}" height="{size}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{rect}{body}</svg>')
