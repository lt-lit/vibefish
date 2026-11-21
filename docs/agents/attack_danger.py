#!/usr/bin/env python3
"""attack_danger.py RUN_DIR... [--arm ARM] [--deck ID] [--json OUT]: whom a seat's attackers go at, by the judgement of danger.
A session helper.

From the `combat` and `attack` lines of games played on harness 0.4.0 or later: every attack declared with two or three
opponents alive (with one there is nothing to choose), and the share of its attackers that go at the opponent that looks most
dangerous as the declare-attackers step begins (its life + 2 x its nonland permanents, DESIGN.md section 33), beside what
attacking a random opponent would give, and at the player who goes on to win. Attackers of planeswalkers count for the
planeswalker's controller. Declarations with a tie for the most dangerous opponent are left out.

For the declarations that sent nothing at the most dangerous opponent it says what stood where, from the combat line (the
seat's creatures that may attack each opponent at no cost, the opponent's creatures that may block, the damage sure to get
through whatever is blocked): whether the opponent attacked instead had the lower life, which of the two had more creatures
that could block, and whether the damage sure to get through was at least as much at the most dangerous one. That is the count
behind a playbook's `"aim": "danger"` on its attack (harness 0.4.5), and with --deck on the two arms of an exam it is the
measure of what that hook changed.
"""
import argparse, collections, glob, gzip, json, os, sys


def pct(a, b):
    return f'{100.0 * a / b:.1f}%' if b else 'n/a'


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--deck', help="count this deck's seats only")
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    C = collections.Counter()
    R = collections.defaultdict(collections.Counter)
    games = 0
    for root in a.run_dirs:
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
                state, combat = {}, None
                op = gzip.open if evf.endswith('.gz') else open
                with op(evf, 'rt', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        e = json.loads(line)
                        k = e['e']
                        if k == 'turn':
                            state = {s['seat']: s for s in e.get('state') or []}
                        elif k == 'combat':
                            combat = e
                        elif k == 'attack' and combat is not None and combat.get('seat') == e.get('seat') and combat.get('t') == e.get('t'):
                            s = e['seat']
                            if a.deck and ids.get(s) != a.deck:
                                continue
                            defs = combat.get('defenders') or []
                            if len(defs) < 2:
                                continue
                            dng = {}
                            for d in defs:
                                n = d.get('permanents')
                                if n is None:
                                    st = state.get(d['seat']) or {}
                                    n = st.get('bf', 0) - st.get('lands', 0)
                                dng[d['seat']] = d['life'] + 2 * n
                            order = sorted(dng.values(), reverse=True)
                            if order[0] == order[1]:
                                C['ties'] += 1
                                continue
                            top = max(dng, key=dng.get)
                            by = collections.Counter(x['defender_seat'] for x in e.get('attacks') or [] if x.get('defender_seat') in dng)
                            n = sum(by.values())
                            if not n:
                                continue
                            key = f'{len(defs)}'
                            C[key + ' declarations'] += 1
                            C[key + ' attackers'] += n
                            C[key + ' at_top'] += by.get(top, 0)
                            C[key + ' all_at_top'] += by.get(top, 0) == n
                            C[key + ' none_at_top'] += by.get(top, 0) == 0
                            if winner is not None and winner != s and winner in dng:
                                C[key + ' attackers_seat_lost'] += n
                                C[key + ' at_winner'] += by.get(winner, 0)
                            rnd = (e['t'] - 1) // 4 + 1
                            b = '1-4' if rnd <= 4 else '5-8' if rnd <= 8 else '9-12' if rnd <= 12 else '13+'
                            R[b]['attackers'] += n
                            R[b]['at_top'] += by.get(top, 0)
                            R[b]['chance'] += n / len(defs)
                            if by.get(top, 0) == 0:
                                main_seat = by.most_common(1)[0][0]
                                dt = next(d for d in defs if d['seat'] == top)
                                dm = next(d for d in defs if d['seat'] == main_seat)
                                gap = dng[top] - dng[main_seat]
                                C['else declarations'] += 1
                                C['else attackers'] += n
                                C['else gap ' + ('1-4' if gap < 5 else '5-9' if gap < 10 else '10-19' if gap < 20 else '20+')] += 1
                                C['else attacked_lower_life'] += dm['life'] < dt['life']
                                C['else attacked_lowest_life'] += dm['life'] == min(d['life'] for d in defs)
                                C['else top_no_blocker'] += dt['blockers'] == 0
                                C['else top_fewer_blockers'] += dt['blockers'] < dm['blockers']
                                C['else top_as_many_blockers'] += dt['blockers'] == dm['blockers']
                                C['else top_more_blockers'] += dt['blockers'] > dm['blockers']
                                C['else sure_at_top_at_least'] += dt['through'] >= dm['through']
                                C['else sure_at_top_at_least gap5'] += dt['through'] >= dm['through'] and gap >= 5
    who = f"{a.deck}'s seats" if a.deck else 'every seat'
    print(f'{games} games' + (f', arm {a.arm}' if a.arm else '') + f', {who}; {C["ties"]} declarations with a tie for the most dangerous opponent left out')
    for key in ('3', '2'):
        n, d = C[key + ' attackers'], C[key + ' declarations']
        print(f'{key} opponents alive: {d} declarations, {n} attackers')
        print(f'  attackers at the most dangerous opponent   {C[key + " at_top"]:6} {pct(C[key + " at_top"], n):>6}   (a random opponent {100.0 / int(key):.1f}%)')
        print(f'  declarations: all there {pct(C[key + " all_at_top"], d)}, none there {pct(C[key + " none_at_top"], d)}')
        m = C[key + ' attackers_seat_lost']
        print(f'  attackers at the player who went on to win {C[key + " at_winner"]:6} {pct(C[key + " at_winner"], m):>6}   of {m} in games the seat did not win')
    print('by round (attackers; at the most dangerous; a random opponent):')
    for b in ('1-4', '5-8', '9-12', '13+'):
        r = R[b]
        print(f'  rounds {b:5} {r["attackers"]:6}  {pct(r["at_top"], r["attackers"]):>6}  {pct(r["chance"], r["attackers"]):>6}')
    t = C['else declarations']
    print(f'declarations with nothing at the most dangerous opponent: {t} ({C["else attackers"]} attackers)')
    for k, label in (('attacked_lower_life', 'the one attacked had the lower life'), ('attacked_lowest_life', 'the one attacked had the lowest life at the table'),
                     ('top_no_blocker', 'the most dangerous had no creature that could block'), ('top_fewer_blockers', 'the most dangerous had fewer creatures that could block'),
                     ('top_as_many_blockers', 'as many'), ('top_more_blockers', 'more'),
                     ('sure_at_top_at_least', 'the damage sure to get through was at least as much at the most dangerous'),
                     ('sure_at_top_at_least gap5', 'the same, and the most dangerous was ahead by 5 or more'),
                     ('gap 1-4', 'ahead of the one attacked by 1 to 4'), ('gap 5-9', 'by 5 to 9'), ('gap 10-19', 'by 10 to 19'), ('gap 20+', 'by 20 or more')):
        print(f'  {label:76} {C["else " + k]:6} {pct(C["else " + k], t):>6}')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'attack-danger', 'games': games, 'arm': a.arm, 'deck': a.deck, 'counts': dict(C),
                       'by_round': {b: dict(r) for b, r in R.items()}}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
