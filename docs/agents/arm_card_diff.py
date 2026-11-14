#!/usr/bin/env python3
"""What a playbook does to each card of its deck, against stock AI on the same tables. A session helper.

    python3 -I docs/agents/arm_card_diff.py STOCK.json PLAYBOOK.json [--min-drawn 20] [--points 15]

The two files are `runner/playtest.py --json` reports of the two arms of one ab.py run. Lists the nonland cards
drawn in at least --min-drawn games under both pilots whose share of games cast (of the games drawn) differs by
--points or more: first the cards the playbook casts LESS than stock AI does, which is where a set of engine rules
starves the rest of the deck (goldfish cannot show it: removal has no target there), then the cards it casts more.
"""
import argparse, json, sys

def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stock'); ap.add_argument('playbook')
    ap.add_argument('--min-drawn', type=int, default=20); ap.add_argument('--points', type=float, default=15)
    a = ap.parse_args(argv)
    s, p = json.load(open(a.stock)), json.load(open(a.playbook))
    print(f"{p['deck']}: stock {s['result']['wins']} of {s['result']['games']}, playbook {p['result']['wins']} of {p['result']['games']}")
    rows = []
    for c, x in p['cards'].items():
        y = s['cards'].get(c)
        if not y or x['drawn'] < a.min_drawn or y['drawn'] < a.min_drawn:
            continue
        d = 100 * ((x['played_share'] or 0) - (y['played_share'] or 0))
        if abs(d) >= a.points:
            rows.append((d, c, x, y))
    for title, pick in (("cast LESS under the playbook", lambda d: d < 0), ("cast more under the playbook", lambda d: d > 0)):
        print(f"\n{title} (card, MV: stock cast/drawn -> playbook cast/drawn; in hand at a loss stock -> playbook)")
        for d, c, x, y in sorted((r for r in rows if pick(r[0])), key=lambda r: r[0] if r[0] < 0 else -r[0]):
            print(f"  {d:+4.0f}  {c}, {x['mv']}: {y['played']}/{y['drawn']} -> {x['played']}/{x['drawn']}; {y['held_at_loss']} -> {x['held_at_loss']}")
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
