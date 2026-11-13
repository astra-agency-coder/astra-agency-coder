/* Astra Trading — Command Deck chart.
   Pure <canvas>, zero libraries. Draws, in order:
     session shading → support/resistance zones → grid → candles →
     liquidity dashed lines → current-price line → axes.
   Palette is taken straight from brand/tokens.json (BRAND.md chart language):
     bull #16C79A · bear #FF4D6D · gold price line #E8C766 · flat #8E93A6
*/

const COL = {
  bg: '#0C0C13',
  grid: 'rgba(42,42,56,0.65)',
  gridStrong: 'rgba(90,95,114,0.55)',
  bull: '#16C79A',
  bear: '#FF4D6D',
  bullDim: 'rgba(22,199,154,0.85)',
  bearDim: 'rgba(255,77,109,0.85)',
  gold: '#E8C766',
  support: 'rgba(22,199,154,0.16)',
  supportEdge: 'rgba(22,199,154,0.85)',
  resistance: 'rgba(255,77,109,0.16)',
  resistanceEdge: 'rgba(255,77,109,0.85)',
  liquidity: '#C9B0F0',
  text: '#A9AEBF',
  textDim: '#767C90',
  axis: '#5A5F72',
  sessionAsia: 'rgba(142,147,166,0.055)',
  sessionLondon: 'rgba(201,176,240,0.075)',
  sessionNY: 'rgba(232,199,102,0.06)',
  crosshair: 'rgba(238,240,247,0.28)',
};

// UTC-hour → session bucket, matching engine.analysis.session_context()
function sessionOf(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return 'late';
  const h = d.getUTCHours();
  if (h >= 0 && h < 7) return 'asia';
  if (h < 12) return 'london';
  if (h < 16) return 'london_ny_overlap';
  if (h < 21) return 'new_york';
  return 'late';
}

const SESSION_FILL = {
  asia: COL.sessionAsia,
  london: COL.sessionLondon,
  london_ny_overlap: COL.sessionLondon,
  new_york: COL.sessionNY,
  late: 'rgba(90,95,114,0.03)',
};

const PAD = { l: 10, r: 78, t: 14, b: 30 };

