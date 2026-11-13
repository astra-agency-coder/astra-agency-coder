#!/usr/bin/env python3
"""Render the Astra Trading brand sheet to PNG/SVG via headless Chromium.

The sheet is generated from the real brand tokens and the real logo files, so
it can never drift from the product. Reproducible: run it any time.

    python3 tools/make_brand_sheet.py            # writes brand/brand-sheet.{html,png,svg}
"""
import base64
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
TOKENS = json.loads((BRAND / "tokens.json").read_text())
REF = TOKENS["color"]["reference"]


def _svg_inline(path: pathlib.Path) -> str:
    return re.sub(r"<\?xml.*?\?>", "", path.read_text()).strip()


def swatches(prefix: str) -> str:
    items = [(k, v) for k, v in REF.items() if k.startswith(prefix)]
    items.sort(key=lambda kv: int(kv[0].split("-")[-1]) if kv[0].split("-")[-1].isdigit() else 0)
    cells = []
    for name, hexv in items:
        cells.append(
            f'<div class="sw"><div class="chip" style="background:{hexv}"></div>'
            f'<div class="meta"><b>{name}</b><span>{hexv}</span></div></div>')
    return "".join(cells)


def build_html() -> str:
    fonts = TOKENS["typography"]
    scale = fonts["scale_px"]
    scale_rows = "".join(
        f'<div class="ty"><span class="lbl">{k} · {v}px</span>'
        f'<span style="font-family:\'{fonts["display"]["family"]}\';font-size:{min(v, 56)}px;'
        f'line-height:1.1">Gold, decoded.</span></div>'
        for k, v in scale.items())
    langs = " · ".join(TOKENS.get("languages", []))
    mark = _svg_inline(BRAND / "logo-mark.svg")
    onlight = BRAND / "logo-mark-onlight.svg"
    mark_light = _svg_inline(onlight) if onlight.exists() else mark
    mono = _svg_inline(BRAND / "logo-mono.svg") if (BRAND / "logo-mono.svg").exists() else ""
    chart_lang = TOKENS.get("chart_language", {})
    chart_txt = " · ".join(f"{k}={v}" for k, v in chart_lang.items()) if isinstance(chart_lang, dict) else str(chart_lang)
    rtl_txt = "Full mirror (dir=rtl)" if TOKENS.get("rtl") else "LTR only"
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Astra Trading — Brand Sheet</title>
<style>
  :root {{ --gold:{REF.get('gold-300')}; --bg:{REF.get('neutral-3')};
           --surf:{REF.get('neutral-8')}; --line:{REF.get('neutral-20')};
           --ink:{REF.get('neutral-90')}; --sub:{REF.get('neutral-70')}; }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ background:var(--bg); color:var(--ink);
          font-family:'{fonts['body']['family']}',system-ui,sans-serif; padding:48px; }}
  .sheet {{ max-width:1180px; margin:0 auto; }}
  h1 {{ font-family:'{fonts['display']['family']}'; font-size:44px; letter-spacing:-.02em; }}
  h1 small {{ display:block; font-family:'{fonts['body']['family']}'; font-size:14px;
             letter-spacing:.14em; text-transform:uppercase; color:var(--gold); margin-bottom:10px; }}
  h2 {{ font-family:'{fonts['display']['family']}'; font-size:20px; margin:44px 0 16px;
       padding-bottom:10px; border-bottom:1px solid var(--line); }}
  .row {{ display:flex; gap:28px; align-items:center; flex-wrap:wrap; }}
  .logos {{ background:var(--surf); border:1px solid var(--line); border-radius:16px; padding:32px; }}
  .logos svg {{ width:120px; height:120px; }}
  .logos.mono svg {{ width:96px; height:96px; }}
  .cap {{ font-size:12px; color:var(--sub); margin-top:12px; text-align:center; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:12px; }}
  .sw {{ background:var(--surf); border:1px solid var(--line); border-radius:12px;
        overflow:hidden; }}
  .chip {{ height:62px; }}
  .meta {{ padding:9px 11px; display:flex; flex-direction:column; gap:2px; }}
  .meta b {{ font-size:12px; }} .meta span {{ font-size:11px; color:var(--sub);
            font-family:'{fonts['mono']['family']}',monospace; }}
  .ty {{ display:flex; align-items:baseline; gap:22px; padding:9px 0;
        border-bottom:1px dashed var(--line); }}
  .lbl {{ width:130px; font-size:12px; color:var(--sub);
         font-family:'{fonts['mono']['family']}',monospace; flex:none; }}
  .facts {{ display:flex; gap:12px; flex-wrap:wrap; }}
  .fact {{ background:var(--surf); border:1px solid var(--line); border-radius:12px;
          padding:14px 18px; }}
  .fact b {{ display:block; font-size:11px; color:var(--sub); text-transform:uppercase;
            letter-spacing:.1em; }} .fact span {{ font-size:15px; }}
  footer {{ margin-top:46px; padding-top:18px; border-top:1px solid var(--line);
           font-size:12px; color:var(--sub); }}
