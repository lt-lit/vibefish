/* Vibefish dashboard. Vanilla JS, no build step.
 * Data contract (base URL from ?data=; otherwise ./data/ then ../demo-data/, whichever has an index.json):
 *   index.json                 {"runs":[{id, generated, forge_version, pod, games, path}]}
 *   <run.path>                 rollup.json written by runner/rollup.py (a pod: four decks in fixed seats) or by
 *                              runner/league.py (kind "league": many decks over random tables; league view below)
 *   <run dir>/scorecard.json   calibration against Playgroup.gg's human references, from runner/scorecard.py (optional)
 *   cards/scryfall-cache.json  {name: {image_uris:{small,normal}, scryfall_uri, ...}} (optional)
 *   bots.json                  the decks with a per-deck bot: stock against playbook on the same tables, goldfish kill
 *                              turns, the human win rate; from runner/bots.py (optional; shown above every run)
 */
(() => {
  'use strict';

  const qs = new URLSearchParams(location.search);
  const DATA_CANDIDATES = qs.get('data') ? [qs.get('data')] : ['./data', '../demo-data'];
  let DATA = DATA_CANDIDATES[0].replace(/\/+$/, '') + '/';
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
      // right margin fits the longest value label (about 6.8 px per character at 12 px), so labels never leave the chart
      const longest = Math.max(4, ...items.map((i) => String(i.label || '').length));
      const rowH = 38, m = { t: 8, r: Math.min(Math.round(W * 0.45), longest * 6.8 + 16), b: 8, l: Math.min(150, Math.round(W * 0.32)) };
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
  function renderRun(run, rollup, cards, scorecard) {
    const decks = rollup.deck_stats || [];
    const names = decks.map((d) => shortName(d.name) || d.id);
    const turns = Array.from({ length: rollup.max_turn || 12 }, (_, i) => turnLabel(i + 1));

    // meta line
    const meta = $('#meta');
    meta.replaceChildren(...[
      el('span', {}, el('b', { text: String(rollup.games) }), ` games · ${rollup.completed_games ?? '–'} decided · ${rollup.drawn_games ?? 0} draws`),
      el('span', {}, 'Forge ', el('b', { text: rollup.forge_version || '?' })),
      el('span', {}, 'avg game ', el('b', { text: `${num(rollup.avg_game_turns, 0)} turns` }), ` (${num(rollup.avg_game_seconds, 0)} s)`),
      el('span', {}, 'generated ', el('b', { text: (rollup.generated || '').replace('T', ' ').replace('Z', ' UTC') })),
      rollup.pod ? el('span', {}, 'pod ', el('b', { text: rollup.pod })) : null,
      rollup.mc && rollup.mc !== 'off' ? el('span', {}, 'Flat Monte Carlo ', el('b', { text: rollup.mc_available === false ? 'requested, unavailable' : rollup.mc })) : null,
    ].filter(Boolean));
    meta.hidden = false;

    // deck cards (the KPI row)
    const deckSec = $('#decks');
    deckSec.className = 'decks';
    $('#league').hidden = true;
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
            el('dt', { text: 'Cmdr out' }), el('dd', { text: d.commander && d.commander.avg_first_cast_turn != null ? `T${num(d.commander.avg_first_cast_turn)}` : 'never' }),
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
    if (rollup.arms && rollup.arms.arms) {
      const arms = Object.entries(rollup.arms.arms);
      chartSec.append(barChart({ title: 'AI arms (A/B)',
        subtitle: `Share of games won by each AI profile's seats; profiles rotate across seats every game. Even would be ${pct(arms[0][1].expected_game_win_share)}.`
          + (rollup.mc_summary ? ` Monte Carlo settled ${rollup.mc_summary.by_rollouts} of ${rollup.mc_summary.decisions} decisions by rollouts and overrode the heuristic ${rollup.mc_summary.overrides} times (${pct(rollup.mc_summary.override_rate, 1)}); ${rollup.mc_summary.too_slow} ran out of time at ${rollup.mc_summary.avg_rollout_ms} ms per rollout.` : ''),
        items: arms.map(([name, a], i) => ({ name, color: `var(--s${(i % MAX_SERIES) + 1})`, value: a.game_win_share,
          label: `${pct(a.game_win_share)}${a.game_win_share_ci95 ? ` (${pct(a.game_win_share_ci95[0])}–${pct(a.game_win_share_ci95[1])})` : ''}`,
          note: `${a.wins} wins in ${a.games} games · ${pct(a.seat_win_rate, 1)} per seat · by deck: ${Object.entries(a.by_deck).map(([d, v]) => `${shortName((decks.find((x) => x.id === d) || {}).name) || d} ${v.wins}/${v.games}`).join(', ')}` })),
        max: 1, format: (v) => pct(v), tableHeader: 'Game win share (95% interval)' }));
    }
    if (scorecard && scorecard.metrics) {
      chartSec.append(calibrationCard(scorecard, names));
    }
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

  /** Sim versus human reference numbers (Playgroup.gg), as a table card. */
  function calibrationCard(sc, names, withDecks = true) {
    const m = sc.metrics;
    const rows = [];
    const add = (metric, sim, human, note) => rows.push([metric, sim, human, note || '']);
    if (m.first_seat_win_rate) add('First seat wins', pct(m.first_seat_win_rate.sim, 1), pct(m.first_seat_win_rate.human, 1), `${m.first_seat_win_rate.sim_games} games; even is ${pct(m.first_seat_win_rate.even)}`);
    if (m.first_seat_win_rate && m.first_seat_win_rate.sim_by_seat) add('Win rate by seat 1–4', m.first_seat_win_rate.sim_by_seat.map((v) => num(v * 100, 1)).join(' / ') + '%', (m.first_seat_win_rate.human_by_seat || []).map((v) => num(v * 100, 1)).join(' / ') + '%', 'human seats from 257,261 four-player games');
    if (m.mulligans_taken) add('Decks that mulligan', pct(m.mulligans_taken.sim_any_mulligan, 1), pct(m.mulligans_taken.human_any_mulligan), `${m.mulligans_taken.sim_seat_games} seat-games`);
    if (m.opening_hand_lands) add('Lands in kept hand', num(m.opening_hand_lands.sim_mean, 2), num(m.opening_hand_lands.human_mean, 2), `${m.opening_hand_lands.sim_hands} hands`);
    if (m.rounds_per_game) add('Rounds per game', num(m.rounds_per_game.sim_mean, 1), num(m.rounds_per_game.human_mean, 2), 'a round is one turn for each player');
    if (withDecks) (m.precon_win_rate && m.precon_win_rate.rows || []).forEach((r) => { if (r.human_win_rate != null) add(`${r.deck} win rate`, pct(r.sim_win_rate, 1), pct(r.human_win_rate, 1), `${r.sim_games} sim games vs ${r.human_games} human stock games`); });
    if (m.precon_win_rate && m.precon_win_rate.spearman_rank_correlation != null) add('Precon rank correlation', String(m.precon_win_rate.spearman_rank_correlation), '1.0', `${m.precon_win_rate.decks_compared} decks; the human table ranks stock precons against mixed tables`);
    if (m.precon_win_rate && m.precon_win_rate.mean_abs_difference != null) add('Mean gap in precon win rate', `${(m.precon_win_rate.mean_abs_difference * 100).toFixed(1)} pts`, '0', `spread across precons: sim ${(m.precon_win_rate.sim_sd * 100).toFixed(1)} pts, human ${(m.precon_win_rate.human_sd * 100).toFixed(1)} pts`);
    const fig = el('figure', { class: 'chart wide calibration' },
      el('figcaption', {}, el('div', {}, el('h3', { text: 'Calibration against human games' }),
        el('p', { text: `Sim numbers next to Playgroup.gg's tracked Commander games (reference copied ${sc.reference_retrieved || ''}). Likeness, not strength.` }))),
      el('div', { class: 'table-view' }, dataTable(['Metric', 'Sim', 'Human', 'Note'], rows)));
    return fig;
  }


  // ---------- league view: many precons over random four-player tables ----------
  const signed = (v, d = 1) => v == null ? '–' : `${v >= 0 ? '+' : '−'}${Math.abs(v * 100).toFixed(d)}`;

  function renderLeague(run, rollup, cards, scorecard) {
    const L = rollup.league || {};
    const decks = rollup.deck_stats || [];
    const byId = new Map(decks.map((d) => [d.id, d]));
    const label = (id) => { const d = byId.get(id); return d ? (shortName(d.name) || id) : id; };
    const sc = scorecard && scorecard.metrics ? scorecard.metrics : {};
    const pw = sc.precon_win_rate || {};
    const scRows = pw.rows || [];
    const matched = scRows.filter((r) => r.human_win_rate != null);

    // meta line
    const meta = $('#meta');
    meta.replaceChildren(...[
      el('span', {}, el('b', { text: String(rollup.games) }), ` of ${L.games_scheduled ?? '–'} games · ${rollup.completed_games ?? '–'} decided · ${rollup.drawn_games ?? 0} draws`),
      el('span', {}, el('b', { text: String(L.decks ?? decks.length) }), ` precons · ${num(L.games_per_deck_avg, 1)} games each`),
      el('span', {}, 'Forge ', el('b', { text: rollup.forge_version || '?' })),
      el('span', {}, 'avg game ', el('b', { text: `${num(rollup.avg_game_turns, 0)} turns` }), ` (${num(rollup.avg_game_seconds, 0)} s)`),
      el('span', {}, 'generated ', el('b', { text: (rollup.generated || '').replace('T', ' ').replace('Z', ' UTC') })),
      rollup.profile && rollup.profile !== 'Default' ? el('span', {}, 'profile ', el('b', { text: rollup.profile })) : null,
      rollup.mc && rollup.mc !== 'off' ? el('span', {}, 'Flat Monte Carlo ', el('b', { text: rollup.mc })) : null,
    ].filter(Boolean));
    meta.hidden = false;

    // headline tiles
    const tiles = $('#decks');
    tiles.className = 'tiles';
    const tile = (value, title, note) => el('article', { class: 'tile' }, el('div', { class: 'value', text: value }), el('div', { class: 'label', text: title }), note ? el('div', { class: 'note', text: note }) : null);
    tiles.replaceChildren(
      tile(pw.spearman_rank_correlation != null ? String(pw.spearman_rank_correlation) : '–', 'Rank correlation with human results',
        pw.decks_compared ? `Spearman over ${pw.decks_compared} precons: 1.0 is the same order, 0 is no relation${pw.well_measured ? `; ${pw.well_measured.spearman_rank_correlation} over the ${pw.well_measured.decks_compared} with 100+ human games` : ''}` : 'no precon matched the human table'),
      tile(pw.mean_abs_difference != null ? `${(pw.mean_abs_difference * 100).toFixed(1)} pts` : '–', 'Mean gap in win rate', 'Average absolute difference between a precon\'s sim and human win rate'),
      tile(pw.sim_sd != null ? `${(pw.sim_sd * 100).toFixed(1)} vs ${(pw.human_sd * 100).toFixed(1)}` : '–', 'Spread of win rates, sim vs human', 'Standard deviation across precons, in points: a wider sim spread means the AI exaggerates deck differences'),
      tile(sc.rounds_per_game ? `${num(sc.rounds_per_game.sim_mean, 1)} vs ${num(sc.rounds_per_game.human_mean, 2)}` : '–', 'Rounds per game, sim vs human', 'A round is one turn for each player'));
    tiles.hidden = false;

    // charts: the dot plot and the calibration card
    charts.length = 0;
    const chartSec = $('#charts');
    const points = matched.map((r) => ({ name: r.deck, x: r.human_win_rate, y: r.sim_win_rate, ci: r.sim_win_rate_ci95, games: r.sim_games, humanGames: r.human_games, tier: r.human_tier }));
    chartSec.replaceChildren();
    if (points.length) {
      const fig = scatterChart({ title: 'Sim versus human win rate, one dot per precon',
        subtitle: `The thin bar is the sim's 95% interval; the dashed diagonal is perfect agreement; the dotted lines mark 25%, an even four-player table. Human rates are Playgroup.gg's stock-precon results (copied ${scorecard.reference_retrieved || ''}).`,
        points, labelCount: 6 });
      fig.classList.add('wide');
      chartSec.append(fig);
    }
    if (scorecard && scorecard.metrics) chartSec.append(calibrationCard(scorecard, [], false));
    chartSec.hidden = false;
    relayout(true);

    // the precon table
    leagueTable(scRows, byId, cards, L);
    $('#cards').hidden = true;

    // games, built when opened
    const gamesSec = $('#games');
    const games = rollup.game_summaries || [];
    const det = el('details', {}, el('summary', { text: `Games (${games.length})` }));
    let built = false;
    det.addEventListener('toggle', () => {
      if (built || !det.open) return;
      built = true;
      const rows = games.map((g) => [String(g.game ?? g.index), `${g.cycle ?? '–'}/${g.round ?? '–'}`, String(g.seed ?? ''),
        (g.seats || []).map((id) => label(id)).join(' · '), g.first_seat != null && g.seats ? label(g.seats[g.first_seat]) : '–',
        String(g.turns ?? ''), g.winner_id ? label(g.winner_id) : '—', endLabel(g.reason), num((g.duration_ms || 0) / 1000, 0)]);
      det.append(dataTable(['Game', 'Cycle/round', 'Seed', 'Table (seats 1–4)', 'First seat', 'Turns', 'Winner', 'End', 'Seconds'], rows));
    });
    gamesSec.replaceChildren(det);
    gamesSec.hidden = false;
  }

  /** Sortable, filterable table of every precon in the league, with the human reference where there is one. */
  function leagueTable(rows, byId, cards, L) {
    const sec = $('#league');
    const cols = [
      { key: 'human_rank', label: '#', get: (r) => r.human_rank, fmt: (r) => r.human_rank == null ? '–' : String(Math.round(r.human_rank)) },
      { key: 'deck', label: 'Precon', get: (r) => r.deck, left: true, cell: (r) => deckCell(r, byId, cards) },
      { key: 'set', label: 'Set', get: (r) => (byId.get(r.id) || {}).set || '', left: true, fmt: (r) => (byId.get(r.id) || {}).set || '' },
      { key: 'sim_win_rate', label: 'Sim win rate', get: (r) => r.sim_win_rate, fmt: (r) => `${pct(r.sim_win_rate, 1)}${r.sim_win_rate_ci95 ? ` (${pct(r.sim_win_rate_ci95[0])}–${pct(r.sim_win_rate_ci95[1])})` : ''}` },
      { key: 'sim_games', label: 'Games', get: (r) => r.sim_games, fmt: (r) => String(r.sim_games) },
      { key: 'human_win_rate', label: 'Human win rate', get: (r) => r.human_win_rate, fmt: (r) => r.human_win_rate == null ? '–' : `${pct(r.human_win_rate, 1)} (${r.human_games})` },
      { key: 'difference', label: 'Sim − human', get: (r) => r.difference, fmt: (r) => signed(r.difference) },
      { key: 'human_tier', label: 'Tier', get: (r) => r.human_tier || '', fmt: (r) => r.human_tier || '–' },
    ];
    const state = { key: 'human_win_rate', dir: -1, q: '' };
    const search = el('input', { type: 'search', placeholder: 'Filter precons', 'aria-label': 'Filter precons' });
    const wrap = el('div', { class: 'table-view' });
    const draw = () => {
      const q = state.q.trim().toLowerCase();
      const col = cols.find((c) => c.key === state.key);
      const data = rows.filter((r) => !q || [r.deck, ...(byId.get(r.id) || {}).commanders || [], (byId.get(r.id) || {}).set || ''].join(' ').toLowerCase().includes(q))
        .sort((a, b) => {
          const va = col.get(a), vb = col.get(b);
          if (va == null && vb == null) return 0;
          if (va == null) return 1;
          if (vb == null) return -1;
          return (typeof va === 'string' ? va.localeCompare(vb) : va - vb) * state.dir;
        });
      const head = el('tr', {}, cols.map((c) => {
        const th = el('th', { scope: 'col', class: `sortable${c.key === state.key ? ' sorted' : ''}${c.key === state.key && state.dir > 0 ? ' asc' : ''}`, text: c.label, title: 'Sort' });
        if (c.left) th.style.textAlign = 'left';
        th.addEventListener('click', () => { if (state.key === c.key) state.dir = -state.dir; else { state.key = c.key; state.dir = c.key === 'deck' || c.key === 'set' || c.key === 'human_rank' ? 1 : -1; } draw(); });
        return th;
      }));
      const body = el('tbody', {}, data.map((r) => el('tr', {}, cols.map((c) => c.cell ? c.cell(r) : el('td', { text: c.fmt(r), style: c.left ? 'text-align:left' : null })))));
      wrap.replaceChildren(el('table', {}, el('thead', {}, head), body));
    };
    search.addEventListener('input', () => { state.q = search.value; draw(); });
    sec.replaceChildren(
      el('div', { class: 'head' },
        el('div', {}, el('h2', { text: `Precons (${rows.length})` }),
          el('p', { class: 'tag', text: `${L.description || ''} Sim win rates carry a 95% Wilson interval; human rates are stock-precon results on Playgroup.gg with their game counts.` })),
        search),
      wrap);
    draw();
    sec.hidden = false;
  }

  function deckCell(r, byId, cards) {
    const d = byId.get(r.id) || {};
    const cmdrs = d.commanders || [];
    const c = cmdrs[0] ? cards[cmdrs[0]] : null;
    const img = c && c.image_uris && c.image_uris.small
      ? el('img', { src: c.image_uris.small, alt: cmdrs[0], loading: 'lazy', width: 28, height: 39 })
      : el('div', { class: 'noimg' });
    const name = c && c.scryfall_uri ? el('a', { class: 'n', href: c.scryfall_uri, target: '_blank', rel: 'noopener', title: `${cmdrs[0]} on Scryfall`, text: r.deck }) : el('span', { class: 'n', text: r.deck });
    return el('td', { class: 'deckcell' }, el('div', { class: 'row' }, img, el('div', {}, name, el('div', { class: 'c', text: cmdrs.join(' + ') }))));
  }

  /** Dot plot: sim win rate against the human one, one dot per precon, the sim's 95% interval as a thin bar. */
  function scatterChart({ title, subtitle, points, labelCount }) {
    return chartFigure(title, subtitle, (W) => {
      const H = Math.max(280, Math.min(520, Math.round(W * 0.7)));
      const m = { t: 16, r: 28, b: 48, l: 50 };
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const maxV = niceMax(Math.max(0.3, ...points.flatMap((p) => [p.x, p.ci ? p.ci[1] : p.y])));
      const sx = (v) => m.l + (v / maxV) * pw, sy = (v) => m.t + ph - (v / maxV) * ph;
      const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': title });
      const ticks = maxV <= 0.5 ? Math.round(maxV / 0.1) : 4;
      for (let k = 0; k <= ticks; k++) {
        const v = (maxV * k) / ticks;
        root.append(svg('line', { class: k === 0 ? 'baseline' : 'gridline', x1: m.l, x2: m.l + pw, y1: sy(v), y2: sy(v) }));
        root.append(svg('text', { class: 'tick', x: m.l - 6, y: sy(v) + 4, 'text-anchor': 'end', text: pct(v) }));
        root.append(svg('line', { class: k === 0 ? 'baseline' : 'gridline', x1: sx(v), x2: sx(v), y1: m.t, y2: m.t + ph }));
        root.append(svg('text', { class: 'tick', x: sx(v), y: m.t + ph + 16, 'text-anchor': 'middle', text: pct(v) }));
      }
      root.append(svg('line', { class: 'even', x1: sx(0.25), x2: sx(0.25), y1: m.t, y2: m.t + ph }));
      root.append(svg('line', { class: 'even', x1: m.l, x2: m.l + pw, y1: sy(0.25), y2: sy(0.25) }));
      root.append(svg('line', { class: 'agree', x1: sx(0), y1: sy(0), x2: sx(maxV), y2: sy(maxV) }));
      root.append(svg('text', { class: 'tick', x: m.l + pw, y: H - 6, 'text-anchor': 'end', text: 'human win rate (Playgroup.gg, stock precons)' }));
      root.append(svg('text', { class: 'tick', x: 12, y: m.t + ph / 2, 'text-anchor': 'middle', transform: `rotate(-90 12 ${m.t + ph / 2})`, text: 'sim win rate' }));
      points.forEach((p) => { if (p.ci) root.append(svg('line', { class: 'ci', x1: sx(p.x), x2: sx(p.x), y1: sy(p.ci[0]), y2: sy(p.ci[1]) })); });
      const dots = points.map((p) => svg('circle', { class: 'pt', cx: sx(p.x), cy: sy(p.y), r: 4.5 }));
      root.append(...dots);
      // direct labels for the largest gaps between sim and human; skip a label that would sit on another
      const placed = [];
      points.slice().sort((a, b) => Math.abs(b.y - b.x) - Math.abs(a.y - a.x)).slice(0, labelCount || 5).forEach((p) => {
        let x = sx(p.x) + 8, y = sy(p.y) + 4;
        const anchorEnd = x + p.name.length * 6.5 > W - 4;
        if (anchorEnd) x = sx(p.x) - 8;
        if (placed.some((q) => Math.abs(q.y - y) < 13 && Math.abs(q.x - x) < 140)) return;
        placed.push({ x, y });
        root.append(svg('text', { class: 'ptlabel', x, y, 'text-anchor': anchorEnd ? 'end' : 'start', text: p.name }));
      });
      const hit = svg('rect', { class: 'hit', x: 0, y: 0, width: W, height: H });
      root.append(hit);
      let hot = null;
      const move = (ev) => {
        const r = root.getBoundingClientRect();
        const px = ((ev.clientX - r.left) / r.width) * W, py = ((ev.clientY - r.top) / r.height) * H;
        let best = null, bd = 20 * 20;
        points.forEach((p, i) => { const dx = sx(p.x) - px, dy = sy(p.y) - py, d2 = dx * dx + dy * dy; if (d2 < bd) { bd = d2; best = i; } });
        if (hot != null && hot !== best) dots[hot].classList.remove('hot');
        hot = best;
        if (best == null) { hideTip(); return; }
        dots[best].classList.add('hot');
        const p = points[best];
        showTip(ev.clientX, ev.clientY, p.name, [
          { value: pct(p.y, 1), name: `sim, ${p.games} games${p.ci ? ` (${pct(p.ci[0])}–${pct(p.ci[1])})` : ''}`, color: 'var(--s1)' },
          { value: pct(p.x, 1), name: `human, ${p.humanGames} stock games${p.tier ? `, tier ${p.tier}` : ''}`, color: 'var(--axis)' },
          { value: signed(p.y - p.x), name: 'points, sim minus human', color: 'transparent' }]);
      };
      const leave = () => { if (hot != null) dots[hot].classList.remove('hot'); hot = null; hideTip(); };
      hit.addEventListener('pointermove', move);
      hit.addEventListener('pointerdown', move);
      hit.addEventListener('pointerleave', leave);
      const plot = el('div', {}, root);
      const table = dataTable(['Precon', 'Sim', 'Human', 'Sim − human', 'Sim games', 'Human games'],
        points.slice().sort((a, b) => b.x - a.x).map((p) => [p.name, pct(p.y, 1), pct(p.x, 1), signed(p.y - p.x), String(p.games), String(p.humanGames)]));
      return { plot, table };
    });
  }

  // ---------- bots: the decks that have a per-deck playbook, stock against playbook on the same tables ----------
  function renderBots(data) {
    const sec = $('#bots');
    const bots = data.bots || [];
    if (!bots.length) return;
    const rate = (a) => a ? `${pct(a.win_rate, 1)} (${a.wins}/${a.games})` : '–';
    const rows = bots.map((b) => {
      const t = b.tables, g = b.goldfish;
      const ci = t && t.difference_ci95;
      return [
        `${b.name} · ${(b.commanders || []).join(' / ')}`,
        b.human && b.human.win_rate != null ? pct(b.human.win_rate, 1) : '–',
        t ? rate(t.stock) : '–',
        t ? rate(t.bot) : '–',
        t ? `${signed(t.difference)}${ci ? ` (${signed(ci[0], 0)} to ${signed(ci[1], 0)})` : ''}` : '–',
        g ? `${num(g.stock_kill_turn)} → ${num(g.bot_kill_turn)}` : '–',
        b.status || '',
      ];
    });
    sec.replaceChildren(
      el('div', { class: 'head' }, el('div', {},
        el('h2', { text: 'Per-deck bots' }),
        el('p', { class: 'tag', text: 'One deck in the seat, played twice at the same four-player tables: by Forge\'s stock AI and under the deck\'s own playbook (which card to cast when, which trigger to take, whom to attack). Win rates are of 200 tables unless the count says otherwise; the difference is in points with its 95% interval. Goldfish is the deck\'s kill turn against three opponents that do nothing, stock then playbook.' }))),
      el('div', { class: 'table-view' }, dataTable(['Deck', 'People', 'Stock AI', 'With playbook', 'Difference', 'Goldfish turns', 'Status'], rows)),
      el('ul', { class: 'bot-notes' }, bots.filter((b) => b.summary).map((b) => el('li', {}, el('strong', { text: `${b.name}: ` }), b.summary))));
    sec.hidden = false;
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
      let index = null;
      for (const c of DATA_CANDIDATES) {
        const base = c.replace(/\/+$/, '') + '/';
        const r = await fetch(base + 'index.json', { cache: 'no-cache' }).catch(() => null);
        if (r && r.ok) { DATA = base; index = await r.json(); break; }
      }
      if (!index) throw new Error(`no index.json under ${DATA_CANDIDATES.join(' or ')}`);
      const runs = (index.runs || []).slice();
      if (!runs.length) throw new Error('index.json lists no runs yet');
      const select = $('#run-select');
      select.replaceChildren(...runs.map((r) => el('option', { value: r.id, text: `${r.id} · ${r.games} games` })));
      const wanted = qs.get('run');
      let current = runs.find((r) => r.id === wanted) || runs[0];
      select.value = current.id;
      const cards = (await loadJson(DATA + 'cards/scryfall-cache.json', true)) || {};
      const bots = await loadJson(DATA + 'bots.json', true).catch(() => null);
      if (bots) renderBots(bots);
      const show = async (run) => {
        status.hidden = false; status.textContent = `Loading ${run.id}…`; status.classList.remove('error');
        const rollup = await loadJson(DATA + run.path);
        const scorecard = await loadJson(DATA + run.path.replace(/rollup\.json$/, 'scorecard.json'), true);
        if (rollup.kind === 'league' || rollup.league) renderLeague(run, rollup, cards, scorecard);
        else renderRun(run, rollup, cards, scorecard);
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
