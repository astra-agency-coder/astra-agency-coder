import pathlib, sys
from playwright.sync_api import sync_playwright
from PIL import Image
BRAND=pathlib.Path('brand')
src=sys.argv[1] if len(sys.argv)>1 else 'brand/logo-mark.svg'
svg=pathlib.Path(src).read_text().replace('width="512" height="512"','').replace('width="32" height="32"','')
N=int(sys.argv[2]) if len(sys.argv)>2 else 72
html=f'<!DOCTYPE html><html><body style="margin:0;background:#000"><div style="width:{N*8}px;height:{N*8}px">{svg}</div></body></html>'
out=BRAND/'build/_ascii.html'; out.write_text(html)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":N*8,"height":N*8})
    pg.goto("file://"+str(out.resolve())); pg.wait_for_timeout(200)
    pg.screenshot(path=str(BRAND/'build/_ascii.png')); b.close()
im=Image.open(BRAND/'build/_ascii.png').convert('L').resize((N,N))
px=im.load()
ramp=" .:-=+*#%@"
for y in range(N):
    row=""
    for x in range(N):
        v=px[x,y]
        row+=ramp[min(9,v*10//256)]
    print(row)
