/* Astra Trading — Command Deck (app controller).
   Wires: trilingual i18n + RTL · timeframe switcher · canvas chart ·
   live readings + rolling tape · AI setup card · position-size calculator ·
   7-day free-trial gate · disclaimers. No libraries, no trackers. */

import { LOCALES, META, STRINGS, t, fmtUTC, fmtNum } from './i18n.js';
import { ChartDeck } from './chart.js';

const LS = {
  locale: 'astra.locale',
  trial: 'astra.trialStart',
  showSessions: 'astra.showSessions',
};

const TF_LIST = ['5m', '15m', '1h', '4h', '1d'];
const TRIAL_DAYS = 7;
const DAY_MS = 86400000;
const WALLET = 'TFBEwXbB4iTyaPC2mtwu5yXSeDjEegJmE6';

const state = {
  locale: 'en',
  tf: '1h',
  data: null,
  loading: false,
  error: null,
  showSessions: true,
  lastGood: null,
};

/* ------------------------------------------------------------------ */
/* persistence                                                         */
/* ------------------------------------------------------------------ */
function lsGet(k, fallback = null) {
  try { const v = localStorage.getItem(k); return v === null ? fallback : v; } catch { return fallback; }
}
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } }

function pickLocale() {
  const saved = lsGet(LS.locale);
  if (saved && LOCALES.includes(saved)) return saved;
  const nav = (navigator.language || 'en').slice(0, 2).toLowerCase();
  return LOCALES.includes(nav) ? nav : 'en';
}

/* ------------------------------------------------------------------ */
/* trial                                                               */
/* ------------------------------------------------------------------ */
function trialStart() {
  let s = lsGet(LS.trial);
  if (!s) { s = new Date().toISOString(); lsSet(LS.trial, s); }
  const d = new Date(s);
  return isNaN(d.getTime()) ? new Date() : d;
}
function trialInfo() {
  const started = trialStart();
  const elapsed = Date.now() - started.getTime();
  const total = TRIAL_DAYS * DAY_MS;
  const left = total - elapsed;
  const daysLeft = Math.max(0, Math.ceil(left / DAY_MS));
  const expired = left <= 0;
  let labelKey = 'trial.daysLeft', vars = { n: daysLeft };
  if (expired) labelKey = 'trial.ended';
  else if (daysLeft <= 0) { labelKey = 'trial.hoursLeft'; vars = { n: Math.max(1, Math.ceil(left / 3600000)) }; }
  else if (daysLeft === 1) labelKey = 'trial.dayLeft';
  return { started, daysLeft, expired, labelKey, vars };
}

/* ------------------------------------------------------------------ */
/* helpers                                                             */
/* ------------------------------------------------------------------ */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function el(tag, attrs = {}, children = []) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) n.setAttribute(k, v);
  }
  for (const c of [].concat(children)) if (c) n.append(c);
  return n;
}

const tr = (key, vars) => t(state.locale, key, vars);

/* Inline SVG icons — never depend on a font glyph existing. */
const ICONS = {
  up: '<svg class="ico-svg" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1.5 11 10H1z" fill="currentColor"/></svg>',
  down: '<svg class="ico-svg" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M6 10.5 1 2h10z" fill="currentColor"/></svg>',
  flat: '<svg class="ico-svg" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><rect x="2" y="5" width="8" height="2" rx="1" fill="currentColor"/></svg>',
  clock: '<svg class="ico-svg" width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.3" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 4.4V8l2.5 1.6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
  lock: '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><rect x="4.5" y="10.5" width="15" height="10" rx="2.4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 10.5V7.6a4 4 0 0 1 8 0v2.9" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
  warn: '<svg class="ico-svg" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.6 15 14H1z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6.2v3.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="11.8" r="0.9" fill="currentColor"/></svg>',
};

function nearestZone(zones, price, side) {
  if (!zones || !zones.length) return null;
  const pool = zones.filter((z) => (side === 'below' ? z.mid <= price : z.mid >= price));
  const arr = pool.length ? pool : zones;
  return arr.slice().sort((a, b) => Math.abs(a.mid - price) - Math.abs(b.mid - price))[0];
}

