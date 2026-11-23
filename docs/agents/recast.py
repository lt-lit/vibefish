#!/usr/bin/env python3
"""recast.py RUN_DIR... [--deck ID] [--arm ARM] [--show N] [--json OUT]: a commander cast again from the command zone at a
tax, and what stayed in the seat's hand that turn. A session helper; read-only.

Written for DESIGN.md section 47: every deck recasts its commander at whatever tax, ahead of larger plays it holds. A
judgement for each deck and not a mistake the logs can call, so this counts and does not judge.

RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory (arm-*/gNNNN); several are read as one. Per deck (or
the one named), for its seat:
  - the commander's casts from the command zone, the recasts among them (the second cast and later) and their mean tax;
  - the recasts on a turn on which a card of mana value five or more stayed in the seat's hand that it had the lands
    for: in its hand at the start of the turn, not a land, not cast that turn, its mana value no more than the lands the
    seat had (with the turn's land drop). Colours and the mana the recast itself took are not looked at: it is the count
    of DESIGN section 47, a ceiling;
  - the seat's own turns after its commander's first cast, and those of them that began with a commander in its command
    zone (the `cmd` list of the `turn` line): what a later recast costs in turns with the commander;
  - the cards of mana value five or more other than the commander: card-games held (in hand at the start of some own
    turn) and cast.
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
    ap.add_argument('--deck')
    ap.add_argument('--arm')
    ap.add_argument('--show', type=int, default=0, help='print this many recasts over a larger card')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    D = collections.defaultdict(collections.Counter)
    ex = []
    for rj, run, g, evs in games(a.run_dirs, a.arm):
        ids = {d['seat']: d['id'] for d in run['decks']}
        seats = [s for s, i in ids.items() if a.deck is None or i == a.deck]
        if not seats:
            continue
        cmc = {d['seat']: {c['name']: c.get('cmc') or 0 for c in d.get('cards') or []} for d in run['decks']}
        island = {d['seat']: {c['name'] for c in d.get('cards') or [] if c.get('land')} for d in run['decks']}
        cmds = {d['seat']: set(d.get('commanders') or []) for d in run['decks']}
        won = {p['seat'] for p in g['players'] if p.get('won')}
        for s in seats:
            D[ids[s]]['seat_games'] += 1
            D[ids[s]]['wins'] += s in won
        ncast = collections.Counter()
        held, cast_big = collections.defaultdict(set), collections.defaultdict(set)
        turns = [(i, e) for i, e in enumerate(evs) if e['e'] == 'turn']
        for n, (i, e) in enumerate(turns):
            s = e['seat']
            if s not in seats:
                continue
            st = next((p for p in e.get('state') or [] if p['seat'] == s), None)
            if st is None:
                continue
            d = D[ids[s]]
            if ncast[s] >= 1:
                d['own_turns_after_first_cast'] += 1
                d['own_turns_commander_in_zone'] += bool(st.get('cmd'))
            end = turns[n + 1][0] if n + 1 < len(turns) else len(evs)
            own = [x for x in evs[i + 1:end] if x.get('seat') == s]
            casts = [x for x in own if x['e'] == 'cast' and x.get('spell')]
            names = [x.get('card') for x in casts]
            hand = st.get('hand') or []
            for c in hand:
                if c not in island[s] and c not in cmds[s] and cmc[s].get(c, 0) >= 5:
                    held[s].add(c)
            for c in names:
                if c not in cmds[s] and cmc[s].get(c, 0) >= 5:
                    cast_big[s].add(c)
            for x in casts:
                if not (x.get('commander') and x.get('from') == 'Command'):
                    continue
                ncast[s] += 1
                d['commander_casts'] += 1
                if ncast[s] < 2:
                    continue
                tax = 2 * (ncast[s] - 1)
                d['recasts'] += 1
                d['recast_tax_sum'] += tax
                avail = (st.get('lands') or 0) + (1 if any(y['e'] == 'land' for y in own) else 0)
                big = [c for c in hand if c not in island[s] and c not in names and 5 <= cmc[s].get(c, 0) <= avail]
                if big:
                    d['recasts_over_a_larger_card'] += 1
                    ex.append({'game': os.path.relpath(os.path.dirname(rj), os.path.dirname(os.path.dirname(os.path.dirname(rj)))), 't': e['t'],
                               'deck': ids[s], 'commander': x.get('card'), 'tax': tax, 'lands': avail, 'kept': [[c, cmc[s].get(c)] for c in big]})
        for s in seats:
            D[ids[s]]['big_card_games_held'] += len(held[s] | cast_big[s])
            D[ids[s]]['big_card_games_cast'] += len(cast_big[s])
    print(f"{'deck':20} {'games':>6} {'wins':>5} {'cmdr casts':>10} {'recasts':>8} {'a game':>7} {'mean tax':>9} {'over a larger card':>19} {'share':>6} "
          f"{'turns cmdr in zone':>19} {'share':>6} {'5+ cards cast of held':>22}")
    out = {}
    for k, v in sorted(D.items()):
        r, t = max(1, v['recasts']), max(1, v['own_turns_after_first_cast'])
        print(f"{k:20} {v['seat_games']:6} {v['wins']:5} {v['commander_casts']:10} {v['recasts']:8} {v['recasts'] / max(1, v['seat_games']):7.2f} "
              f"{v['recast_tax_sum'] / r:9.1f} {v['recasts_over_a_larger_card']:19} {100 * v['recasts_over_a_larger_card'] / r:5.0f}% "
              f"{v['own_turns_commander_in_zone']:8} of {v['own_turns_after_first_cast']:6} {100 * v['own_turns_commander_in_zone'] / t:5.1f}% "
              f"{v['big_card_games_cast']:9} of {v['big_card_games_held']:5} ({100 * v['big_card_games_cast'] / max(1, v['big_card_games_held']):.1f}%)")
        out[k] = dict(v)
    for x in ex[:a.show]:
        print(f"    {x['game']:22} turn {x['t']:3} {x['deck']}: {x['commander']} at a tax of {x['tax']} with {x['lands']} lands, kept {x['kept']}")
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'recast', 'decks': out, 'recasts_over_a_larger_card': ex}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