export class ChartDeck {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.data = null;
    this.dir = 'ltr';
    this.legendFor = null; // (key) => label
    this.showSessions = true;
    this.hover = null;
    this._raf = null;
    this._bindPointer();
  }

  setLegend(fn) { this.legendFor = fn; }

  _bindPointer() {
    const c = this.canvas;
    const move = (e) => {
      const r = c.getBoundingClientRect();
      const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
      const y = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
      this.hover = { x, y };
      this._schedule();
    };
    const leave = () => { this.hover = null; this._schedule(); };
    c.addEventListener('mousemove', move);
    c.addEventListener('mouseleave', leave);
    c.addEventListener('touchstart', move, { passive: true });
    c.addEventListener('touchmove', move, { passive: true });
    c.addEventListener('touchend', leave);
  }

  _schedule() {
    if (this._raf) return;
    this._raf = requestAnimationFrame(() => { this._raf = null; this.draw(); });
  }

  render(data, { dir = 'ltr' } = {}) {
    this.data = data;
    this.dir = dir;
    this.draw();
  }

  resize() { this.draw(); }

  draw() {
    const c = this.canvas;
    const rect = c.getBoundingClientRect();
    const cssW = Math.max(240, rect.width || 800);
    const cssH = Math.max(200, rect.height || 460);
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    if (c.width !== Math.round(cssW * dpr) || c.height !== Math.round(cssH * dpr)) {
      c.width = Math.round(cssW * dpr);
      c.height = Math.round(cssH * dpr);
    }
    const ctx = this.ctx;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);
    ctx.fillStyle = COL.bg;
    ctx.fillRect(0, 0, cssW, cssH);

    const d = this.data;
    if (!d || !d.candles || d.candles.length < 2) {
      this._empty(cssW, cssH);
      return;
    }

    // price axis side: right in LTR, left in RTL (a designed choice, not a mirror)
    const rtl = this.dir === 'rtl';
    const pad = { l: rtl ? PAD.r : PAD.l, r: rtl ? PAD.l : PAD.r, t: PAD.t, b: PAD.b };
    const plotW = cssW - pad.l - pad.r;
    const plotH = cssH - pad.t - pad.b;

    const candles = d.candles.slice().reverse(); // oldest → newest, left → right
    const n = candles.length;
    const slot = plotW / n;
    const bodyW = Math.max(1, Math.min(slot * 0.68, 14));

    // --- price scale (include zones + price so nothing clips) ---
    let lo = Infinity, hi = -Infinity;
    for (const k of candles) { if (k.l < lo) lo = k.l; if (k.h > hi) hi = k.h; }
    const zones = [...(d.zones?.supports || []), ...(d.zones?.resistances || [])];
    for (const z of zones) { if (z.low < lo) lo = z.low; if (z.high > hi) hi = z.high; }
    for (const l of (d.liquidity || [])) { if (l.price < lo) lo = l.price; if (l.price > hi) hi = l.price; }
    if (typeof d.price === 'number') { if (d.price < lo) lo = d.price; if (d.price > hi) hi = d.price; }
    const range = (hi - lo) || 1;
    lo -= range * 0.06; hi += range * 0.06;

    const yOf = (p) => pad.t + (hi - p) / (hi - lo) * plotH;
    const xOf = (i) => pad.l + slot * (i + 0.5);

    ctx.save();
    ctx.beginPath();
    ctx.rect(pad.l, pad.t, plotW, plotH);
    ctx.clip();

    // --- session shading ---
    if (this.showSessions) {
      let runStart = 0;
      let cur = sessionOf(candles[0].t);
      for (let i = 1; i <= n; i++) {
        const s = i < n ? sessionOf(candles[i].t) : null;
        if (s !== cur) {
          const x0 = pad.l + slot * runStart;
          const x1 = pad.l + slot * i;
          ctx.fillStyle = SESSION_FILL[cur] || 'transparent';
          ctx.fillRect(x0, pad.t, x1 - x0, plotH);
          cur = s; runStart = i;
        }
      }
    }

    // --- zones ---
    const drawZone = (z, kind) => {
      const yTop = yOf(z.high), yBot = yOf(z.low);
      const y = Math.min(yTop, yBot);
      const h = Math.max(2, Math.abs(yBot - yTop));
      ctx.fillStyle = kind === 'support' ? COL.support : COL.resistance;
      ctx.fillRect(pad.l, y, plotW, h);
      ctx.strokeStyle = kind === 'support' ? COL.supportEdge : COL.resistanceEdge;
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.globalAlpha = 0.35 + 0.45 * (z.strength ?? 0.5);
      ctx.beginPath();
      ctx.moveTo(pad.l, y + 0.5); ctx.lineTo(pad.l + plotW, y + 0.5);
      ctx.moveTo(pad.l, y + h - 0.5); ctx.lineTo(pad.l + plotW, y + h - 0.5);
      ctx.stroke();
      ctx.globalAlpha = 1;

      // zone price tag on the axis side
      if (h >= 9) {
        const label = `${z.low.toFixed(1)}–${z.high.toFixed(1)}`;
        ctx.font = '10px "IBM Plex Mono", monospace';
        ctx.textBaseline = 'middle';
        const tagY = y + h / 2;
        if (rtl) { ctx.textAlign = 'right'; ctx.fillStyle = COL.textDim; ctx.fillText(label, pad.l - 4, tagY); }
        else { ctx.textAlign = 'left'; ctx.fillStyle = COL.textDim; ctx.fillText(label, pad.l + plotW + 4, tagY); }
      }
    };
    for (const z of (d.zones?.supports || [])) drawZone(z, 'support');
    for (const z of (d.zones?.resistances || [])) drawZone(z, 'resistance');

    // --- grid + price axis ---
    const ticks = 6;
    ctx.font = '11px "IBM Plex Mono", monospace';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= ticks; i++) {
      const p = hi - (hi - lo) * (i / ticks);
      const y = Math.round(yOf(p)) + 0.5;
      ctx.strokeStyle = COL.grid;
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + plotW, y); ctx.stroke();
      ctx.fillStyle = COL.textDim;
      if (rtl) { ctx.textAlign = 'right'; ctx.fillText(p.toFixed(1), pad.l - 6, y); }
      else { ctx.textAlign = 'left'; ctx.fillText(p.toFixed(1), pad.l + plotW + 6, y); }
    }

    // --- candles ---
    for (let i = 0; i < n; i++) {
      const k = candles[i];
      const bull = k.c >= k.o;
      const col = bull ? COL.bullDim : COL.bearDim;
      const x = xOf(i);
      ctx.strokeStyle = col;
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      const wickTop = yOf(k.h), wickBot = yOf(k.l);
      ctx.beginPath();
      ctx.moveTo(Math.round(x) + 0.5, wickTop);
      ctx.lineTo(Math.round(x) + 0.5, wickBot);
      ctx.stroke();
      const yO = yOf(k.o), yC = yOf(k.c);
      const top = Math.min(yO, yC);
      const hh = Math.max(1, Math.abs(yC - yO));
      ctx.fillStyle = col;
      ctx.fillRect(x - bodyW / 2, top, bodyW, hh);
    }

    // --- liquidity (dashed + label) ---
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.1;
    const liq = (d.liquidity || []).slice(0, 12);
    for (const l of liq) {
      const y = Math.round(yOf(l.price)) + 0.5;
      if (y < pad.t - 2 || y > pad.t + plotH + 2) continue;
      ctx.strokeStyle = COL.liquidity;
      ctx.globalAlpha = 0.55 + 0.35 * (l.strength ?? 0.5);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + plotW, y); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.setLineDash([]);

    // liquidity labels (few, spaced to avoid clutter)
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textBaseline = 'middle';
    const placed = [];
    for (const l of liq) {
      const y = yOf(l.price);
      if (y < pad.t + 6 || y > pad.t + plotH - 6) continue;
      if (placed.some((py) => Math.abs(py - y) < 13)) continue;
      placed.push(y);
      const label = `${(l.kind || '').replace(/_/g, ' ')} ${l.price.toFixed(1)}`;
      ctx.fillStyle = 'rgba(12,12,19,0.82)';
      const tw = ctx.measureText(label).width;
      const bx = rtl ? pad.l + 6 : pad.l + plotW - tw - 14;
      ctx.fillRect(bx - 4, y - 8, tw + 8, 15);
      ctx.fillStyle = COL.liquidity;
      ctx.textAlign = 'left';
      ctx.fillText(label, bx, y);
    }

    // --- current price line ---
    if (typeof d.price === 'number') {
      const y = Math.round(yOf(d.price)) + 0.5;
      ctx.strokeStyle = COL.gold;
      ctx.lineWidth = 1.4;
      ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + plotW, y); ctx.stroke();
      ctx.setLineDash([]);
      // price tag
      const label = d.price.toFixed(2);
      ctx.font = 'bold 11px "IBM Plex Mono", monospace';
      const tw = ctx.measureText(label).width + 10;
      const tagX = rtl ? pad.l - tw - 2 : pad.l + plotW + 2;
      ctx.fillStyle = COL.gold;
      ctx.fillRect(tagX, y - 9, tw, 18);
      ctx.fillStyle = '#07070C';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, tagX + tw / 2, y + 0.5);
    }

    ctx.restore();

    // --- frame ---
    ctx.strokeStyle = COL.axis;
    ctx.globalAlpha = 0.5;
    ctx.lineWidth = 1;
    ctx.strokeRect(pad.l + 0.5, pad.t + 0.5, plotW - 1, plotH - 1);
    ctx.globalAlpha = 1;

    // --- time axis ---
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.fillStyle = COL.textDim;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    const step = Math.max(1, Math.ceil(n / 7));
    for (let i = 0; i < n; i += step) {
      const dt = new Date(candles[i].t);
      if (isNaN(dt.getTime())) continue;
      const lbl = `${String(dt.getUTCMonth() + 1).padStart(2, '0')}/${String(dt.getUTCDate()).padStart(2, '0')} ${String(dt.getUTCHours()).padStart(2, '0')}:${String(dt.getUTCMinutes()).padStart(2, '0')}`;
      ctx.fillText(lbl, xOf(i), pad.t + plotH + 8);
    }

    // --- crosshair (desktop hover) ---
    if (this.hover && this.hover.x >= pad.l && this.hover.x <= pad.l + plotW &&
        this.hover.y >= pad.t && this.hover.y <= pad.t + plotH) {
      const idx = Math.max(0, Math.min(n - 1, Math.floor((this.hover.x - pad.l) / slot)));
      const k = candles[idx];
      const x = Math.round(xOf(idx)) + 0.5;
      ctx.strokeStyle = COL.crosshair;
      ctx.setLineDash([3, 3]);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, pad.t + plotH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad.l, this.hover.y); ctx.lineTo(pad.l + plotW, this.hover.y); ctx.stroke();
      ctx.setLineDash([]);

      const p = hi - (this.hover.y - pad.t) / plotH * (hi - lo);
      const ohlc = `${p.toFixed(2)}   O ${k.o.toFixed(2)} H ${k.h.toFixed(2)} L ${k.l.toFixed(2)} C ${k.c.toFixed(2)}`;
      ctx.font = '11px "IBM Plex Mono", monospace';
      const tw = ctx.measureText(ohlc).width + 14;
      const bx = rtl ? pad.l + plotW - tw - 6 : pad.l + 6;
      ctx.fillStyle = 'rgba(18,18,26,0.94)';
      ctx.fillRect(bx, pad.t + 6, tw, 22);
      ctx.strokeStyle = COL.axis;
      ctx.strokeRect(bx + 0.5, pad.t + 6.5, tw - 1, 21);
      ctx.fillStyle = COL.text;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(ohlc, bx + 7, pad.t + 17);
    }
  }

  _empty(w, h) {
    const ctx = this.ctx;
    ctx.fillStyle = COL.textDim;
    ctx.font = '13px "IBM Plex Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('—', w / 2, h / 2);
  }
}