/* ------------------------------------------------------------------ */
/* data fetch                                                          */
/* ------------------------------------------------------------------ */
async function load(tf) {
  state.loading = true;
  state.error = null;
  paintStatus();
  try {
    const r = await fetch(`/api/analysis?tf=${encodeURIComponent(tf)}`, { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    if (!data || !Array.isArray(data.candles) || data.candles.length < 2) throw new Error('bad payload');
    state.data = data;
    state.lastGood = data;
    state.loading = false;
    renderAll();
    paintStatus();
  } catch (e) {
    state.loading = false;
    state.error = e.message || String(e);
    if (!state.lastGood) { state.data = null; renderAll(); }
    paintStatus();
  }
}

/* ------------------------------------------------------------------ */
/* render: chrome                                                      */
/* ------------------------------------------------------------------ */
function applyLocale() {
  const m = META[state.locale];
  const html = document.documentElement;
  html.lang = m.htmlLang;
  html.dir = m.dir;
  $$('[data-i18n]').forEach((n) => { n.textContent = tr(n.dataset.i18n); });
  $$('[data-i18n-title]').forEach((n) => { n.setAttribute('title', tr(n.dataset.i18nTitle)); });
  $$('[data-i18n-aria]').forEach((n) => { n.setAttribute('aria-label', tr(n.dataset.i18nAria)); });
  document.title = state.locale === 'ar' ? 'Astra Trading — منصة القيادة'
    : state.locale === 'tr' ? 'Astra Trading — Komuta Merkezi'
      : 'Astra Trading — Command Deck';
  $$('.lang-switch button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.locale === state.locale)));
  // timeframe labels are built dynamically, so re-translate them here
  $$('#tf-switch button').forEach((b) => { b.textContent = tr('tf.' + b.dataset.tf); });
  chart.dir = m.dir;
  renderAll();
}

function paintStatus() {
  const pill = $('#live-pill');
  const txt = $('#live-text');
  const src = $('#status-source');
  if (state.loading && !state.data) {
    pill.classList.remove('stale'); txt.textContent = tr('status.connecting');
    src.textContent = ''; return;
  }
  const d = state.data;
  if (!d) {
    pill.classList.add('stale'); txt.textContent = tr('common.error');
    src.textContent = state.error ? `(${state.error})` : '';
    return;
  }
  const live = d.source === 'live';
  pill.classList.toggle('stale', !live);
  txt.textContent = live ? tr('status.live') : tr('status.fixture');
  const when = fmtUTC(d.generated_at);
  src.textContent = `${tr('status.updated', { t: when })} · ${tr('status.source', { s: d.tick?.source || d.source })}`;
}

/* ------------------------------------------------------------------ */
/* render: header price                                                */
/* ------------------------------------------------------------------ */
function renderPrice() {
  const d = state.data;
  const host = $('#price-head');
  if (!d) { host.innerHTML = `<div class="price-big muted">—</div>`; return; }
  const price = d.tick?.mid ?? d.price;
  const prev = d.candles[1]?.c ?? price;
  const chg = price - prev;
  const pct = prev ? (chg / prev) * 100 : 0;
  const cls = chg > 0.001 ? 'up' : chg < -0.001 ? 'down' : 'flatc';
  const arrow = chg > 0.001 ? ICONS.up : chg < -0.001 ? ICONS.down : ICONS.flat;
  host.innerHTML = `
    <div class="price-row">
      <div class="price-big">${fmtNum(price, 2)}</div>
      <div class="price-chg ${cls}" title="${tr('readings.price')}">${arrow} ${chg >= 0 ? '+' : ''}${fmtNum(chg, 2)} (${chg >= 0 ? '+' : ''}${fmtNum(pct, 2)}%)</div>
      <span class="symbol-tag">${d.symbol}</span>
      <span class="symbol-tag">${tr('tf.' + state.tf)}</span>
    </div>`;
}

/* ------------------------------------------------------------------ */
/* render: live readings                                               */
/* ------------------------------------------------------------------ */
function renderReadings() {
  const d = state.data;
  const host = $('#readings');
  const noteHost = $('#session-note');
  if (!d) { host.innerHTML = ''; noteHost.textContent = ''; return; }
  const price = d.tick?.mid ?? d.price;
  const sup = nearestZone(d.zones?.supports, price, 'below');
  const res = nearestZone(d.zones?.resistances, price, 'above');
  const bias = d.bias?.direction || 'neutral';
  const sess = d.session?.name || 'late';

  const distRow = (z) => {
    if (!z) return `<div class="stat-v muted">${tr('readings.none')}</div>`;
    const dist = price - z.mid;
    const pct = (Math.abs(dist) / price) * 100;
    return `<div class="stat-v">${fmtNum(z.mid, 1)}</div>
            <div class="stat-sub">${tr('readings.distAway', { v: `${fmtNum(Math.abs(dist), 1)} (${fmtNum(pct, 2)}%)` })}</div>`;
  };

  const biasCls = bias.startsWith('bullish') ? 'up' : bias.startsWith('bearish') ? 'down' : 'flatc';

  host.innerHTML = `
    <div class="stat">
      <div class="stat-k">${tr('readings.price')}</div>
      <div class="stat-v">${fmtNum(price, 2)}</div>
      <div class="stat-sub">${d.symbol} · ${tr('tf.' + state.tf)}</div>
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.bid')} / ${tr('readings.ask')}</div>
      <div class="stat-v">${fmtNum(d.tick?.bid, 2)} / ${fmtNum(d.tick?.ask, 2)}</div>
      <div class="stat-sub">${tr('readings.spread')} ${fmtNum(d.tick?.spread, 2)}</div>
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.atr')}</div>
      <div class="stat-v">${fmtNum(d.atr, 2)}</div>
      <div class="stat-sub">${tr('readings.atrSub')}</div>
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.bias')}</div>
      <div class="stat-v ${biasCls}">${tr('bias.' + bias)}</div>
      <div class="stat-sub">EMA21 ${fmtNum(d.bias?.ema21, 1)} · EMA50 ${fmtNum(d.bias?.ema50, 1)}</div>
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.nearestSupport')}</div>
      ${distRow(sup)}
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.nearestResistance')}</div>
      ${distRow(res)}
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.liqCount')}</div>
      <div class="stat-v">${(d.liquidity || []).length}</div>
      <div class="stat-sub">${tr('readings.liqCountSub')}</div>
    </div>
    <div class="stat">
      <div class="stat-k">${tr('readings.session')}</div>
      <div class="stat-v">${tr('session.' + sess)}</div>
      <div class="stat-sub">${fmtUTC(d.generated_at)} UTC</div>
    </div>`;

  noteHost.innerHTML = `<b>${tr('readings.session')}:</b> ${tr('session.' + sess)} — ${tr('session.note.' + sess)}`;
}

/* rolling tape: real recent candles, newest last, duplicated for seamless scroll */
function renderTicker() {
  const d = state.data;
  const track = $('#ticker-track');
  if (!d) { track.innerHTML = ''; return; }
  const recent = d.candles.slice(0, 14).reverse();
  const items = recent.map((k, i) => {
    const prev = i > 0 ? recent[i - 1].c : k.o;
    const chg = k.c - prev;
    const cls = chg > 0 ? 'up' : chg < 0 ? 'down' : 'flatc';
    return `<span class="tick-item"><span class="t">${fmtUTC(k.t)}</span><span class="${cls}">${fmtNum(k.c, 2)}</span><span class="t">${chg >= 0 ? '+' : ''}${fmtNum(chg, 2)}</span></span>`;
  }).join('');
  track.innerHTML = items + items; // duplicate → seamless loop
  // measure after layout, set the scroll distance, then resume the paused tape
  requestAnimationFrame(() => {
    const half = track.scrollWidth / 2;
    if (half > 0) {
      track.style.setProperty('--scroll', `${half}px`);
      track.style.animationDuration = `${Math.max(24, half / 26)}s`;
      track.style.animationPlayState = 'running';
    }
  });
}

/* ------------------------------------------------------------------ */
/* render: chart                                                       */
/* ------------------------------------------------------------------ */
function renderChart() {
  const holder = $('#chart-holder');
  const d = state.data;
  if (!d) {
    holder.classList.add('is-empty');
    chart.data = null;
    chart.draw();
    return;
  }
  holder.classList.remove('is-empty');
  chart.showSessions = state.showSessions;
  chart.render(d, { dir: META[state.locale].dir });
}

/* ------------------------------------------------------------------ */
/* render: setup card + calculator                                     */
/* ------------------------------------------------------------------ */
function factorText(f) {
  // engine emits English factor strings; translate the known shapes, else pass through
  let m;
  if ((m = f.match(/^(support|resistance) zone ([\d.]+)[–-]([\d.]+) \((\d+) touches?\)$/))) {
    return tr('factor.zone', { kind: tr('factor.zone.' + m[1]), lo: m[2], hi: m[3], n: m[4] });
  }
  if ((m = f.match(/^EMA21 ([\d.]+) (above|below) EMA50 ([\d.]+)$/))) {
    return tr('factor.ema', { a: m[1], rel: tr('factor.ema.' + m[2]), b: m[3] });
  }
  if ((m = f.match(/^ATR\(14\) ([\d.]+) —/))) {
    return tr('factor.atr', { v: m[1] });
  }
  if ((m = f.match(/^session: (\w+) \((.+)\)$/))) {
    const name = tr('session.' + m[1]);
    const note = tr('session.note.' + m[1]) || m[2];
    return tr('factor.session', { name, note });
  }
  if ((m = f.match(/^liquidity nearby: (.+) @ ([\d.]+)$/))) {
    const kind = m[1].includes('buy-side') ? 'equal_highs' : m[1].includes('sell-side') ? 'equal_lows' : null;
    const note = kind ? tr('liq.' + kind) : m[1];
    return tr('factor.liquidity', { note, p: m[2] });
  }
  return f;
}

function renderSetup() {
  const d = state.data;
  const body = $('#setup-body');
  if (!d) { body.innerHTML = `<p class="muted">${tr('common.loading')}</p>`; return; }
  const s = d.setup;
  if (!s) {
    body.innerHTML = `
      <div class="row between">
        <span class="dir-badge dir-none">${tr('setup.none')}</span>
        <span class="muted" style="font-size:12px">${tr('setup.subtitle')}</span>
      </div>
      <p class="rationale" style="margin-top:14px">${tr('setup.noneNote')}</p>`;
    syncCalc(null);
    return;
  }
  const long = s.direction === 'long';
  const badge = `<span class="dir-badge ${long ? 'dir-long' : 'dir-short'}">${long ? ICONS.up : ICONS.down} ${tr('setup.' + s.direction)}</span>`;
  const conf = Math.round((s.confidence || 0) * 100);

  // localize the engine's English invalidation / rationale strings
  const zoneWord = long ? tr('factor.zone.support') : tr('factor.zone.resistance');
  const rationale = tr('setup.rationaleFmt', {
    dir: tr('setup.' + s.direction), zone: zoneWord,
    entry: fmtNum(s.entry, 2), stop: fmtNum(s.stop_loss, 2),
    tp1: fmtNum(s.tp1, 2), tp2: fmtNum(s.tp2, 2), tp3: fmtNum(s.tp3, 2),
    rr: fmtNum(s.risk_reward, 2),
  });
  let inval = s.invalidation || '';
  let mi;
  if ((mi = inval.match(/^close (above|below) ([\d.]+)$/))) {
    inval = tr(mi[1] === 'above' ? 'setup.invalAbove' : 'setup.invalBelow', { p: mi[2] });
  }

  const level = (k, v, pip, cls = '') => `
    <div class="level">
      <span class="level-k"><i class="pip ${pip}"></i>${k}</span>
      <span class="level-v ${cls}">${fmtNum(v, 2)}</span>
    </div>`;

  body.innerHTML = `
    <div class="row between">
      <div>${badge}</div>
      <div class="mono muted" style="font-size:12px">${s.symbol} · ${tr('tf.' + s.timeframe)} · ${tr('setup.entryType.limit')}</div>
    </div>
    <div class="levels" style="margin-top:14px">
      ${level(tr('setup.entry'), s.entry, 'entry')}
      ${level(tr('setup.stop'), s.stop_loss, 'stop', 'down')}
      ${level(tr('setup.tp1'), s.tp1, 'tp', 'up')}
      ${level(tr('setup.tp2'), s.tp2, 'tp', 'up')}
      ${level(tr('setup.tp3'), s.tp3, 'tp', 'up')}
    </div>
    <div class="row between" style="margin-top:16px">
      <div class="stat" style="background:transparent;padding:0">
        <div class="stat-k">${tr('setup.rr')}</div>
        <div class="stat-v">${fmtNum(s.risk_reward, 2)} : 1</div>
      </div>
      <div class="stat" style="background:transparent;padding:0;flex:1;max-width:200px">
        <div class="stat-k">${tr('setup.confidence')}</div>
        <div class="stat-v">${conf}%</div>
        <div class="conf-track"><div class="conf-fill" style="width:${conf}%"></div></div>
      </div>
    </div>
    <hr class="hr">
    <div class="stat-k" style="margin-bottom:10px">${tr('setup.factors')}</div>
    <ul class="factors">${(s.factors || []).map((f) => `<li>${factorText(f)}</li>`).join('')}</ul>
    <div class="rationale"><b>${tr('setup.invalidation')}:</b> ${inval}</div>
    <div class="rationale">${rationale}</div>`;
  syncCalc(s);
}

/* ------------------------------------------------------------------ */
/* calculator                                                          */
/* ------------------------------------------------------------------ */
const calcState = { account: 10000, riskPct: 1, contract: 100, stopDist: 0 };

function syncCalc(setup) {
  const s = setup || (state.data?.setup || null);
  if (s) {
    const dist = Math.abs(s.entry - s.stop_loss);
    calcState.stopDist = Math.round(dist * 100) / 100;
    const inp = $('#stop-dist');
    if (inp) inp.value = calcState.stopDist.toFixed(2);
  }
  runCalc();
}

function runCalc() {
  const out = $('#calc-out');
  if (!out) return;
  const account = Number($('#acct-size')?.value);
  const riskPct = Number($('#risk-pct')?.value);
  const contract = Number($('#contract-size')?.value) || 100;
  const stopDist = Number($('#stop-dist')?.value);
  const bad = !(account > 0) || !(riskPct > 0) || !(stopDist > 0);
  if (bad) { out.innerHTML = `<div class="stat" style="grid-column:1/-1"><div class="stat-v muted" style="font-size:13px">${tr('calc.invalid')}</div></div>`; return; }
  const riskAmount = account * (riskPct / 100);
  const ounces = riskAmount / stopDist;
  const lots = ounces / contract;
  const perMove = ounces;
  out.innerHTML = `
    <div class="stat"><div class="stat-k">${tr('calc.riskAmount')}</div><div class="stat-v">$${fmtNum(riskAmount, 2)}</div></div>
    <div class="stat"><div class="stat-k">${tr('calc.lots')}</div><div class="stat-v">${lots.toFixed(2)} <span class="muted" style="font-size:12px">${tr('calc.lotsUnit')}</span></div></div>
    <div class="stat"><div class="stat-k">${tr('calc.units')}</div><div class="stat-v">${ounces.toFixed(2)}</div></div>
    <div class="stat"><div class="stat-k">${tr('calc.perMove')}</div><div class="stat-v">$${fmtNum(perMove, 2)}</div></div>`;
}

/* ------------------------------------------------------------------ */
/* trial gate                                                          */
/* ------------------------------------------------------------------ */
function renderTrial() {
  const info = trialInfo();
  const chip = $('#trial-chip');
  chip.classList.toggle('expired', info.expired);
  chip.innerHTML = info.expired
    ? `${ICONS.lock} ${tr('trial.endedChip')}`
    : `${ICONS.clock} ${tr(info.labelKey, info.vars)}`;
  const gate = $('#setup-gate');
  gate.classList.toggle('locked', info.expired);
  $('#gate-title').textContent = tr('trial.gateTitle');
  $('#gate-body').textContent = tr('trial.gateBody');
  $('#gate-upgrade').textContent = `${tr('trial.upgrade')} · ${tr('trial.price')} ${tr('trial.monthly')}`;
  $('#gate-crypto').textContent = tr('trial.cryptoOnly');
  $('#gate-wallet-label').textContent = tr('trial.wallet');
  $('#gate-wallet').textContent = WALLET;
  $('#gate-lock').innerHTML = ICONS.lock;
  $('#gate-copy').textContent = tr('trial.copy');
  $('#gate-howto').textContent = tr('trial.howTo');
  $('#gate-reset').textContent = tr('trial.resetDemo');
  return info;
}

/* ------------------------------------------------------------------ */
/* render all                                                          */
/* ------------------------------------------------------------------ */
function renderAll() {
  renderPrice();
  renderReadings();
  renderTicker();
  renderChart();
  renderSetup();
  renderTrial();
}

/* ------------------------------------------------------------------ */
/* toast                                                               */
/* ------------------------------------------------------------------ */
let toastTimer = null;
function toast(msg) {
  const n = $('#toast');
  n.textContent = msg;
  n.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => n.classList.remove('show'), 2200);
}

/* ------------------------------------------------------------------ */
/* wiring                                                              */
/* ------------------------------------------------------------------ */
const chart = new ChartDeck($('#chart'));

function buildLangSwitch() {
  const host = $('#lang-switch');
  host.innerHTML = '';
  for (const loc of LOCALES) {
    host.append(el('button', {
      type: 'button', 'data-locale': loc, text: META[loc].name,
      'aria-pressed': String(loc === state.locale),
      'data-i18n-aria': 'a11y.langswitch',
      onclick: () => {
        state.locale = loc;
        lsSet(LS.locale, loc);
        applyLocale();
        paintStatus();
      },
    }));
  }
}

function buildTfSwitch() {
  const host = $('#tf-switch');
  host.innerHTML = '';
  for (const tf of TF_LIST) {
    host.append(el('button', {
      type: 'button', 'data-tf': tf, text: tr('tf.' + tf),
      'aria-pressed': String(tf === state.tf),
      onclick: () => {
        if (state.tf === tf) return;
        state.tf = tf;
        $$('#tf-switch button').forEach((b) => {
          b.setAttribute('aria-pressed', String(b.dataset.tf === tf));
          b.textContent = tr('tf.' + b.dataset.tf);
        });
        load(tf);
      },
    }));
  }
}

function init() {
  state.locale = pickLocale();
  state.showSessions = lsGet(LS.showSessions) !== '0';
  buildLangSwitch();
  buildTfSwitch();
  applyLocale();

  // calculator inputs
  $('#acct-size').value = calcState.account;
  $('#risk-pct').value = calcState.riskPct;
  $('#contract-size').value = calcState.contract;
  ['#acct-size', '#risk-pct', '#contract-size', '#stop-dist'].forEach((sel) => {
    $(sel).addEventListener('input', runCalc);
  });

  // session toggle
  const st = $('#toggle-sessions');
  st.checked = state.showSessions;
  st.addEventListener('change', () => {
    state.showSessions = st.checked;
    lsSet(LS.showSessions, st.checked ? '1' : '0');
    renderChart();
  });

  // gate actions
  $('#gate-copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(WALLET); toast(tr('trial.copied')); }
    catch { toast(WALLET); }
  });
  $('#gate-reset').addEventListener('click', () => {
    lsSet(LS.trial, new Date().toISOString());
    renderTrial();
    toast(tr('trial.resetDemo'));
  });

  // retry on error
  $('#retry-btn').addEventListener('click', () => load(state.tf));

  // responsive redraw
  let rt = null;
  window.addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => chart.resize(), 120);
  });
  window.addEventListener('orientationchange', () => setTimeout(() => chart.resize(), 200));

  // keep the deck fresh
  load(state.tf);
  setInterval(() => { if (!document.hidden) load(state.tf); }, 20000);
}

document.addEventListener('DOMContentLoaded', init);
