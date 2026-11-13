import pathlib, sys
from playwright.sync_api import sync_playwright
BRAND = pathlib.Path('brand')
svg = (BRAND/'logo-mark.svg').read_text()
svg = svg.replace('width="512" height="512"','')  # let CSS size it
sizes=[512,256,64,32,24,16]
cells="".join(
  f'<div class="c"><div class="dark" style="width:{s}px;height:{s}px">{svg}</div>'
  f'<div class="dark" style="width:{s}px;height:{s}px">{svg}</div>'
  f'<span>{s}px</span></div>' for s in sizes)
html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{background:#c8c8d0;margin:0;padding:24px;font:12px monospace}}
.c{{display:inline-flex;flex-direction:column;align-items:center;gap:4px;margin:12px}}
.dark{{background:#07070C;display:flex;align-items:center;justify-content:center;border-radius:6px}}
svg{{width:100%;height:100%;display:block}}
</style></head><body>{cells}</body></html>"""
out=BRAND/'build/_mark_preview.html'; out.write_text(html)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1400,"height":700},device_scale_factor=2)
    pg.goto("file://"+str(out.resolve())); pg.wait_for_timeout(300)
    pg.screenshot(path=str(BRAND/'build/_mark_preview.png'),full_page=True)
    b.close()
print("ok")
