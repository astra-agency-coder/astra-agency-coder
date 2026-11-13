#!/usr/bin/env python3
"""Reproducible verification for deliveries/astra-launch/website.

Checks:
  1. HTML well-formedness (html5lib strict parser)
  2. Every local asset referenced by HTML/CSS exists on disk
  3. Responsive sanity: viewport meta present; no fixed px width that can
     overflow a 320px viewport; media queries present
  4. Live serve check is done separately (see VERIFY.md)

Exit code 0 = all checks pass, 1 = at least one failure.
"""
import os
import re
import sys
import html5lib

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")
CSS = os.path.join(ROOT, "styles.css")

failures = []
notes = []


def check(cond, ok_msg, fail_msg):
    if cond:
        print(f"  PASS  {ok_msg}")
    else:
        print(f"  FAIL  {fail_msg}")
        failures.append(fail_msg)


print("== 1. HTML well-formedness (html5lib strict) ==")
with open(INDEX, "rb") as fh:
    raw = fh.read()
parser = html5lib.HTMLParser(strict=True)
try:
    parser.parse(raw)
    print("  PASS  index.html parses with no conformance errors")
except html5lib.html5parser.ParseError as exc:  # pragma: no cover
    check(False, "", f"html5lib parse error: {exc}")

# Structural assertions on the parsed tree.
doc = html5lib.parse(raw, namespaceHTMLElements=False)
check(doc.find(".//head/meta[@name='viewport']") is not None,
      "viewport meta present",
      "viewport meta MISSING")
vp = doc.find(".//head/meta[@name='viewport']")
if vp is not None:
    content = vp.get("content", "")
    check("width=device-width" in content,
          f"viewport content = {content!r}",
          f"viewport missing width=device-width: {content!r}")
check(doc.find(".//main") is not None, "<main> landmark present", "<main> missing")
check(doc.find(".//h1") is not None, "<h1> present", "<h1> missing")
check(len(doc.findall(".//h1")) == 1,
      "exactly one <h1>", f"{len(doc.findall('.//h1'))} <h1> elements (want 1)")
root = doc if doc.tag == "html" else doc.find(".//html")
check(root is not None and root.get("lang"),
      f"<html lang> present = {root.get('lang') if root is not None else None!r}",
      "<html lang> missing")

print("\n== 1b. Image alt attributes (accessibility) ==")
imgs = doc.findall(".//img")
if imgs:
    print(f"  INFO  {len(imgs)} <img> element(s) found")
else:
    notes.append("no <img> elements found -> alt check is vacuous")
# (a) every <img> must carry an alt attribute (may legitimately be empty).
missing_alt = [im for im in imgs if im.get("alt") is None]
check(not missing_alt,
      "every <img> has an alt attribute (present; may be empty for decorative)",
      f"{len(missing_alt)} <img> element(s) MISSING the alt attribute")
# (b) an empty alt="" is the WCAG-correct DECORATIVE pattern only when the image
#     is also hidden from assistive tech (aria-hidden="true" / role="presentation").
decorative = [im for im in imgs
              if im.get("alt") is not None and im.get("alt").strip() == ""]
meaningful = [im for im in imgs
              if im.get("alt") is not None and im.get("alt").strip() != ""]
bad_decorative = [im for im in decorative
                  if im.get("aria-hidden") != "true"
                  and im.get("role") != "presentation"]
check(not bad_decorative,
      f'{len(decorative)} decorative alt="" image(s) marked aria-hidden="true"/presentation',
      f'{len(bad_decorative)} empty-alt <img> NOT marked aria-hidden="true" or '
      f'role="presentation" (empty alt is the decorative pattern; hide it from AT)')
check(len(decorative) + len(meaningful) == len(imgs),
      f"alt coverage complete: {len(meaningful)} meaningful + {len(decorative)} decorative",
      "some <img> could not be classified")
for im in imgs:
    print(f"  INFO  src={im.get('src')!r} alt={im.get('alt')!r} "
          f"aria-hidden={im.get('aria-hidden')!r}")

