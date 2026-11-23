#!/usr/bin/env python3
"""commander_kills.py RESULTS_DIR --pair BASE:CAND DECK... [--json OUT]: a commander's sure kill, turn by turn and table by table.

A session helper for the exam of `"finish_commander": true` (ab-run #66, DESIGN.md section 41); read-only. RESULTS_DIR holds
the merged run directories `ab-<entry>/arm-playbook/gNNNN` (docs/agents/shards.sh); the arm `shipped` is the entry DECK, any
other arm NAME the entry DECK@NAME. Games of harness 0.4.13 or later (the `combat` line's `cmd`).

Two readings, both from the logs alone:

  turns    for the seat under test in each arm: every turn on which only its commander gave it a sure kill of the most
           dangerous or the last opponent (`cmd` >= 21 with `through` < `life`; most dangerous by life + 2 x nonland
           permanents, ties count), with what the seat sent (at that player, at a planeswalker of that player, elsewhere,
           nothing) and who was out of the game that turn. `runner/mistakes.py` counts the same turns; where another
           opponent went out that turn it files the turn apart and not as a miss, and so does the summary here.
  tables   the tables whose two games differ first at an attack of the seat under test: the commander's kills that were on
           the table at that attack and where each opponent stood, what each game sent, who was out that turn, and who won.
           A table with no commander's kill at that attack differs for a reason that is not the option's (Forge's own
           declaration is not the same in two games on the same seed about one time in seven).
"""
import argparse, glob, gzip, json, os, sys

KINDS = {'turn', 'land', 'cast', 'resolve', 'combat', 'attack', 'block', 'damage', 'life', 'lost', 'mulligan', 'zone', 'ability', 'trigger'}


def entry(deck, arm):
    return deck if arm == 'shipped' else f'{deck}@{arm}'


def load(root, ent, idx):
    d = os.path.join(root, 'ab-' + ent, 'arm-playbook', f'g{idx:04d}')
    rj = os.path.join(d, 'run.json')
    if not os.path.exists(rj):
        return None
    run = json.load(open(rj))
    g = run['games'][0]
    fs = glob.glob(os.path.join(d, 'games', '*events*'))
    if not fs:
        return None
    op = gzip.open if fs[0].endswith('.gz') else open
    with op(fs[0], 'rt', encoding='utf-8') as f:
        evs = [json.loads(l) for l in f if l.strip()]
    evs = [e for e in evs if e['e'] in KINDS]
    ids = {x['seat']: x['id'] for x in run['decks']}
    return {'evs': evs, 'ids': ids, 'winner': next((p['seat'] for p in g['players'] if p.get('won')), None),
            'stats': g.get('playbook_stats_by_seat') or {}}


def norm(e):
    if e['e'] == 'combat':
        return {'e': 'combat', 't': e.get('t'), 'seat': e.get('seat'), 'able': e.get('able'),
                'defenders': [{k: v for k, v in d.items() if k != 'permanents'} for d in e.get('defenders') or []]}
    return e


def standing(defs):
    dg = {d['seat']: d['life'] + 2 * (d.get('permanents') or 0) for d in defs}
    top = max(dg.values())
    return {d['seat']: 'last' if len(defs) == 1 else 'top' if dg[d['seat']] == top else 'lesser' for d in defs}


def sent(evs, focus, t, ids):
    out = {'player': {}, 'planeswalker': {}}
    for x in evs:
        if x['e'] == 'attack' and x['t'] == t and x.get('seat') == focus:
            for a in x.get('attacks') or []:
                if a.get('defender_seat') is None:
                    continue
                out['planeswalker' if a.get('planeswalker') else 'player'].setdefault(ids[a['defender_seat']], []).append(a['attacker'])
    return out


def turns(g, deck):
    ids = g['ids']
    focus = next(s for s, i in ids.items() if i == deck)
    lost = {x['seat']: x['t'] for x in g['evs'] if x['e'] == 'lost'}
    rows = []
    for x in g['evs']:
        if x['e'] != 'combat' or x.get('seat') != focus:
            continue
        defs = [d for d in x.get('defenders') or [] if d['life'] > 0]
        if not defs:
            continue
        st = standing(defs)
        for d in defs:
            if (d.get('cmd') or 0) < 21 or d['through'] >= d['life'] or st[d['seat']] == 'lesser':
                continue
            s = sent(g['evs'], focus, x['t'], ids)
            opp = ids[d['seat']]
            did = ('at the player' if s['player'].get(opp) else 'at a planeswalker of that player' if s['planeswalker'].get(opp)
                   else 'elsewhere' if s['player'] or s['planeswalker'] else 'nothing sent')
            rows.append({'t': x['t'], 'opponent': opp, 'stood': st[d['seat']], 'life': d['life'], 'through': d['through'], 'cmd': d['cmd'],
                         'sent': did, 'out': lost.get(d['seat']) == x['t'], 'others_out': sorted(ids[q] for q, tt in lost.items() if tt == x['t'] and q != d['seat']),
                         'won': g['winner'] == focus})
    return rows


