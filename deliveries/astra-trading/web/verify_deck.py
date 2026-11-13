#!/usr/bin/env python3
"""Astra Trading — Command Deck verifier.

Drives headless Chromium over the DevTools Protocol to prove the deck actually
works in a browser (not just that the files exist):

  * captures console errors / uncaught exceptions per locale
  * measures real geometry (horizontal overflow, element rects, tap-target sizes)
  * confirms the <canvas> actually painted (non-background pixel count)
  * confirms the Arabic surface resolves to IBM Plex Sans Arabic and dir=rtl
  * screenshots desktop / tablet / phone for each locale, plus the expired-trial
    (locked) state.

Run:  python3 verify_deck.py            (server must be up on :8090 or $PORT)
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

BASE = os.environ.get("DECK_URL", "http://127.0.0.1:8090")
OUT = Path(__file__).resolve().parent / "shots"
DEBUG_PORT = int(os.environ.get("CDP_PORT", "9333"))
VIEWPORTS = [("desktop", 1440, 900), ("tablet", 1024, 768), ("phone", 390, 844)]
LOCALES = ["en", "ar", "tr"]

CHROME = shutil.which("chromium") or shutil.which("chromium-browser") or "chromium"


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self._id = 0
        self.events: list[dict] = []

    async def send(self, method, params=None, timeout=30):
        self._id += 1
        mid = self._id
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)

    async def drain(self, seconds=1.0):
        end = time.time() + seconds
        while time.time() < end:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=max(0.05, end - time.time()))
            except asyncio.TimeoutError:
                break
            msg = json.loads(raw)
            if "method" in msg:
                self.events.append(msg)

    def problems(self) -> list[str]:
        out = []
        for e in self.events:
            m = e.get("method")
            p = e.get("params", {})
            if m == "Runtime.exceptionThrown":
                d = p.get("exceptionDetails", {})
                out.append("exception: " + (d.get("exception", {}).get("description") or d.get("text", "?")))
            elif m == "Runtime.consoleAPICalled" and p.get("type") in ("error", "warning"):
                args = " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", []))
                if "favicon" in args.lower():
                    continue
                out.append(f"console.{p.get('type')}: {args[:200]}")
            elif m == "Log.entryAdded":
                lv = p.get("entry", {}).get("level")
                if lv in ("error", "warning"):
                    txt = p["entry"].get("text", "")
                    if "favicon" in txt.lower() or "dbus" in txt.lower():
                        continue
                    out.append(f"log.{lv}: {txt[:200]}")
        return out


PROBE = r"""
(() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const inTicker = (el) => !!(el.closest && el.closest('.ticker'));
  const overflow = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (inTicker(el)) return;                 // the tape is intentionally clipped
    if (r.right > vw + 1.5 || r.left < -1.5) {
      const cs = getComputedStyle(el);
      if (cs.position === 'fixed') return;
      overflow.push({tag: el.tagName.toLowerCase(), cls: (el.className||'').toString().slice(0,40),
                     left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width)});
    }
  });

  // tap targets: controls should be >= 22px tall (inline text links are exempt)
  const small = [];
  document.querySelectorAll('button, input, select, a.btn').forEach(el => {
    if (el.matches('input[type=checkbox], input[type=radio]')) return;  // label is the tap target
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if (r.height < 22) small.push({tag: el.tagName.toLowerCase(), h: Math.round(r.height), txt: (el.textContent||'').trim().slice(0,20)});
  });

  // canvas paint proof
  let canvasPainted = 0, canvasW = 0, canvasH = 0;
  const cv = document.querySelector('#chart');
  if (cv) {
    canvasW = cv.width; canvasH = cv.height;
    try {
      const ctx = cv.getContext('2d');
      const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
      for (let i = 0; i < d.length; i += 4 * 37) {
        if (Math.abs(d[i]-12) > 12 || Math.abs(d[i+1]-12) > 12 || Math.abs(d[i+2]-19) > 12) canvasPainted++;
      }
    } catch (e) { canvasPainted = -1; }
  }

  // ---- WCAG contrast audit of visible text ----
  const lum = (c) => {
    const f = c.map(v => { v/=255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2];
  };
  const parse = (s) => {
    const m = (s||'').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x));
    return { rgb: [p[0],p[1],p[2]], a: p.length > 3 ? p[3] : 1 };
  };
  const bgOf = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0.6) return c.rgb;
      n = n.parentElement;
    }
    return [7,7,12];
  };
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); const hi = Math.max(la,lb), lo = Math.min(la,lb); return (hi+0.05)/(lo+0.05); };
  const lowContrast = [];
  const seen = new Set();
  const gateLocked = !!document.querySelector('#setup-gate.locked');
  document.querySelectorAll('p, span, div, h1, h2, h3, h4, li, a, label, td, th, button').forEach(el => {
    if (el.children.length > 0) return;                 // leaf text only
    const txt = (el.textContent||'').trim();
    if (!txt || txt.length < 2) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.5) return;
    if (gateLocked && el.closest('.gate-content')) return;   // intentionally blurred behind the gate
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    const fg = parse(cs.color); if (!fg) return;
    const bg = bgOf(el);
    const cr = ratio(fg.rgb, bg);
    const size = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight,10) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3.0 : 4.5;
    if (cr < need - 0.05) {
      const key = txt.slice(0,24)+'|'+cr.toFixed(2);
      if (seen.has(key)) return; seen.add(key);
      lowContrast.push({txt: txt.slice(0,30), ratio: Math.round(cr*100)/100, need, size});
    }
  });

  // ---- text clipping (truncated labels) ----
  const clipped = [];
  document.querySelectorAll('body *').forEach(el => {
    if (el.children.length > 0) return;
    const t = (el.textContent||'').trim();
    if (!t) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    const clippedX = el.scrollWidth > el.clientWidth + 2;
    const clippedY = el.scrollHeight > el.clientHeight + 2;
    const hides = cs.overflow !== 'visible' && (cs.overflowX !== 'visible' || cs.overflowY !== 'visible');
    if (clippedX && (hides || cs.textOverflow === 'ellipsis')) {
      clipped.push({txt: t.slice(0,26), sw: el.scrollWidth, cw: el.clientWidth});
    }
  });

  // ---- overlap of the main panels ----
  const panels = ['#setup-gate', '.col-side .card:last-child', '.col-chart .card', '#chart'];
  const rects = {};
  for (const sel of panels) { const e = document.querySelector(sel); if (e) { const r = e.getBoundingClientRect(); rects[sel] = [Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom)]; } }
  const overlaps = [];
  const keys = Object.keys(rects);
  for (let i=0;i<keys.length;i++) for (let j=i+1;j<keys.length;j++) {
    const a=rects[keys[i]], b=rects[keys[j]];
    const ox = Math.min(a[2],b[2]) - Math.max(a[0],b[0]);
    const oy = Math.min(a[3],b[3]) - Math.max(a[1],b[1]);
    const contains = (p,q) => p[0] <= q[0]+1 && p[1] <= q[1]+1 && p[2] >= q[2]-1 && p[3] >= q[3]-1;
    if (ox > 6 && oy > 6 && !contains(a,b) && !contains(b,a)) overlaps.push([keys[i],keys[j],ox,oy]);
  }

  const titleEl = document.querySelector('.card-title');
  const arabicFamily = titleEl ? getComputedStyle(titleEl).fontFamily : '';
  const lock = document.querySelector('#setup-gate.locked');
  const lockOp = lock ? parseFloat(getComputedStyle(document.querySelector('#setup-gate .gate-overlay')).opacity) : 0;

  return {
    lang: de.lang, dir: de.dir,
    vw, scrollW: de.scrollWidth, bodyScrollW: document.body.scrollWidth,
    overflow: overflow.slice(0, 10), overflowCount: overflow.length,
    clipped: clipped.slice(0, 8), clippedCount: clipped.length,
    overlaps, rects,
    smallTargets: small.slice(0, 8), smallCount: small.length,
    lowContrast: lowContrast.slice(0, 10), lowContrastCount: lowContrast.length,
    canvasPainted, canvasW, canvasH,
    arabicFamily, hasArabicFont: /IBM Plex Sans Arabic/.test(arabicFamily),
    readings: document.querySelectorAll('#readings .stat').length,
    tickItems: document.querySelectorAll('.tick-item').length,
    factors: document.querySelectorAll('.factors li').length,
    langButtons: document.querySelectorAll('.lang-switch button').length,
    tfButtons: document.querySelectorAll('#tf-switch button').length,
    price: (document.querySelector('.price-big')||{}).textContent,
    dirBadge: (document.querySelector('.dir-badge')||{}).textContent,
    gateLocked: !!lock, gateOverlayOpacity: lockOp,
    hasDisclaimer: !!(document.querySelector('.disclaimer-bar')||document.querySelector('.mini-disclaimer')),
    hasFooter: !!document.querySelector('footer.site-foot'),
    trialChip: (document.querySelector('#trial-chip')||{}).textContent,
    fontsReady: document.fonts ? document.fonts.status : 'n/a',
    docHeight: de.scrollHeight,
  };
})()
"""


async def run_view(cdp: CDP, locale: str, name: str, w: int, h: int, *, expired=False) -> dict:
    await cdp.send("Emulation.setDeviceMetricsOverride",
                   {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": w < 700})
    # 1) land on the origin so localStorage is writable, 2) seed prefs, 3) reload
    trial = "2000-01-01T00:00:00.000Z" if expired else "2030-01-01T00:00:00.000Z"
    await cdp.send("Page.navigate", {"url": BASE + "/"})
    await asyncio.sleep(1.0)
    await cdp.send("Runtime.evaluate", {"expression":
        f"localStorage.setItem('astra.locale','{locale}');"
        f"localStorage.setItem('astra.trialStart','{trial}');"})
    cdp.events.clear()
    await cdp.send("Page.navigate", {"url": BASE + "/"})
    await asyncio.sleep(2.4)   # let the API call + first paint settle
    await cdp.drain(0.6)
    probe = (await cdp.send("Runtime.evaluate", {"expression": PROBE, "returnByValue": True}))["result"]["value"]
    problems = cdp.problems()
    tag = f"{locale}-{name}" + ("-locked" if expired else "")
    shot = OUT / f"{tag}.png"
    data = (await cdp.send("Page.captureScreenshot", {"format": "png"}))["data"]
    shot.write_bytes(base64.b64decode(data))
    probe.update(locale=locale, viewport=name, size=f"{w}x{h}", problems=problems,
                 screenshot=str(shot.relative_to(Path(__file__).resolve().parent)))
    return probe


async def run_interactions(cdp: CDP) -> dict:
    """Click through the timeframe + language switchers and confirm real changes."""
    await cdp.send("Emulation.setDeviceMetricsOverride",
                   {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})
    await cdp.send("Page.navigate", {"url": BASE + "/"})
    await asyncio.sleep(0.6)
    await cdp.send("Runtime.evaluate", {"expression":
        "localStorage.setItem('astra.locale','en');localStorage.setItem('astra.trialStart','2030-01-01T00:00:00.000Z');"})
    cdp.events.clear()
    await cdp.send("Page.navigate", {"url": BASE + "/"})
    await asyncio.sleep(2.2)

    async def click(sel):
        expr = ("(()=>{const e=document.querySelector(%s); if(!e) return 'missing'; e.click(); return 'ok';})()"
                % json.dumps(sel))
        return (await cdp.send("Runtime.evaluate", {
            "expression": expr, "returnByValue": True}))["result"].get("value", "err")

    async def ev(expr):
        r = (await cdp.send("Runtime.evaluate", {"expression": expr, "returnByValue": True}))["result"]
        if "exceptionDetails" in r:
            raise RuntimeError(str(r["exceptionDetails"])[:200])
        return r.get("value")

    checks = {}
    # --- timeframe switch: 5m ---
    await click("#tf-switch button[data-tf='5m']")
    await asyncio.sleep(1.8)
    tf5_active = await ev("document.querySelector(\"#tf-switch button[data-tf='5m']\").getAttribute('aria-pressed')")
    tf1_pressed = await ev("document.querySelector(\"#tf-switch button[data-tf='1h']\").getAttribute('aria-pressed')")
    checks["tf_5m_active"] = tf5_active == "true"
    checks["tf_1h_released"] = tf1_pressed == "false"

    # --- back to 1h ---
    await click("#tf-switch button[data-tf='1h']")
    await asyncio.sleep(1.6)
    checks["tf_1h_active"] = (await ev("document.querySelector(\"#tf-switch button[data-tf='1h']\").getAttribute('aria-pressed')")) == "true"

    # --- language switch: ar ---
    await click(".lang-switch button[data-locale='ar']")
    await asyncio.sleep(0.8)
    ar_lang = await ev("document.documentElement.lang")
    ar_dir = await ev("document.documentElement.dir")
    ar_label = await ev("document.querySelector('#tf-switch button[data-tf=\"1h\"]').textContent")
    ar_persist = await ev("localStorage.getItem('astra.locale')")
    checks["lang_ar_applied"] = ar_lang == "ar" and ar_dir == "rtl"
    checks["lang_ar_strings"] = ar_label == "1س"
    checks["lang_ar_persisted"] = ar_persist == "ar"

    # --- language switch: tr ---
    await click(".lang-switch button[data-locale='tr']")
    await asyncio.sleep(0.8)
    tr_lang = await ev("document.documentElement.lang")
    tr_dir = await ev("document.documentElement.dir")
    tr_label = await ev("document.querySelector('#tf-switch button[data-tf=\"1h\"]').textContent")
    tr_persist = await ev("localStorage.getItem('astra.locale')")
    checks["lang_tr_applied"] = tr_lang == "tr" and tr_dir == "ltr"
    checks["lang_tr_strings"] = tr_label == "1sa"
    checks["lang_tr_persisted"] = tr_persist == "tr"

    # --- reload persistence (tr must survive) ---
    await cdp.send("Page.navigate", {"url": BASE + "/"})
    await asyncio.sleep(2.0)
    checks["lang_persist_reload"] = (await ev("document.documentElement.lang")) == "tr"

    # --- calculator: 10000 @ 1% with stop distance from setup ---
    await ev("document.querySelector('#acct-size').value=10000;"
             "document.querySelector('#risk-pct').value=2;"
             "document.querySelector('#contract-size').value=100;"
             "document.querySelector('#stop-dist').value=10;"
             "document.querySelector('#acct-size').dispatchEvent(new Event('input'))")
    await asyncio.sleep(0.4)
    calc = await ev("document.querySelector('#calc-out').textContent")
    checks["calc_updates"] = "200" in calc  # 2% of 10000
    checks["calc_lots"] = "0.2" in calc or "0.20" in calc  # 200 / 10 / 100

    await cdp.drain(0.4)
    problems = cdp.problems()
    checks["no_console_errors"] = len(problems) == 0
    shot = OUT / "interaction-tests.png"
    data = (await cdp.send("Page.captureScreenshot", {"format": "png"}))["data"]
    shot.write_bytes(base64.b64decode(data))

    return {
        "locale": "interaction", "viewport": "1280x900", "size": "1280x900",
        "checks": checks, "problems": problems, "calcText": calc.strip()[:120],
        "screenshot": shot.name,
    }


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="deck-chrome-")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         f"--remote-debugging-port={DEBUG_PORT}", "--remote-allow-origins=*",
         f"--user-data-dir={profile}", "--no-first-run", "--disable-extensions",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json", timeout=2) as r:
                targets = json.loads(r.read())
            pages = [t for t in targets if t.get("type") == "page"]
            if pages:
                ws_url = pages[0]["webSocketDebuggerUrl"]; break
        except Exception:
            pass
        time.sleep(0.25)
    if not ws_url:
        proc.terminate()
        print("FATAL: could not reach Chromium DevTools endpoint")
        return 2

    results = []
    async with websockets.connect(ws_url, max_size=60_000_000) as ws:
        cdp = CDP(ws)
        for m in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            await cdp.send(m)
        for loc in LOCALES:
            for name, w, h in VIEWPORTS:
                results.append(await run_view(cdp, loc, name, w, h))
        # locked / expired-trial state (the gate must blur + show the upgrade)
        results.append(await run_view(cdp, "en", "desktop", 1440, 900, expired=True))
        results.append(await run_view(cdp, "ar", "phone", 390, 844, expired=True))
        # live interaction tests
        results.append(await run_interactions(cdp))

    proc.terminate()
    try: proc.wait(timeout=5)
    except Exception: proc.kill()
    shutil.rmtree(profile, ignore_errors=True)

    (OUT / "verify.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))

    # ---- report ----
    fails = 0
    print(f"\n{'locale':6} {'viewport':9} {'size':10} {'paint':>6} {'ovf':>4} {'small':>5} {'stats':>5} {'ticks':>5} {'dir':>4} {'lock':>5}  problems")
    for r in results:
        if r.get("locale") == "interaction":
            print("\n-- interaction tests --")
            for k, v in r["checks"].items():
                print(f"   {'PASS' if v else 'FAIL'}  {k}")
                if not v:
                    fails += 1
            if r["problems"]:
                print("   problems:", r["problems"]); fails += len(r["problems"])
            print("   calc:", r["calcText"])
            continue
        probs = "; ".join(r["problems"]) if r["problems"] else "-"
        if r["problems"]: fails += len(r["problems"])
        print(f"{r['locale']:6} {r['viewport']:9} {r['size']:10} {r['canvasPainted']:>6} "
              f"{r['overflowCount']:>4} {r['smallCount']:>5} {r['readings']:>5} {r['tickItems']:>5} "
              f"{r['dir']:>4} {str(r['gateLocked']):>5}  {probs[:90]}")
        # hard assertions
        if r["overflowCount"] > 0:
            print("   !! horizontal overflow:", json.dumps(r["overflow"], ensure_ascii=False)[:400]); fails += 1
        if r["canvasPainted"] <= 50:
            print("   !! canvas appears unpainted:", r["canvasPainted"]); fails += 1
        if r["readings"] != 8:
            print("   !! live readings panel incomplete:", r["readings"]); fails += 1
        if r["lang"] != r["locale"]:
            print("   !! html lang mismatch:", r["lang"]); fails += 1
        if r["locale"] == "ar" and (r["dir"] != "rtl" or not r["hasArabicFont"]):
            print("   !! Arabic RTL/font not applied:", r["dir"], r["arabicFamily"]); fails += 1
        if r["locale"] != "ar" and r["dir"] != "ltr":
            print("   !! non-Arabic dir wrong:", r["dir"]); fails += 1
        if r.get("clippedCount", 0) > 0:
            print("   !! clipped text:", json.dumps(r["clipped"], ensure_ascii=False)[:300]); fails += 1
        if r.get("overlaps"):
            print("   !! panel overlap:", r["overlaps"]); fails += 1
        if r["lowContrastCount"] > 0:
            print("   !! low-contrast text:", json.dumps(r["lowContrast"], ensure_ascii=False)[:300]); fails += 1
        if r["smallCount"] > 0:
            print("   !! sub-22px control:", json.dumps(r["smallTargets"], ensure_ascii=False)[:200]); fails += 1
        if not (r["hasDisclaimer"] and r["hasFooter"]):
            print("   !! missing disclaimer/footer"); fails += 1
        if r["tfButtons"] != 5 or r["langButtons"] != 3:
            print("   !! switchers wrong:", r["tfButtons"], r["langButtons"]); fails += 1
        if r["locale"] != "ar" and r["factors"] < 3:
            print("   !! factors list thin:", r["factors"]); fails += 1
        if r.get("gateLocked") and r["gateOverlayOpacity"] < 0.99:
            print("   !! gate overlay not shown:", r["gateOverlayOpacity"]); fails += 1

    print(f"\nscreenshots -> {OUT}")
    print(f"total hard failures: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