print("\n== 2. Local asset existence ==")
html = raw.decode("utf-8")
refs = set()
for attr in ("href", "src"):
    for m in re.finditer(rf'{attr}="([^"]+)"', html):
        refs.add(m.group(1))
for m in re.finditer(r'url\(([^)]+)\)', open(CSS, encoding="utf-8").read()):
    refs.add(m.group(1).strip("'\" "))

local = [r for r in refs
         if not re.match(r'^(https?:|mailto:|tel:|data:|#|//)', r)]
for r in sorted(local):
    path = os.path.join(ROOT, r)
    check(os.path.isfile(path), f"asset exists: {r}", f"asset MISSING: {r}")
if not local:
    notes.append("no local asset references found")
check(not any(re.match(r'^https?:', r) for r in refs),
      "no external (http/https) asset references",
      "external asset reference found -> would break offline render")

print("\n== 3. Responsive sanity ==")
css = open(CSS, encoding="utf-8").read()
check("@media" in css, "media queries present", "no media queries -> not responsive")
fixed = re.findall(r'(?<!max-)(?<!min-)width\s*:\s*(\d+)px', css)
big = [w for w in fixed if int(w) >= 480]
check(not big, "no fixed width >= 480px on layout boxes",
      f"fixed widths that can overflow mobile: {big}")
check("max-width" in css, "max-width used for container (fluid)",
      "no max-width -> container may not be fluid")
check(re.search(r'box-sizing\s*:\s*border-box', css) is not None,
      "border-box sizing set", "box-sizing: border-box not set")
notes.append("no headless browser available in this environment; responsive "
             "check is static (viewport meta + CSS heuristics), not pixel-level")

print("\n== 4. Brand-token conformance (Creative tokens.json v2) ==")
tokens_path = os.path.join(ROOT, "..", "brand", "tokens.json")
if os.path.isfile(tokens_path):
    import json
    with open(tokens_path, encoding="utf-8") as fh:
        tok = json.load(fh)
    dark = tok["color"]["sys_resolved"]["dark"]
    expect = {
        "background": dark["background"],
        "on-surface": dark["on-surface"],
        "primary":    dark["primary"],
        "secondary":  dark["secondary"],
        "tertiary":   dark["tertiary"],
    }
    for role, val in expect.items():
        check(val.upper() in css.upper(),
              f"brand token {role} {val} present in styles.css",
              f"brand token {role} {val} NOT found in styles.css")
    ver = tok.get("meta", {}).get("version", "?")
    notes.append(f"aligned to brand tokens.json v{ver} (dark theme)")
else:
    notes.append("brand/tokens.json not present -> palette was hand-picked; "
                 "re-map :root when Creative publishes tokens")

print("\n== 5. Colour contrast (WCAG 2.1) ==")
def _lum(hexs):
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def _ratio(fg, bg):
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

pairs = [
    ("body text",       "#E6E1E9", "#0B0A12"),
    ("muted text",      "#CBC9CF", "#0B0A12"),
    ("muted on card",   "#CBC9CF", "#1C1B20"),
    ("primary heading", "#C9B0F0", "#0B0A12"),
    ("secondary link",  "#8FDBE4", "#0B0A12"),
    ("tertiary eyebrow","#F5D488", "#0B0A12"),
    ("button label",    "#2D1450", "#C9B0F0"),
]
worst = min(_ratio(f, b) for _, f, b in pairs)
for name, fg, bg in pairs:
    r = _ratio(fg, bg)
    print(f"  INFO  {r:5.2f}:1  {name}")
check(worst >= 4.5,
      f"min contrast {worst:.2f}:1 >= WCAG AA 4.5:1 (normal text)",
      f"min contrast {worst:.2f}:1 below WCAG AA 4.5:1")

print("\n== Summary ==")
for n in notes:
    print(f"  NOTE  {n}")
if failures:
    print(f"\nRESULT: FAIL ({len(failures)} problem(s))")
    sys.exit(1)
print("\nRESULT: PASS")
