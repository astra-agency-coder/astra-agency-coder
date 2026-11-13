#!/usr/bin/env python3
"""Astra Trading palette definition + WCAG validation."""
from __future__ import annotations

from brandlib import contrast, wcag_grade

# --------------------------------------------------------------------------- #
# Reference ramp
# --------------------------------------------------------------------------- #
REF = {
    # Gold — the measured element (Au)
    "gold-100": "#FBF3DA",
    "gold-200": "#F3E2AE",
    "gold-300": "#E8C766",
    "gold-400": "#D9AF3A",
    "gold-500": "#C9A227",   # brand gold
    "gold-600": "#A8851A",
    "gold-700": "#856A16",
    "gold-800": "#5C4A11",
    "gold-900": "#2E260A",

    # Violet — inherited from AI ASTRA AGENCY (sub-brand link)
    "violet-200": "#D9CBF7",
    "violet-300": "#C9B0F0",
    "violet-500": "#7C4DFF",
    "violet-700": "#5A2EA6",
    "violet-900": "#2A1650",

    # Neutrals — cool, near-black first
    "neutral-0":   "#FFFFFF",
    "neutral-3":   "#07070C",   # page background (dark-first)
    "neutral-5":   "#0C0C13",   # chart / canvas
    "neutral-8":   "#12121A",   # surface-1
    "neutral-12":  "#1B1B26",   # surface-2 / borders
    "neutral-20":  "#2A2A38",
    "neutral-40":  "#5A5F72",
    "neutral-60":  "#767C90",
    "neutral-70":  "#A9AEBF",
    "neutral-90":  "#EEF0F7",
    "neutral-100": "#14141B",   # "ink" on light surfaces

    # Semantic chart language (colour-blind-considerate)
    "bull-400":    "#16C79A",   # teal-green (deuteranopia-safe vs red)
    "bull-600":    "#0E9E79",
    "bull-700":    "#06775B",   # light-theme text variant (AA on white)
    "bear-400":    "#FF4D6D",   # rose-red
    "bear-600":    "#D92D4E",
    "flat-400":    "#8E93A6",   # grey for indecision
}

# --------------------------------------------------------------------------- #
# System roles (dark theme is the default)
# --------------------------------------------------------------------------- #
SYS = {
    "dark": {
        "background":        "neutral-3",
        "on-background":     "neutral-90",
        "surface-1":         "neutral-8",
        "surface-2":         "neutral-12",
        "on-surface":        "neutral-90",
        "on-surface-muted":  "neutral-70",
        "on-surface-subtle": "neutral-60",
        "outline":           "neutral-20",       # decorative divider only
        "outline-strong":    "neutral-40",       # interactive border (>=3:1)
        "primary":           "gold-300",
        "primary-strong":    "gold-500",
        "on-primary":        "neutral-3",
        "accent":            "violet-300",
        "bull":              "bull-400",
        "bear":              "bear-400",
        "flat":              "flat-400",
        "chart-bg":          "neutral-5",
        "error":             "bear-400",
        "success":           "bull-400",
    },
    "light": {
        "background":        "neutral-0",
        "on-background":     "neutral-100",
        "surface-1":         "#F7F7FB",
        "surface-2":         "#ECECF3",
        "on-surface":        "neutral-100",
        "on-surface-muted":  "neutral-40",
        "outline":           "#D6D6E0",
        "outline-strong":    "neutral-40",
        "primary":           "gold-700",
        "primary-strong":    "gold-700",
        "on-primary":        "neutral-0",
        "accent":            "violet-700",
        "bull":              "bull-700",
        "bear":              "bear-600",
        "flat":              "neutral-40",
        "chart-bg":          "#F2F2F7",
        "error":             "bear-600",
        "success":           "bull-600",
    },
}


def resolve(theme: str, role: str) -> str:
    v = SYS[theme][role]
    return REF.get(v, v)


# (fg_role, bg_role, theme, large_or_graphic, purpose)
TEXT_PAIRS = [
    ("on-background", "background", "dark", False, "body text on page"),
    ("on-surface", "surface-1", "dark", False, "body text on card"),
    ("on-surface", "surface-2", "dark", False, "body text on raised panel"),
    ("on-surface-muted", "background", "dark", False, "secondary text on page"),
    ("on-surface-muted", "surface-1", "dark", False, "secondary text on card"),
    ("on-surface-subtle", "background", "dark", False, "captions / axis labels"),
    ("primary", "background", "dark", False, "gold link text on page"),
    ("primary", "surface-1", "dark", False, "gold link text on card"),
    ("primary-strong", "background", "dark", False, "gold icon+label on near-black"),
    ("accent", "background", "dark", False, "violet accent text"),
    ("on-primary", "primary", "dark", False, "ink on gold button"),
    ("bull", "background", "dark", False, "bull signal text"),
    ("bull", "chart-bg", "dark", True, "bull candle/zone on chart"),
    ("bear", "background", "dark", False, "bear signal text"),
    ("bear", "chart-bg", "dark", True, "bear candle/zone on chart"),
    ("flat", "chart-bg", "dark", True, "neutral candle/zone on chart"),
    ("primary", "chart-bg", "dark", True, "gold price line on chart"),
    ("outline", "background", "dark", True, "decorative divider [exempt]"),
    ("outline-strong", "background", "dark", True, "interactive border / focus ring"),
    ("on-background", "background", "light", False, "body text on light page"),
    ("primary", "background", "light", False, "gold link on light"),
    ("bull", "background", "light", False, "bull text on light"),
    ("bear", "background", "light", False, "bear text on light"),
    ("on-primary", "primary", "light", False, "white on gold-700 button"),
]


def main() -> int:
    print(f"{'pair':52s} {'ratio':>6s}  grade")
    fails = 0
    for fg, bg, th, large, purpose in TEXT_PAIRS:
        c = contrast(resolve(th, fg), resolve(th, bg))
        exempt = "[exempt]" in purpose
        need = 3.0 if large else 4.5
        ok = c >= need or exempt
        fails += 0 if ok else 1
        flag = "" if ok else "  <<< FAIL"
        print(f"{th}:{fg} on {bg:18s} ({purpose[:26]:26s}) {c:6.2f}  "
              f"{wcag_grade(c, large)}{flag}")
    print(f"\nfailures: {fails}")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
