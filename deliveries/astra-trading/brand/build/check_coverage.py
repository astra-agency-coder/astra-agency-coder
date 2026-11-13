#!/usr/bin/env python3
"""Verify that the chosen OFL fonts actually cover the scripts we must set."""
from fontTools.ttLib import TTFont
from pathlib import Path

F = Path(__file__).resolve().parent.parent / "fonts"

LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;/%()-–—&+@#$€£¥₺"
TR = "ğĞşŞıİöÖüÜçÇâîû"
AR_BASE = "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأإئؤىة٠١٢٣٤٥٦٧٨٩"


def cov(path, chars):
    f = TTFont(path, lazy=True)
    cmap = f.getBestCmap()
    missing = [c for c in chars if ord(c) not in cmap]
    total = len(chars)
    return total - len(missing), total, missing


def arabic_shaping_ok(path):
    """Confirm the font carries the Arabic init/medi/fina feature tables."""
    f = TTFont(path, lazy=True)
    if "GSUB" not in f:
        return False, "no GSUB"
    feats = set()
    for fr in f["GSUB"].table.FeatureList.FeatureRecord:
        feats.add(fr.FeatureTag)
    need = {"init", "medi", "fina", "isol"}
    return need.issubset(feats), sorted(need - feats)


for name in ["SpaceGrotesk-var.ttf", "IBMPlexSans-var.ttf", "IBMPlexMono-Regular.ttf"]:
    p = F / name
    if not p.exists():
        print(f"MISSING {name}")
        continue
    g, t, miss = cov(p, LATIN)
    gt, tt, misst = cov(p, TR)
    print(f"{name:26s} latin {g}/{t}  turkish {gt}/{tt}  missing_tr={misst}")

for name in ["IBMPlexSansArabic-Regular.ttf", "IBMPlexSansArabic-Medium.ttf",
             "IBMPlexSansArabic-SemiBold.ttf", "IBMPlexSansArabic-Bold.ttf"]:
    p = F / name
    if not p.exists():
        print(f"MISSING {name}")
        continue
    g, t, miss = cov(p, AR_BASE)
    ok, missing_feat = arabic_shaping_ok(p)
    gl, tl, ml = cov(p, "0123456789.:/%,-+")
    print(f"{name:30s} arabic {g}/{t} missing={miss}  shaping_ok={ok} missing_feat={missing_feat}  digits {gl}/{tl}")