def table(a, b, deck, idx):
    ids = a['ids']
    focus = next(s for s, i in ids.items() if i == deck)
    ea, eb = a['evs'], b['evs']
    i = 0
    while i < min(len(ea), len(eb)) and norm(ea[i]) == norm(eb[i]):
        i += 1
    if i == len(ea) == len(eb):
        return None
    xa = ea[i] if i < len(ea) else None
    xb = eb[i] if i < len(eb) else None
    own = [x for x in (xa, xb) if x is not None and x['e'] == 'attack' and x.get('seat') == focus]
    if not own:
        return None
    t = own[0]['t']
    cb = next((x for x in eb[:i] if x['e'] == 'combat' and x.get('seat') == focus and x['t'] == t), None)
    defs = [d for d in (cb or {}).get('defenders') or [] if d['life'] > 0]
    st = standing(defs) if defs else {}
    la = {x['seat']: x['t'] for x in ea if x['e'] == 'lost'}
    lb = {x['seat']: x['t'] for x in eb if x['e'] == 'lost'}
    nxt = lambda evs: next((x['t'] for x in evs if x['e'] == 'turn' and x.get('seat') == focus and x['t'] > t), None)
    dead = lambda lost, evs: focus in lost and lost[focus] >= t and (nxt(evs) is None or lost[focus] < nxt(evs))
    return {'deck': deck, 'table': idx, 't': t,
            'opponents': [{'deck': ids[d['seat']], 'stood': st[d['seat']], 'life': d['life'], 'through': d['through'], 'cmd': d.get('cmd'), 'cmd_any': d.get('cmd_any'),
                           'life_kill': d['through'] >= d['life'], 'commander_kill': (d.get('cmd') or 0) >= 21 and d['through'] < d['life']} for d in defs],
            'base_sent': sent(ea, focus, t, ids), 'cand_sent': sent(eb, focus, t, ids),
            'base_out': sorted(ids[s] for s, tt in la.items() if tt == t and s != focus), 'cand_out': sorted(ids[s] for s, tt in lb.items() if tt == t and s != focus),
            'base_dead_before_next_turn': dead(la, ea), 'cand_dead_before_next_turn': dead(lb, eb),
            'base_won': a['winner'] == focus, 'cand_won': b['winner'] == focus,
            'cand_counters': {k: v for k, v in (b['stats'].get(deck) or {}).items() if k.startswith(('attack_kill_commander', 'attack_guard'))},
            'base_counters': {k: v for k, v in (a['stats'].get(deck) or {}).items() if k.startswith('attack_guard')}}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('results')
    ap.add_argument('decks', nargs='+')
    ap.add_argument('--pair', required=True, help='BASE:CAND, arm names (shipped is the entry DECK)')
    ap.add_argument('--tables', type=int, default=200)
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    base, cand = a.pair.split(':')
    out = {'kind': 'commander-kills', 'base': base, 'candidate': cand, 'decks': {}}
    for deck in a.decks:
        T = {base: [], cand: []}
        tabs = []
        for idx in range(1, a.tables + 1):
            ga, gb = load(a.results, entry(deck, base), idx), load(a.results, entry(deck, cand), idx)
            if ga is None or gb is None:
                continue
            for arm, g in ((base, ga), (cand, gb)):
                for r in turns(g, deck):
                    T[arm].append(dict(r, table=idx))
            r = table(ga, gb, deck, idx)
            if r:
                tabs.append(r)
        out['decks'][deck] = {'turns': T, 'tables': tabs}
        print(f'{deck}')
        for arm in (base, cand):
            rows = T[arm]
            taken = [r for r in rows if r['out']]
            other = [r for r in rows if not r['out'] and r['others_out']]
            miss = [r for r in rows if not r['out'] and not r['others_out']]
            why = {}
            for r in miss:
                why[r['sent']] = why.get(r['sent'], 0) + 1
            print(f"  {arm:10} a commander's sure kill of the most dangerous or the last opponent on {len(rows)} turns: that opponent out on {len(taken)}, "
                  f"another opponent out instead on {len(other)}, nobody out on {len(miss)}" + (' (' + ', '.join(f'{k} {v}' for k, v in sorted(why.items())) + ')' if miss else ''))
        withk = [r for r in tabs if any(o['commander_kill'] for o in r['opponents'])]
        print(f"  the seat's own attack is the first thing that differs on {len(tabs)} tables; a commander's sure kill was on the table at that attack on {len(withk)}")
        for r in tabs:
            ck = [o for o in r['opponents'] if o['commander_kill']]
            lk = [o for o in r['opponents'] if o['life_kill']]
            print(f"    table {r['table']:3} turn {r['t']:2}: " + ('; '.join(f"{o['deck']} ({o['stood']}, life {o['life']}, commander damage would be {o['cmd']})" for o in ck) or "no commander's kill")
                  + (' | a kill by life: ' + ', '.join(f"{o['deck']} ({o['stood']}, life {o['life']})" for o in lk) if lk else '')
                  + f" | {base}: out {r['base_out'] or 'nobody'}, {'won' if r['base_won'] else 'lost'}{', dead before its next turn' if r['base_dead_before_next_turn'] else ''}"
                  + f" | {cand}: out {r['cand_out'] or 'nobody'}, {'won' if r['cand_won'] else 'lost'}{', dead before its next turn' if r['cand_dead_before_next_turn'] else ''}")
        o = {'both': 0, 'cand_only': 0, 'base_only': 0, 'neither': 0}
        for r in withk:
            o['both' if r['base_won'] and r['cand_won'] else 'cand_only' if r['cand_won'] else 'base_only' if r['base_won'] else 'neither'] += 1
        print(f"  the tables with a commander's kill at the first difference: both won {o['both']}, only {cand} {o['cand_only']}, only {base} {o['base_only']}, neither {o['neither']}")
        out['decks'][deck]['first_difference_with_a_commander_kill'] = o
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
