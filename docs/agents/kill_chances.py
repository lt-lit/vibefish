#!/usr/bin/env python3
"""kill_chances.py RUN_DIR... [--deck ID]: a seat's sure kills counted once an opponent, not once a turn. A session helper.

`runner/mistakes.py` counts turns, and a kill that is passed up is usually there again on the next turn, so its count of misses
repeats. Here every opponent a seat was at some point sure to kill (the `combat` line's `through >= life`, harness 0.4.0 or later)
is one chance: it went out on the first turn the kill was sure, on a later such turn of that seat's, or on no such turn; and for
the last group, what became of the opponent that was let live (it won the game, went out anyway, was alive at the end). A seat
that can kill two opponents on one turn and kills one has the other counted as not taken on its first turn.
"""
import argparse, collections, glob, gzip, json, os, sys


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--deck', help="count this deck's seats only")
    a = ap.parse_args(argv)
    C = collections.Counter()
    for root in a.run_dirs:
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            run = json.load(open(rj))
            ids = {d['seat']: d['id'] for d in run['decks']}
            for g in run['games']:
                if not g.get('events'):
                    continue
                evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
                if not os.path.exists(evf):
                    evf += '.gz'
                    if not os.path.exists(evf):
                        continue
                op = gzip.open if evf.endswith('.gz') else open
                with op(evf, 'rt', encoding='utf-8') as f:
                    evs = [json.loads(l) for l in f if l.strip()]
                winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
                lost_at = {e['seat']: e['t'] for e in evs if e['e'] == 'lost'}
                C['games'] += 1
                for s in ids:
                    if a.deck and ids[s] != a.deck:
                        continue
                    C['seat_games'] += 1
                    first, took, turns = {}, {}, collections.Counter()
                    for e in evs:
                        if e['e'] != 'combat' or e.get('seat') != s:
                            continue
                        for d in e.get('defenders') or []:
                            if d['life'] > 0 and d['through'] >= d['life']:
                                o = d['seat']
                                turns[o] += 1
                                first.setdefault(o, e['t'])
                                if lost_at.get(o) == e['t'] and o not in took:
                                    took[o] = 'first' if first[o] == e['t'] else 'later'
                    for o in first:
                        C['chances'] += 1
                        C['turns'] += turns[o]
                        if o in took:
                            C['taken_' + took[o]] += 1
                        else:
                            C['never'] += 1
                            C['spared_won' if winner == o else 'spared_out_anyway' if o in lost_at else 'spared_alive_at_end'] += 1
                            C['never_and_the_seat_won'] += winner == s
    n = C['chances'] or 1
    print(f"{C['games']} games, {C['seat_games']} seat-games: {C['chances']} opponents a seat was sure to kill at some point (on {C['turns']} turns)")
    print(f"  went out on the first such turn {C['taken_first']} ({100 * C['taken_first'] / n:.0f}%), on a later one {C['taken_later']} ({100 * C['taken_later'] / n:.0f}%), "
          f"on none {C['never']} ({100 * C['never'] / n:.0f}%)")
    print(f"  the {C['never']} let live: won the game {C['spared_won']}, went out anyway {C['spared_out_anyway']}, alive at the end {C['spared_alive_at_end']}; "
          f"the seat that let them live won {C['never_and_the_seat_won']}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
