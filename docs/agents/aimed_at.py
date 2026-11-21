#!/usr/bin/env python3
"""aimed_at.py RUN_DIR... [--arm ARM] [--deck ID | --focus] [--json OUT]: whose permanents a seat's spells and abilities are aimed at. A session helper.

From the `cast` lines of harness 0.4.0 or later, which name the seat that controls each target (`target_ctrl`): every cast with a
target an opponent controls, split into spells, triggered abilities and activated abilities, and for each the share that goes at
the opponent that looks most dangerous at the start of that turn (life + 2 x nonland permanents, DESIGN.md §33), at the opponent
with the most nonland permanents, at the one with the lowest life, and at the player who goes on to win, each beside what aiming
at a random opponent alive would give. Casts with two or three opponents alive only (with one there is nothing to choose).
A cast with targets of several opponents counts once for each of them. --focus counts, in each run directory, only the seat
under test of that run (the deck its ab.json names), so the arms of an exam of several decks can be read together.
"""
import argparse, collections, glob, gzip, json, os, sys


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--deck', help="count this deck's seats only")
    ap.add_argument('--focus', action='store_true', help="in each run directory, count only the deck its ab.json names")
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    C = collections.defaultdict(collections.Counter)
    games = 0
    for root in a.run_dirs:
        only = a.deck
        if a.focus:
            only = json.load(open(os.path.join(root, 'ab.json')))['deck']
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            if a.arm and f'{os.sep}arm-{a.arm}{os.sep}' not in rj:
                continue
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
                winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
                games += 1
                state = {}
                op = gzip.open if evf.endswith('.gz') else open
                with op(evf, 'rt', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        e = json.loads(line)
                        if e['e'] == 'turn':
                            state = {s['seat']: s for s in e.get('state') or []}
                        elif e['e'] == 'cast' and e.get('target_ctrl') and e.get('seat') is not None:
                            s = e['seat']
                            if only and ids.get(s) != only:
                                continue
                            opps = [x for x in state.values() if x['seat'] != s and x.get('alive')]
                            if len(opps) < 2:
                                continue
                            hit = {c for c in e['target_ctrl'] if c is not None and c != s and any(o['seat'] == c for o in opps)}
                            if not hit:
                                continue
                            ab = e.get('ability') or ''
                            kind = 'spell' if e.get('spell') else ('trigger' if ab.lstrip().startswith(('When', 'At ', 'Landfall', 'Magecraft')) or ' — When' in ab[:60] else 'ability')
                            dg = {o['seat']: o['life'] + 2 * (o['bf'] - o['lands']) for o in opps}
                            wide = {o['seat']: o['bf'] - o['lands'] for o in opps}
                            life = {o['seat']: o['life'] for o in opps}
                            top, widest, lowest = max(dg.values()), max(wide.values()), min(life.values())
                            for c in hit:
                                k = C[kind]
                                k['n'] += 1
                                k['chance'] += 1 / len(opps)
                                k['danger'] += dg[c] == top
                                k['widest'] += wide[c] == widest
                                k['lowest_life'] += life[c] == lowest
                                if winner is not None and winner != s:
                                    k['n_lost'] += 1
                                    k['winner'] += c == winner
                                    k['winner_chance'] += 1 / len(opps)
    print(f"{games} games; casts with a target an opponent controls, two or three opponents alive")
    print(f"  {'':10} {'casts':>7} {'most dangerous':>15} {'widest board':>13} {'lowest life':>12} {'chance':>7}   {'the eventual winner (games the caster did not win)':>52} {'chance':>7}")
    tot = collections.Counter()
    for kind in ('spell', 'trigger', 'ability'):
        tot.update(C[kind])
    for name, k in [(x, C[x]) for x in ('spell', 'trigger', 'ability')] + [('all', tot)]:
        if not k['n']:
            continue
        pc = lambda x, n: f"{100 * x / n:.0f}%" if n else '-'
        print(f"  {name:10} {k['n']:>7} {pc(k['danger'], k['n']):>15} {pc(k['widest'], k['n']):>13} {pc(k['lowest_life'], k['n']):>12} {pc(k['chance'], k['n']):>7}   {pc(k['winner'], k['n_lost']):>52} {pc(k['winner_chance'], k['n_lost']):>7}")
    if a.json:
        json.dump({'kind': 'aimed-at', 'games': games, 'counts': {k: dict(v) for k, v in C.items()}}, open(a.json, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
