#!/usr/bin/env python3
"""life_spell.py RUN_DIR... --card NAME [--deck ID] [--arm ARM] [--show] [--json OUT]: what a spell that is paid for in life cost its caster.

A session helper; read-only. Written for Eventide's Shadow ("Remove any number of counters from among permanents on the
battlefield. You draw that many cards and lose that much life", DESIGN.md section 44), and good for any spell whose
price is taken while it resolves: Forge's AI answers "any number" with every counter on the table, and the caster pays
for all of them.

RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory (arm-*/gNNNN); several are read as one. Per cast of
the card (by the deck named, or by anyone): the turn, the caster's life before, the life it lost and the cards it drew
between the `cast` line and the spell's `resolve` line, the life it was left with, and whether it was out of the game
on that same turn. Then the sums: the games the card was held in (in the seat's hand at the start of some turn, or
cast), the games it was cast in, the casts that left the caster at five life or less, and the casts after which it was
out that turn. With harness 0.4.14 logs, the seat's `cast_take` counters as well.
"""
import argparse, collections, glob, gzip, json, os, sys


def games(roots, arm=None):
    for root in roots:
        pats = [os.path.join(root, 'shard-*', '*', 'run.json'), os.path.join(root, 'arm-' + (arm or '*'), '*', 'run.json')]
        for rj in sorted(p for pat in pats for p in glob.glob(pat)):
            run = json.load(open(rj))
            g = run['games'][0]
            evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                evf += '.gz'
                if not os.path.exists(evf):
                    continue
            op = gzip.open if evf.endswith('.gz') else open
            with op(evf, 'rt', encoding='utf-8') as f:
                evs = [json.loads(l) for l in f if l.strip()]
            yield rj, run, g, evs


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--card', required=True)
    ap.add_argument('--deck')
    ap.add_argument('--arm')
    ap.add_argument('--show', action='store_true', help='print every cast')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    rows = []
    T = collections.Counter()
    stats = collections.Counter()
    for rj, run, g, evs in games(a.run_dirs, a.arm):
        ids = {d['seat']: d['id'] for d in run['decks']}
        seats = [s for s, i in ids.items() if a.deck is None or i == a.deck]
        if not seats:
            continue
        T['games'] += 1
        for s in seats:
            st = (g.get('playbook_stats_by_seat') or {}).get(ids[s]) or {}
            for k, v in st.items():
                if k.startswith('cast_take'):
                    stats[k] += v
        life = {}
        lost = {x['seat']: x['t'] for x in evs if x['e'] == 'lost'}
        held, cast = set(), set()
        for i, e in enumerate(evs):
            k = e['e']
            if k == 'turn':
                for p in e.get('state') or []:
                    life[p['seat']] = p.get('life')
                    if p['seat'] in seats and a.card in (p.get('hand') or []):
                        held.add(p['seat'])
            elif k == 'life':
                life[e['seat']] = e.get('to')
            elif k == 'cast' and e.get('card') == a.card and e.get('spell') and e.get('seat') in seats:
                s = e['seat']
                cast.add(s)
                before = life.get(s)
                paid = drawn = 0
                resolved = fizzled = False
                for x in evs[i + 1:]:
                    if x['e'] == 'life' and x.get('seat') == s:
                        paid += (x.get('from') or 0) - (x.get('to') or 0)
                    elif x['e'] == 'zone' and x.get('seat') == s and x.get('from') == 'Library' and x.get('to') == 'Hand':
                        drawn += 1
                    elif x['e'] == 'resolve' and x.get('id') == e.get('id'):
                        resolved, fizzled = True, bool(x.get('fizzled'))
                        break
                    elif x['e'] == 'turn':
                        break                                           # triggers and abilities go on the stack in between: only the turn ends the search
                after = None if before is None else before - paid
                rows.append({'game': os.path.relpath(os.path.dirname(rj), os.path.dirname(os.path.dirname(os.path.dirname(rj)))), 'deck': ids[s], 't': e['t'],
                             'life_before': before, 'life_paid': paid, 'drawn': drawn, 'life_after': after, 'resolved': resolved and not fizzled,
                             'out_that_turn': lost.get(s) == e['t'], 'won': any(p.get('won') and p['seat'] == s for p in g['players'])})
        T['games_held'] += len(held | cast)
        T['games_cast'] += len(cast)
    n = len(rows)
    out_turn = sum(r['out_that_turn'] for r in rows)
    low = sum(1 for r in rows if r['life_after'] is not None and r['life_after'] <= 5)
    print(f"{a.card}{' cast by ' + a.deck if a.deck else ''}: {T['games']} games, held in {T['games_held']}, cast in {T['games_cast']} ({n} casts)")
    if n:
        print(f"  a cast: {sum(r['drawn'] for r in rows) / n:.1f} cards drawn and {sum(r['life_paid'] for r in rows) / n:.1f} life paid at the mean; "
              f"the most life paid {max(r['life_paid'] for r in rows)}; left at five life or less {low}; out of the game that turn {out_turn}; "
              f"the caster won the game after {sum(r['won'] for r in rows)}")
    if stats:
        print('  ' + ', '.join(f'{k} {v}' for k, v in sorted(stats.items())))
    if a.show:
        for r in rows:
            print(f"    {r['game']:24} turn {r['t']:3}: life {r['life_before']} -> {r['life_after']}, {r['drawn']} drawn"
                  + (', out that turn' if r['out_that_turn'] else '') + (', won the game' if r['won'] else '') + ('' if r['resolved'] else ', did not resolve'))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'life-spell', 'card': a.card, 'deck': a.deck, 'totals': dict(T), 'counters': dict(stats), 'casts': rows}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
