#!/usr/bin/env python3
"""Tiny SVG canvas with a text engine (HarfBuzz outlines) and a contrast gate.

Every text element drawn on the canvas is registered together with the fill
colour *and* the local background it sits on, so the sheet can prove WCAG AA
for each pair it actually renders.
"""
from __future__ import annotations

from brandlib import text_path_d, contrast


class Canvas:
    def __init__(self, w: float, h: float, bg: str):
        self.w, self.h, self.bg = w, h, bg
        self.parts: list[str] = []
        self.elements: list[dict] = []

    # ---- primitives ------------------------------------------------------ #
    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1.0, rx=0, op=None):
        s = f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"'
        s += f' rx="{rx:.2f}"' if rx else ""
        s += f' fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw:.2f}"'
        if op is not None:
            s += f' opacity="{op}"'
        self.parts.append(s + "/>")

    def line(self, x1, y1, x2, y2, stroke, sw=1.0, dash=None, op=None):
        s = (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
             f'stroke="{stroke}" stroke-width="{sw:.2f}"')
        if dash:
            s += f' stroke-dasharray="{dash}"'
        if op is not None:
            s += f' opacity="{op}"'
        self.parts.append(s + "/>")

    def path(self, d, fill="none", stroke=None, sw=1.0):
        s = f'<path d="{d}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round"'
        self.parts.append(s + "/>")

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1.0):
        s = f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw:.2f}"'
        self.parts.append(s + "/>")

    def raw(self, svg_fragment: str):
        self.parts.append(svg_fragment)

    # ---- text (outlines) ------------------------------------------------- #
    def text(self, x, y, s, font, size, fill, weight=None, direction="ltr",
             script=None, language=None, anchor="start", tracking=0.0,
             bg=None, purpose="", large=False, register=True, opacity=None):
        d, w, bbox = text_path_d(s, font, size, weight=weight, direction=direction,
                                 script=script, language=language, tracking=tracking)
        dx = {"start": 0.0, "middle": -w / 2.0, "end": -w}[anchor]
        op = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(
            f'<g transform="translate({x + dx:.3f} {y:.3f})" fill="{fill}"{op}>{d}</g>')
        if register:
            self.elements.append({
                "text": s, "font": font, "size": size, "fill": fill,
                "bg": bg or self.bg, "purpose": purpose, "large": large,
                "ratio": contrast(fill, bg or self.bg),
            })
        return w

    def text_width(self, s, font, size, weight=None, direction="ltr", script=None,
                   language=None, tracking=0.0):
        _d, w, _b = text_path_d(s, font, size, weight=weight, direction=direction,
                                script=script, language=language, tracking=tracking)
        return w

    # ---- output ---------------------------------------------------------- #
    def svg(self, title="Astra Trading — brand sheet") -> str:
        body = "".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w:.0f} '
                f'{self.h:.0f}" width="{self.w:.0f}" height="{self.h:.0f}" '
                f'role="img" aria-label="{title}"><title>{title}</title>'
                f'<rect width="{self.w:.0f}" height="{self.h:.0f}" fill="{self.bg}"/>'
                f'{body}</svg>')

    def contrast_failures(self, min_ratio=4.5, min_large=3.0):
        bad = []
        for e in self.elements:
            need = min_large if e["large"] else min_ratio
            if e["ratio"] < need:
                bad.append(e)
        return bad
