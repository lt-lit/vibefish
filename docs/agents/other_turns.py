#!/usr/bin/env python3
"""other_turns.py RUN_DIR... [--arm ARM] [--deck ID] [--focus] [--cards N]: what a seat does on other players' turns. A session helper.

From the event logs: a seat's spells by card type (instants, cards with flash, the rest), split by whether it was the seat's own
turn; its activated abilities the same way. Card types come from the deck lists in run.json; flash is not in them, so a spell
that is not an instant and is cast on another player's turn is listed as "other, at instant speed". --focus keeps the seat under
test of an ab.py run (the deck named in ab.json); --deck keeps one deck's seats; --arm one arm. Seats are grouped by pilot
(`bot` has a playbook, `stock` has none). --cards N lists the N instants cast most, each by when: on the seat's own turn before
its attack was declared, after it, or on another player's turn (a `play` rule casts a named instant in the main phase, so the
removal a playbook names shows up in the first column; DESIGN.md section 34).
"""
import argparse, collections, glob, gzip, json, os, sys


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--deck')
    ap.add_argument('--focus', action='store_true')
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--cards', type=int, default=0)
    a = ap.parse_args(argv)
    C = collections.defaultdict(collections.Counter)
    names = collections.defaultdict(collections.Counter)
    cards = collections.defaultdict(collections.Counter)
    for root in a.run_dirs:
        focus_deck = None
        abj = os.path.join(root, 'ab.json')
        if a.focus and os.path.exists(abj):
            focus_deck = json.load(open(abj)).get('deck')
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            if a.arm and f'{os.sep}arm-{a.arm}{os.sep}' not in rj:
                continue
            run = json.load(open(rj))
            ids = {d['seat']: d['id'] for d in run['decks']}
            pilot = {d['seat']: ('bot' if d.get('playbook') else 'stock') for d in run['decks']}
            types = {d['seat']: {c['name']: c.get('type', '') for c in (d.get('cards') or []) + (d.get('commander_cards') or [])} for d in run['decks']}
            for g in run['games']:
                if not g.get('events'):
                    continue
                evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
                if not os.path.exists(evf):
                    evf += '.gz'
                    if not os.path.exists(evf):
                        continue
                op = gzip.open if evf.endswith('.gz') else open
                keep = [s for s in ids if (not a.deck or ids[s] == a.deck) and (not focus_deck or ids[s] == focus_deck)]
                for s in keep:
                    C[pilot[s]]['seat_games'] += 1
                active = None
                attacked = set()
                with op(evf, 'rt', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        e = json.loads(line)
                        if e['e'] == 'turn':
                            active = e['seat']
                            attacked = set()
                        elif e['e'] == 'attack':
                            attacked.add(e.get('seat'))
                        elif e['e'] == 'cast' and e.get('seat') in keep and not e.get('copy'):
                            s = e['seat']
                            when = 'own' if s == active else 'other'
                            if e.get('spell'):
                                t = types[s].get(e['card'], '')
                                kind = 'instant' if 'Instant' in t else 'other'
                                C[pilot[s]][f'{kind}_{when}'] += 1
                                if kind == 'instant':
                                    cards[(pilot[s], ids[s], e['card'])]['other' if when == 'other' else 'after' if s in attacked else 'before'] += 1
                                if when == 'other':
                                    names[pilot[s]][e['card']] += 1
                            elif e.get('ability') and not e['ability'].lstrip().startswith(('When', 'At ', 'Landfall', 'Magecraft', 'Whenever')) and ' — When' not in e['ability'][:40]:
                                C[pilot[s]][f'ability_{when}'] += 1
    for p in sorted(C):
        c = C[p]
        n = c['seat_games'] or 1
        ins = c['instant_own'] + c['instant_other']
        print(f"{p}: {c['seat_games']} seat-games")
        print(f"  instants cast: {ins} ({ins / n:.2f} a seat-game), on another player's turn {c['instant_other']} ({100 * c['instant_other'] / ins if ins else 0:.0f}%, {c['instant_other'] / n:.2f} a seat-game)")
        print(f"  other spells: own turn {c['other_own']} ({c['other_own'] / n:.2f}), at instant speed on another player's turn {c['other_other']} ({c['other_other'] / n:.2f})")
        print(f"  activated abilities: own turn {c['ability_own']} ({c['ability_own'] / n:.2f}), another player's turn {c['ability_other']} ({c['ability_other'] / n:.2f})")
        print(f"  spells on another player's turn, the most frequent: " + ', '.join(f'{k} {v}' for k, v in names[p].most_common(a.top)))
        if a.cards:
            mine = sorted(((sum(c2.values()), k, c2) for k, c2 in cards.items() if k[0] == p), key=lambda r: (-r[0], r[1]))
            tot = collections.Counter()
            for _, _, c2 in mine:
                tot.update(c2)
            print(f"  instants by when: own turn before the seat's attack {tot['before']}, own turn after it {tot['after']}, another player's turn {tot['other']}")
            print(f"  {'':4}  {'deck':18} {'card':34} {'before':>7} {'after':>6} {'other':>6}")
            for n2, k, c2 in mine[:a.cards]:
                print(f"  {n2:4}  {k[1]:18} {k[2]:34} {c2['before']:7} {c2['after']:6} {c2['other']:6}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
