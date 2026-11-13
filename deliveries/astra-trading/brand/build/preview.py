#!/usr/bin/env python3
"""Render an image and print an ASCII luminance map so the agent can *look* at it.

Usage: python3 preview.py <image> [cols] [rows]
Prints a character grid (dark->space, light->@) plus a colour summary.
"""
import sys
from PIL import Image
import numpy as np

RAMP = " .:-=+*#%@"


def preview(path: str, cols: int = 78, rows: int = 34):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (7, 7, 12, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    # letterbox to the requested aspect
    w, h = im.size
    target = cols / rows
    if w / h > target:
        new_h = int(w / target)
        canvas = Image.new("RGB", (w, new_h), (7, 7, 12))
        canvas.paste(im, (0, (new_h - h) // 2))
        im = canvas
    else:
        new_w = int(h * target)
        canvas = Image.new("RGB", (new_w, h), (7, 7, 12))
        canvas.paste(im, ((new_w - w) // 2, 0))
        im = canvas
    small = np.asarray(im.resize((cols, rows), Image.BOX)).astype(float)
    lum = 0.2126 * small[:, :, 0] + 0.7152 * small[:, :, 1] + 0.0722 * small[:, :, 2]
    lo, hi = lum.min(), max(lum.max(), 1)
    norm = (lum - lo) / (hi - lo + 1e-9)
    print(f"# {path}  {w}x{h}")
    for r in range(rows):
        line = "".join(RAMP[min(len(RAMP) - 1, int(norm[r, c] * len(RAMP)))] for c in range(cols))
        print("|" + line + "|")
    # colour summary
    px = np.asarray(Image.open(path).convert("RGB")).reshape(-1, 3)
    cols_uniq, counts = np.unique(px, axis=0, return_counts=True)
    order = np.argsort(-counts)[:6]
    print("# top colours:")
    for i in order:
        r, g, b = cols_uniq[i]
        print(f"#   #{r:02X}{g:02X}{b:02X}  {counts[i]*100.0/len(px):5.1f}%")


if __name__ == "__main__":
    p = sys.argv[1]
    c = int(sys.argv[2]) if len(sys.argv) > 2 else 78
    r = int(sys.argv[3]) if len(sys.argv) > 3 else 34
    preview(p, c, r)
