#!/usr/bin/env python3
"""Prove Arabic joining + RTL ordering via HarfBuzz before we outline the wordmark."""
import uharfbuzz as hb
from pathlib import Path

F = Path(__file__).resolve().parent.parent / "fonts"
text = "أسترا تريدنغ"   # "Astra Trading" in Arabic

blob = hb.Blob.from_file_path(str(F / "IBMPlexSansArabic-SemiBold.ttf"))
face = hb.Face(blob)
font = hb.Font(face)
buf = hb.Buffer()
buf.add_str(text)
buf.direction = "rtl"
buf.script = "Arab"
buf.language = "ar"
hb.shape(font, buf)
infos = buf.glyph_infos
names = [font.glyph_to_string(i.codepoint) for i in infos]
print("text:", text)
print("glyph count:", len(infos))
print("glyphs:", names)
# Count distinct glyphs: if joining worked, several letters map to medial/final forms,
# so glyph count == char count but names differ from isolated forms.
print("distinct glyphs:", len(set(names)))