</style></head><body><div class="sheet">
  <h1><small>{TOKENS['parent_brand']}</small>{TOKENS['brand']} — Brand Sheet
    <span style="font-size:15px;color:var(--sub);font-weight:400">
      · tokens v{TOKENS['version']}</span></h1>

  <h2>Logo</h2>
  <div class="row">
    <div class="logos">{mark}<div class="cap">Primary mark</div></div>
    <div class="logos mono">{mono}<div class="cap">Mono</div></div>
    <div class="logos" style="background:#F7F4EC">
      {mark_light}
      <div class="cap" style="color:#5A5F72">On light</div></div>
  </div>

  <h2>Colour — reference palette</h2>
  <div class="grid">{swatches('gold-')}{swatches('neutral-')}{swatches('bull-')}{swatches('bear-')}{swatches('violet-')}</div>

  <h2>Typography</h2>
  <div class="ty"><span class="lbl">display</span>
    <span style="font-family:'{fonts['display']['family']}';font-size:30px">{fonts['display']['family']}</span>
    <span style="color:var(--sub);font-size:12px">{fonts['display']['use']} · {fonts['display']['licence']}</span></div>
  <div class="ty"><span class="lbl">body</span>
    <span style="font-size:20px">{fonts['body']['family']}</span>
    <span style="color:var(--sub);font-size:12px">{fonts['body']['use']} · {fonts['body']['licence']}</span></div>
  <div class="ty"><span class="lbl">arabic</span>
    <span style="font-size:22px" dir="rtl">الذهب، بوضوح تام</span>
    <span style="color:var(--sub);font-size:12px">{fonts['arabic']['family']} · {fonts['arabic']['use']}</span></div>
  <div class="ty"><span class="lbl">mono</span>
    <span style="font-family:'{fonts['mono']['family']}',monospace;font-size:20px">3,876.93 ▲</span>
    <span style="color:var(--sub);font-size:12px">{fonts['mono']['use']}</span></div>
  <div style="margin-top:14px">{scale_rows}</div>

  <h2>Language & direction</h2>
  <div class="facts">
    <div class="fact"><b>Locales</b><span>{langs}</span></div>
    <div class="fact"><b>RTL</b><span>{rtl_txt}</span></div>
    <div class="fact"><b>Chart language</b><span>{chart_txt}</span></div>
  </div>

  <footer>{TOKENS['brand']} — a product of {TOKENS['parent_brand']}.
    Generated from brand/tokens.json; fonts under OFL-1.1.</footer>
</div></body></html>"""


def main() -> int:
    html = build_html()
    out_html = BRAND / "brand-sheet.html"
    out_html.write_text(html)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        pg.goto("file://" + str(out_html.resolve()), wait_until="load")
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(BRAND / "brand-sheet.png"), full_page=True)
        b.close()
    print("wrote", out_html.name, "+ brand-sheet.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
