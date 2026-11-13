#!/usr/bin/env python3
"""Crop an image region and ASCII-preview it. Usage:
   python3 crop_preview.py img x y w h [cols rows]"""
import sys
from PIL import Image
from preview import preview

img = sys.argv[1]
x, y, w, h = (int(v) for v in sys.argv[2:6])
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 110
rows = int(sys.argv[7]) if len(sys.argv) > 7 else 34
im = Image.open(img).crop((x, y, x + w, y + h))
im.save("/tmp/_crop.png")
preview("/tmp/_crop.png", cols, rows)
