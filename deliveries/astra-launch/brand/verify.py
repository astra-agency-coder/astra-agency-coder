#!/usr/bin/env python3
"""Verify the brand deliverables and write VERIFY.md with the real evidence.

Checks (no mocks — every claim is measured from the files on disk):
  * every PNG opens with Pillow and `Image.verify()` passes (not corrupt)
  * every PNG is non-blank (>= 2 distinct colours) and reports its true size
  * every SVG parses as XML and has a viewBox
  * tokens.json is valid JSON and every colour.sys value aliases a colour.ref key
  * WCAG contrast for the declared text pairs

Run:  python3 verify.py    (writes VERIFY.md, exits non-zero on failure)
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(hx(a)), lum(hx(b))
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def main() -> int:
    lines: list[str] = []
    ok = True

    def w(s=""):
        lines.append(s)

    w("# Brand deliverables — verification")
    w()
    w(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} "
      f"by `brand/verify.py` (Creative / `astra-ccr`).")
    w()
    w("Every figure below was measured from the files on disk in this directory.")
    w()

    # ---- PNGs ------------------------------------------------------------ #
    w("## PNG assets — open + integrity + size")
    w()
    w("| File | Size (px) | Mode | Opens | verify() | Distinct colours |")
    w("|---|---|---|---|---|---|")
    pngs = sorted(HERE.glob("*.png"))
    for p in pngs:
        try:
            im = Image.open(p)
            size = im.size
            mode = im.mode
            im.verify()          # detects truncation/corruption
            reopened = Image.open(p).convert("RGB")
            distinct = len(set(reopened.getdata()))
            good = distinct >= 2
            if not good:
                ok = False
            w(f"| `{p.name}` | {size[0]}×{size[1]} | {mode} | yes | pass | {distinct} |")
        except Exception as e:  # noqa: BLE001
            ok = False
            w(f"| `{p.name}` | — | — | **FAIL** | {e} | — |")
    w()

    # ---- SVGs ------------------------------------------------------------ #
    w("## SVG assets — XML parse + viewBox")
    w()
    w("| File | Parses | viewBox | Root |")
    w("|---|---|---|---|")
    for p in sorted(HERE.glob("*.svg")):
        try:
            root = ET.parse(p).getroot()
            vb = root.get("viewBox")
            if not vb:
                ok = False
            w(f"| `{p.name}` | yes | `{vb}` | `{root.tag.split('}')[-1]}` |")
        except Exception as e:  # noqa: BLE001
            ok = False
            w(f"| `{p.name}` | **FAIL** | — | {e} |")
    w()

    # ---- tokens ---------------------------------------------------------- #
    w("## tokens.json — integrity")
    w()
    T = json.loads((HERE / "tokens.json").read_text())
    ref = T["color"]["ref"]
    unbacked = [f"{s}.{k}={v}" for s in ("light", "dark")
                for k, v in T["color"]["sys"][s].items() if v not in ref]
    if unbacked:
        ok = False
    w(f"- Valid JSON: **yes**")
    w(f"- `color.ref` entries: **{len(ref)}**")
    w(f"- `color.sys` values not backed by a ref token: **{len(unbacked)}** "
      f"{'(all backed — ref→sys aliasing holds)' if not unbacked else unbacked}")
    w(f"- Typography scale entries: **{len(T['typography']['scale'])}**")
    w(f"- Spacing scale steps: **{len(T['spacing']['scale'])}**")
    w()

    # ---- contrast -------------------------------------------------------- #
    w("## WCAG contrast (declared text pairs)")
    w()
    L, D = T["color"]["sys_resolved"]["light"], T["color"]["sys_resolved"]["dark"]
    pairs = [
        ("light: primary / on-primary", L["primary"], L["on-primary"], 4.5),
        ("light: on-surface / surface", L["on-surface"], L["surface"], 4.5),
        ("light: secondary / on-secondary", L["secondary"], L["on-secondary"], 4.5),
        ("light: tertiary / on-tertiary", L["tertiary"], L["on-tertiary"], 4.5),
        ("dark: primary / on-primary", D["primary"], D["on-primary"], 4.5),
        ("dark: on-surface / surface", D["on-surface"], D["surface"], 4.5),
        ("dark: secondary / on-secondary", D["secondary"], D["on-secondary"], 4.5),
        ("dark: tertiary / on-tertiary", D["tertiary"], D["on-tertiary"], 4.5),
        ("mark: violet on light surface", L["primary"], L["surface"], 3.0),
        ("mark: light-violet on dark surface", D["primary"], D["surface"], 3.0),
    ]
    w("| Pair | Ratio | Requirement | Result |")
    w("|---|---|---|---|")
    for name, a, b, req in pairs:
        r = contrast(a, b)
        passed = r >= req
        if not passed:
            ok = False
        w(f"| {name} | {r}:1 | ≥ {req}:1 | {'PASS' if passed else 'FAIL'} |")
    w()

    # ---- wordmark outline check ------------------------------------------ #
    w("## Wordmark — vector outline (no font dependency)")
    w()
    for p in sorted(HERE.glob("astra-wordmark-*.svg")):
        txt = p.read_text()
        has_path = "<path" in txt
        has_text = "<text" in txt
        w(f"- `{p.name}`: `<path>` present = **{has_path}**, "
          f"`<text>` element = **{has_text}** "
          f"({'outlined — renders without the font installed' if has_path and not has_text else 'CHECK'})")
    w()

    # ---- logo raster colour check ---------------------------------------- #
    w("## Logo raster colour verification")
    w()
    checks = {
        "logo-mark-on-light-1024.png": (("#5A2EA6"), ("#0D7D8F")),
        "logo-mark-on-dark-1024.png": (("#C9B0F0"), ("#8FDBE4")),
    }
    for fn, (c1, c2) in checks.items():
        p = HERE / fn
        if p.exists():
            px = set(Image.open(p).convert("RGB").getdata())
            w(f"- `{fn}`: contains mark violet `{c1}` = **{hx(c1) in px}**, "
              f"star cyan `{c2}` = **{hx(c2) in px}**")
    w()

    w("## Result")
    w()
    w(f"**{'ALL CHECKS PASSED' if ok else 'CHECKS FAILED — see FAIL rows above'}**")
    w()
    (HERE / "VERIFY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
