/* Vibefish dashboard. Vanilla JS, no build step.
 * Data contract (base URL from ?data=, default ./data/):
 *   index.json                 {"runs":[{id, generated, forge_version, pod, games, path}]}
 *   <run.path>                 rollup.json written by runner/rollup.py
 *   cards/scryfall-cache.json  {name: {image_uris:{small,normal}, scryfall_uri, ...}} (optional)
 */
(() => {
  'use strict';

  const qs = new URLSearchParams(location.search);
  const DATA = (qs.get('data') || './data').replace(/\/+$/, '') + '/';
  const MAX_SERIES = 8;
  const seatColor = (seat) => `var(--s${(seat % MAX_SERIES) + 1})`;
  const SVG = 'http://www.w3.org/2000/svg';

  // ---------- tiny DOM helpers (all text goes in via textContent) ----------
  function el(tag, attrs, ...children) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null) continue;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k === 'style') n.style.cssText = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    for (const c of children.flat(Infinity)) {
      if (c == null) continue;
      n.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return n;
  }
  function svg(tag, attrs, ...children) {
    const n = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null) continue;
      if (k === 'text') n.textContent = v;
      else n.setAttribute(k, v);
    }
    for (const c of children.flat(Infinity)) if (c != null) n.append(c);
    return n;
  }
  const $ = (sel) => document.querySelector(sel);
  const pct = (v, d = 0) => v == null ? '–' : `${(v * 100).toFixed(d)}%`;
  const num = (v, d = 1) => v == null || Number.isNaN(v) ? '–' : Number(v).toFixed(d).replace(/\.0$/, '');
  const shortName = (s) => (s || '').replace(/\s*\[[^\]]*\]/g, '').trim();
  const turnLabel = (i) => `T${i}`;

  async function loadJson(url, optional) {
    const r = await fetch(url, { cache: 'no-cache' });
    if (!r.ok) {
      if (optional) return null;
      throw new Error(`${url} → HTTP ${r.status}`);
    }
    return r.json();
  }

  // ---------- theme ----------
  function effectiveTheme() {
    const t = document.documentElement.dataset.theme;
    if (t === 'light' || t === 'dark') return t;
    return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  $('#theme-toggle').addEventListener('click', () => {
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('vibefish-theme', next); } catch (e) { /* private mode */ }
  });

  // ---------- tooltip ----------
  const tip = $('#tooltip');
  function showTip(x, y, title, rows) {
    tip.replaceChildren(el('div', { class: 'tt-title', text: title }),
      ...rows.map((r) => el('div', { class: 'tt-row' },
        el('b', { text: r.value }),
        el('i', { class: 'key', style: `background:${r.color}` }),
        el('span', { text: r.name }))));
    tip.hidden = false;
    const pad = 14;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let left = x + pad, top = y + pad;
    if (left + w > innerWidth - 8) left = x - w - pad;
    if (top + h > innerHeight - 8) top = y - h - pad;
    tip.style.left = `${Math.max(8, left)}px`;
    tip.style.top = `${Math.max(8, top)}px`;
  }
  function hideTip() { tip.hidden = true; }

  // ---------- charts ----------
  function niceMax(v) {
    if (!(v > 0)) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(v)));
    for (const m of [1, 2, 2.5, 4, 5, 8, 10]) if (m * p >= v) return m * p;
    return 10 * p;
  }

  // Charts draw at their container's pixel width (1 SVG unit = 1 CSS px) and redraw on resize,
  // so type stays legible instead of scaling with a fixed viewBox.
  const charts = [];
  function chartFigure(title, subtitle, build) {
    const fig = el('figure', { class: 'chart' });
    const toggle = el('button', { class: 'toggle', type: 'button', text: 'Table', 'aria-pressed': 'false' });
    fig.append(el('figcaption', {}, el('div', {}, el('h3', { text: title }), subtitle ? el('p', { text: subtitle }) : null), toggle));
    const plotWrap = el('div', { class: 'plot' });
    const tableWrap = el('div', { class: 'table-view' });
    tableWrap.hidden = true;
    fig.append(plotWrap, tableWrap);
    const entry = { fig, lastW: 0, draw() {
      const w = Math.max(260, Math.floor(plotWrap.clientWidth || fig.clientWidth || 600));
      entry.lastW = w;
      const { plot, table } = build(w);
      plotWrap.replaceChildren(plot);
      tableWrap.replaceChildren(table);
    } };
    charts.push(entry);
    toggle.addEventListener('click', () => {
      const showTable = tableWrap.hidden;
      tableWrap.hidden = !showTable;
      plotWrap.hidden = showTable;
      toggle.textContent = showTable ? 'Chart' : 'Table';
      toggle.setAttribute('aria-pressed', String(showTable));
    });
    return fig;
  }
  function relayout(force) {
    for (const c of charts) {
      if (!c.fig.isConnected) continue;
      const w = c.fig.querySelector('.plot').clientWidth;
      if (force || Math.abs(w - c.lastW) > 24) c.draw();
    }
  }
  let resizeTimer = null;
  addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => relayout(false), 150); });

  function dataTable(headers, rows) {
    const wrap = el('div');
    const t = el('table', {}, el('thead', {}, el('tr', {}, headers.map((h) => el('th', { scope: 'col', text: h })))),
      el('tbody', {}, rows.map((r) => el('tr', {}, r.map((c, i) => el(i === 0 ? 'th' : 'td', i === 0 ? { scope: 'row', text: c } : { text: c }))))));
    wrap.append(t);
    return wrap;
  }

  /** Multi-series line chart over turns. series: [{name, color, values:[number|null]}] */
  function lineChart({ title, subtitle, x, series, yMax, format }) {
    return chartFigure(title, subtitle, (W) => {
      const wide = W >= 480;
      const H = Math.max(220, Math.min(320, Math.round(W * 0.5)));
      const m = { t: 14, r: wide ? 108 : 14, b: 34, l: 44 };
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const all = series.flatMap((s) => s.values).filter((v) => v != null);
      const ymax = yMax != null ? yMax : niceMax(Math.max(0, ...all));
      const sx = (i) => m.l + (x.length > 1 ? (i * pw) / (x.length - 1) : pw / 2);
      const sy = (v) => m.t + ph - (v / ymax) * ph;
      const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': title });

      const ticks = 4;
      for (let k = 0; k <= ticks; k++) {
        const v = (ymax * k) / ticks, y = sy(v);
        root.append(svg('line', { class: k === 0 ? 'baseline' : 'gridline', x1: m.l, x2: m.l + pw, y1: y, y2: y }));
        root.append(svg('text', { class: 'tick', x: m.l - 6, y: y + 4, 'text-anchor': 'end', text: format(v, true) }));
      }
      const every = pw / x.length < 26 ? 2 : 1;
      x.forEach((lab, i) => { if (i % every === 0 || i === x.length - 1) root.append(svg('text', { class: 'tick', x: sx(i), y: m.t + ph + 18, 'text-anchor': 'middle', text: lab })); });

      // lines + end dots
      const ends = [];
      series.forEach((s) => {
        let d = '', pen = false, lastIdx = -1;
        s.values.forEach((v, i) => {
          if (v == null) { pen = false; return; }
          d += `${pen ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`;
          pen = true; lastIdx = i;
        });
        if (!d) return;
        root.append(svg('path', { class: 'line', d, style: `stroke:${s.color}` }));
        const ex = sx(lastIdx), ey = sy(s.values[lastIdx]);
        root.append(svg('circle', { class: 'dot', cx: ex, cy: ey, r: 4, style: `fill:${s.color}` }));
        ends.push({ s, x: ex, y: ey });
      });
      // direct end labels on wide charts; when two would collide, keep the first and let the legend carry the rest
      if (wide) {
        ends.sort((a, b) => a.y - b.y);
        let lastY = -Infinity;
        ends.forEach((e) => {
          if (e.y - lastY < 14) return;
          lastY = e.y;
          root.append(svg('text', { class: 'endlabel', x: e.x + 9, y: e.y + 4, text: e.s.name }));
        });
      }

      // hover layer: crosshair finds the nearest X, tooltip lists every series
      const cross = svg('line', { class: 'crosshair', x1: 0, x2: 0, y1: m.t, y2: m.t + ph, visibility: 'hidden' });
      const hoverDots = series.map((s) => svg('circle', { class: 'hover-dot', r: 5, style: `fill:${s.color}`, visibility: 'hidden' }));
      root.append(cross, ...hoverDots);
      const hit = svg('rect', { class: 'hit', x: m.l - 10, y: m.t, width: pw + 20, height: ph + m.b });
      root.append(hit);
      const move = (ev) => {
        const r = root.getBoundingClientRect();
        const px = ((ev.clientX - r.left) / r.width) * W;
        let i = Math.round(((px - m.l) / pw) * (x.length - 1));
        i = Math.max(0, Math.min(x.length - 1, i));
        const cx = sx(i);
        cross.setAttribute('x1', cx); cross.setAttribute('x2', cx); cross.setAttribute('visibility', 'visible');
        const rows = [];
        series.forEach((s, k) => {
          const v = s.values[i];
          if (v == null) { hoverDots[k].setAttribute('visibility', 'hidden'); return; }
          hoverDots[k].setAttribute('cx', cx); hoverDots[k].setAttribute('cy', sy(v)); hoverDots[k].setAttribute('visibility', 'visible');
          rows.push({ value: format(v), name: s.name, color: s.color });
        });
        showTip(ev.clientX, ev.clientY, `Turn ${x[i].replace(/^T/, '')}`, rows);
      };
      const leave = () => { cross.setAttribute('visibility', 'hidden'); hoverDots.forEach((d) => d.setAttribute('visibility', 'hidden')); hideTip(); };
      hit.addEventListener('pointermove', move);
      hit.addEventListener('pointerdown', move);
      hit.addEventListener('pointerleave', leave);

      const legend = el('ul', { class: 'legend' }, series.map((s) => el('li', {}, el('i', { class: 'key', style: `background:${s.color}` }), s.name)));
      const plot = el('div', {}, root, legend);
      const table = dataTable(['Turn', ...series.map((s) => s.name)],
        x.map((lab, i) => [lab, ...series.map((s) => s.values[i] == null ? '–' : format(s.values[i]))]));
      return { plot, table };
    });
  }

  /** Horizontal bars, one per item, colored by the entity (seat). items: [{name, color, value, label, note}] */
  function barChart({ title, subtitle, items, max, format, tableHeader }) {
    return chartFigure(title, subtitle, (W) => {
      const rowH = 38, m = { t: 8, r: 64, b: 8, l: Math.min(150, Math.round(W * 0.32)) };
      const H = m.t + items.length * rowH + m.b, pw = W - m.l - m.r, th = 20;
      const xmax = max != null ? max : niceMax(Math.max(0, ...items.map((i) => i.value || 0)));
      const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': title });
      root.append(svg('line', { class: 'baseline', x1: m.l, x2: m.l, y1: m.t, y2: H - m.b }));
      items.forEach((it, i) => {
        const y = m.t + i * rowH + (rowH - th) / 2;
        const w = Math.max(0, ((it.value || 0) / xmax) * pw);
        const g = svg('g', { class: 'bar-row', tabindex: '0', role: 'img', 'aria-label': `${it.name}: ${it.label}` });
        g.append(svg('rect', { class: 'hit', x: 0, y: m.t + i * rowH, width: W, height: rowH }));
        if (w > 0) {
          const rr = Math.min(4, w);
          const d = `M${m.l},${y}h${w - rr}a${rr},${rr} 0 0 1 ${rr},${rr}v${th - 2 * rr}a${rr},${rr} 0 0 1 -${rr},${rr}h-${w - rr}z`;
          g.append(svg('path', { class: 'bar', d, style: `fill:${it.color}` }));
        }
        g.append(svg('text', { class: 'bar-cat', x: m.l - 10, y: y + th / 2 + 4, 'text-anchor': 'end', text: it.name }));
        g.append(svg('text', { class: 'bar-label', x: m.l + w + 8, y: y + th / 2 + 4, text: it.label }));
        const show = (ev) => showTip(ev.clientX, ev.clientY, it.name, [{ value: it.label, name: it.note || title, color: it.color }]);
        g.addEventListener('pointermove', show);
        g.addEventListener('pointerleave', hideTip);
        g.addEventListener('focus', (ev) => { const r = g.getBoundingClientRect(); showTip(r.left + r.width / 2, r.top, it.name, [{ value: it.label, name: it.note || title, color: it.color }]); });
        g.addEventListener('blur', hideTip);
        root.append(g);
      });
      const plot = el('div', {}, root);
      const table = dataTable(['Deck', tableHeader || title, 'Note'], items.map((it) => [it.name, it.label, it.note || '']));
      return { plot, table };
    });
  }

  // ---------- card images ----------
  function cardThumb(name, cards, badge) {
    const c = cards[name];
    const img = c && c.image_uris && c.image_uris.small
      ? el('img', { src: c.image_uris.small, alt: name, loading: 'lazy', width: 88, height: 123 })
      : el('div', { class: 'noimg', text: name });
    const inner = [img, el('span', { class: 'n', text: name, title: name })];
    if (badge != null) inner.push(el('span', { class: 'badge', text: badge }));
    return c && c.scryfall_uri
      ? el('a', { class: 'thumb', href: c.scryfall_uri, target: '_blank', rel: 'noopener', title: `${name} on Scryfall` }, inner)
      : el('div', { class: 'thumb' }, inner);
  }

  // ---------- render ----------
  function renderRun(run, rollup, cards) {
    const decks = rollup.deck_stats || [];
    const names = decks.map((d) => shortName(d.name) || d.id);
    const turns = Array.from({ length: rollup.max_turn || 12 }, (_, i) => turnLabel(i + 1));

    // meta line
    const meta = $('#meta');
    meta.replaceChildren(
      el('span', {}, el('b', { text: String(rollup.games) }), ` games · ${rollup.completed_games ?? '–'} decided · ${rollup.drawn_games ?? 0} draws`),
      el('span', {}, 'Forge ', el('b', { text: rollup.forge_version || '?' })),
      el('span', {}, 'avg game ', el('b', { text: `${num(rollup.avg_game_turns, 0)} turns` }), ` (${num(rollup.avg_game_seconds, 0)} s)`),
      el('span', {}, 'generated ', el('b', { text: (rollup.generated || '').replace('T', ' ').replace('Z', ' UTC') })),
      rollup.pod ? el('span', {}, 'pod ', el('b', { text: rollup.pod })) : null);
    meta.hidden = false;

    // deck cards (the KPI row)
    const deckSec = $('#decks');
    deckSec.replaceChildren(...decks.map((d, i) => {
      const cmdr = (d.commanders || [])[0];
      const c = cmdr ? cards[cmdr] : null;
      const art = c && c.image_uris && c.image_uris.normal
        ? el('a', { href: c.scryfall_uri || '#', target: '_blank', rel: 'noopener', title: `${cmdr} on Scryfall` }, el('img', { src: c.image_uris.normal, alt: cmdr, loading: 'lazy' }))
        : el('div', { class: 'noimg', text: cmdr || 'no commander' });
      const losses = Object.entries(d.loss_reasons || {}).map(([k, v]) => `${lossLabel(k)} ${v}`);
      if (d.draws) losses.push(`draw ${d.draws}`);
      return el('article', { class: 'deck', style: `--seat:${seatColor(d.seat)}` },
        el('div', { class: 'art' }, art),
        el('div', { class: 'who' },
          el('div', { class: 'name' }, el('i', { class: 'swatch' }), names[i]),
          el('div', { class: 'cmdr', text: (d.commanders || []).join(' + ') }),
          el('div', { class: 'win' }, pct(d.win_rate), el('small', { text: `${d.wins}/${d.games} games` })),
          el('dl', {},
            el('dt', { text: 'Turns played' }), el('dd', { text: num(d.avg_turns_played) }),
            el('dt', { text: 'Commander out' }), el('dd', { text: d.commander && d.commander.avg_first_cast_turn != null ? `T${num(d.commander.avg_first_cast_turn)}` : 'never' }),
            el('dt', { text: 'Mulligans' }), el('dd', { text: pct(d.mulligan_rate) }),
            el('dt', { text: 'Opening lands' }), el('dd', { text: num(d.opening_hand_lands_avg) }),
            el('dt', { text: 'Damage dealt' }), el('dd', { text: `${num(d.damage && d.damage.dealt_per_game, 0)}/game` }),
            el('dt', { text: 'Never cast' }), el('dd', { text: String((d.drawn_never_cast || []).length) }),
            el('div', { class: 'losses', text: losses.length ? `Lost to: ${losses.join(' · ')}` : 'Never lost a game' }))));
    }));
    deckSec.hidden = false;

    // charts
    const series = (key) => decks.map((d, i) => ({ name: names[i], color: seatColor(d.seat), values: (d[key] || []).slice(0, turns.length) }));
    charts.length = 0;
    const chartSec = $('#charts');
    chartSec.replaceChildren(
      lineChart({ title: 'Land drop rate by turn', subtitle: 'Share of games with a land played on the deck\'s own turn', x: turns,
        series: series('land_drop_rate'), yMax: 1, format: (v) => pct(v) }),
      lineChart({ title: 'Lands on the battlefield', subtitle: 'Average at the start of the deck\'s own turn', x: turns,
        series: series('lands_by_turn'), format: (v) => num(v, 1) }),
      lineChart({ title: 'Life total by turn', subtitle: 'Average at the start of the deck\'s own turn', x: turns,
        series: series('life_by_turn'), yMax: 40, format: (v, axis) => num(v, axis ? 0 : 1) }),
      lineChart({ title: 'Cards in hand', subtitle: 'Average at the start of the deck\'s own turn', x: turns,
        series: series('hand_by_turn'), format: (v) => num(v, 1) }),
      barChart({ title: 'Commander first cast', subtitle: 'Average own turn of the first cast from the command zone (lower is faster)',
        items: decks.map((d, i) => ({ name: names[i], color: seatColor(d.seat), value: d.commander ? d.commander.avg_first_cast_turn : null,
          label: d.commander && d.commander.avg_first_cast_turn != null ? `T${num(d.commander.avg_first_cast_turn)}` : 'never',
          note: d.commander ? `${num(d.commander.casts_per_game)} casts/game · never cast in ${d.commander.never_cast_games} game(s)` : '' })),
        format: (v) => num(v), tableHeader: 'Avg first cast turn' }),
      barChart({ title: 'Win rate', subtitle: `Share of ${rollup.games} games won; ${pct(1 / Math.max(1, decks.length))} is an even pod`,
        items: decks.map((d, i) => ({ name: names[i], color: seatColor(d.seat), value: d.win_rate, label: pct(d.win_rate),
          note: `${d.wins} wins, ${d.losses} losses, ${d.draws} draws` })),
        max: 1, format: (v) => pct(v), tableHeader: 'Win rate' }));
    chartSec.hidden = false;
    relayout(true);

    // card lists
    const cardSec = $('#cards');
    cardSec.replaceChildren(el('h2', { text: 'Cards' }), ...decks.map((d, i) => {
      const byCast = (d.cards || []).filter((c) => !c.land && c.cast > 0).sort((a, b) => b.cast - a.cast).slice(0, 10);
      const never = (d.drawn_never_cast || []).slice(0, 16);
      const lands = (d.cards || []).filter((c) => c.land);
      return el('details', { class: 'cardgroup', style: `--seat:${seatColor(d.seat)}`, open: i === 0 ? '' : null },
        el('summary', {}, el('i', { class: 'swatch' }), names[i], el('span', { text: `${(d.cards || []).length} distinct cards · ${lands.reduce((n, c) => n + (c.count || 0), 0)} lands` })),
        el('h4', { text: 'Most cast' }),
        el('div', { class: 'thumbs' }, byCast.length ? byCast.map((c) => cardThumb(c.name, cards, `${num(c.cast / Math.max(1, d.games), 1)}×`)) : el('p', { class: 'tag', text: 'Nothing cast yet' })),
        el('h4', { text: `Drawn but never cast (${(d.drawn_never_cast || []).length})` }),
        el('div', { class: 'thumbs' }, never.length ? never.map((n) => cardThumb(n, cards)) : el('p', { class: 'tag', text: 'Every drawn spell was cast at least once' })));
    }));
    cardSec.hidden = false;

    // games table
    const gamesSec = $('#games');
    const rows = (rollup.game_summaries || []).map((g) => [
      `${g.shard ? g.shard.replace('shard-', 's') + '·' : ''}${g.index}`, String(g.seed ?? ''), g.first_seat != null ? names[g.first_seat] : '–',
      String(g.turns ?? ''), g.winner != null ? names[g.winner] : '—', endLabel(g.reason), num((g.duration_ms || 0) / 1000, 0)]);
    gamesSec.replaceChildren(el('h2', { text: `Games (${rows.length})` }),
      dataTable(['Game', 'Seed', 'First seat', 'Turns', 'Winner', 'End', 'Seconds'], rows));
    gamesSec.hidden = false;
  }

  function lossLabel(k) {
    return ({ LifeReachedZero: 'life', CommanderDamage: 'commander damage', Poisoned: 'poison', Milled: 'decking',
      SpellEffect: 'spell effect', OpponentWon: 'opponent win con', Conceded: 'concession', Draw: 'draw', Unknown: 'unknown' })[k] || k;
  }
  function endLabel(r) {
    return ({ AllOpponentsLost: 'last standing', TurnCap: 'turn cap (draw)', Timeout: 'clock (draw)', Draw: 'draw',
      WinsGameSpellEffect: 'spell win', Exception: 'engine error' })[r] || r || '';
  }

  async function main() {
    const status = $('#status');
    try {
      const index = await loadJson(DATA + 'index.json');
      const runs = (index.runs || []).slice();
      if (!runs.length) throw new Error('index.json lists no runs yet');
      const select = $('#run-select');
      select.replaceChildren(...runs.map((r) => el('option', { value: r.id, text: `${r.id} · ${r.games} games` })));
      const wanted = qs.get('run');
      let current = runs.find((r) => r.id === wanted) || runs[0];
      select.value = current.id;
      const cards = (await loadJson(DATA + 'cards/scryfall-cache.json', true)) || {};
      const show = async (run) => {
        status.hidden = false; status.textContent = `Loading ${run.id}…`; status.classList.remove('error');
        const rollup = await loadJson(DATA + run.path);
        renderRun(run, rollup, cards);
        status.hidden = true;
        const u = new URL(location.href); u.searchParams.set('run', run.id); history.replaceState(null, '', u);
      };
      select.addEventListener('change', () => { current = runs.find((r) => r.id === select.value) || runs[0]; show(current).catch(fail); });
      await show(current);
    } catch (err) {
      fail(err);
    }
    function fail(err) {
      status.hidden = false;
      status.classList.add('error');
      status.textContent = `Could not load data from ${DATA}: ${err.message}`;
    }
  }
  main();
})();
