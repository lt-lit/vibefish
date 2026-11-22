#!/usr/bin/env python3
"""react_exam.py EXAM_RESULTS_DIR VARIANT DECK... [--base NAME] [--json OUT.json]: what a candidate with rules for other players'
turns did with the cards those rules name, beside the base arm on the same tables. A session helper (harness 0.4.12).

EXAM_RESULTS_DIR holds the run directories docs/agents/shards.sh makes (ab-DECK for the shipped playbook, ab-DECK@VARIANT for the
candidate; --base NAME reads ab-DECK@NAME as the base). The cards are read from the candidate's own `reserve` and `hold` rules
(playbook/variants/DECK-VARIANT.json). For the seat under test, in each arm:
  - per card: the games it was in hand, the games it was cast, and its casts by when: the seat's own turn, or another player's
    turn (there: at a creature that was attacking the seat, between that player's attack and the seat's blocks; or anything else,
    which for the candidate is the end step before its own turn);
  - the casts at an attacker, one by one: the turn, the card, the attacker, the seat's block line that turn (its life, the damage
    coming through the blocks made, the least its best blocks could have let through) and whether the seat was out of the game
    that turn;
  - the seat's deaths in combat, and the candidate's own counters (react_*, reserve_*, cast_react*).
Read-only.
"""
import argparse, collections, glob, gzip, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def events(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                pass


def read_arm(run_dir, deck, cards):
    out = {'games': 0, 'wins': 0, 'cards': {c: collections.Counter() for c in cards}, 'at_attacker': [], 'combat_deaths': 0,
           'counters': collections.Counter(), 'casts': collections.Counter()}
    for rj in sorted(glob.glob(os.path.join(run_dir, 'arm-*', '*', 'run.json'))):
        run = json.load(open(rj))
        seat = next((d['seat'] for d in run['decks'] if d['id'] == deck), None)
        g = run['games'][0]
        evf = glob.glob(os.path.join(os.path.dirname(rj), 'games', '*.events.jsonl*'))
        if seat is None or not evf:
            continue
        out['games'] += 1
        out['wins'] += g.get('winner') == seat
        for k, v in ((g.get('playbook_stats_by_seat') or {}).get(deck) or {}).items():
            if k.startswith(('react_', 'reserve_', 'cast_react')) or k in ('cast_aim_attacker', 'cast_hold_vetoes', 'cast_hold_stuck', 'cast_errors', 'cast_failed'):
                out['counters'][k] += v
        evs = list(events(evf[0]))
        lost_at = {e['seat']: e['t'] for e in evs if e['e'] == 'lost'}
        held, cast_in = set(), set()
        cur = None; attackers_at_me = []; blocked = False; pending = []
        for e in evs:
            k = e['e']
            if k == 'turn':
                cur = e; attackers_at_me = []; blocked = False
                me = next((s for s in e.get('state') or [] if s['seat'] == seat), None)
                if me:
                    held |= set(me.get('hand') or []) & set(cards)
            elif cur is None:
                continue
            elif k == 'zone' and e.get('seat') == seat and e.get('card') in cards and e.get('to') == 'Hand':
                held.add(e['card'])
            elif k == 'attack' and e.get('seat') == cur.get('seat') and cur.get('seat') != seat:
                attackers_at_me = [a.get('attacker') for a in e.get('attacks') or [] if a.get('defender_seat') == seat and not a.get('planeswalker')]
            elif k == 'block' and e.get('seat') == seat:
                blocked = True
                for row in pending:
                    if row['t'] == e['t']:
                        row.update(life=e.get('life'), incoming=e.get('incoming'), best=e.get('best'), out=lost_at.get(seat) == e['t'])
                    else:                                # no block line that turn: nothing was left attacking the seat
                        row.update(life=None, incoming=0, best=0, out=lost_at.get(seat) == row['t'])
                pending = []
                if e.get('life', 0) > 0 and (e.get('incoming', 0) >= e.get('life', 0) or e.get('cmd')) and lost_at.get(seat) == e['t']:
                    out['combat_deaths'] += 1
            elif k == 'cast' and e.get('seat') == seat and e.get('spell') and e.get('card') in cards:
                c = e['card']; cast_in.add(c); held.add(c)
                tg = (e.get('targets') or [None])[0]
                if cur.get('seat') == seat:
                    when = 'own turn'
                elif attackers_at_me and not blocked and tg in attackers_at_me:
                    when = 'at an attacker'
                    row = {'where': os.path.relpath(evf[0], run_dir), 't': e['t'], 'card': c, 'attacker': tg, 'attackers': len(attackers_at_me)}
                    out['at_attacker'].append(row); pending.append(row)
                else:
                    when = "another player's turn"
                out['cards'][c][when] += 1
                out['casts'][when] += 1
        for c in held:
            out['cards'][c]['games_held'] += 1
        for c in cast_in:
            out['cards'][c]['games_cast'] += 1
        for row in pending:                              # no block line followed: nothing was left attacking the seat
            row.update(life=None, incoming=0, best=0, out=lost_at.get(seat) == row['t'])
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('results'); ap.add_argument('variant'); ap.add_argument('decks', nargs='+')
    ap.add_argument('--base'); ap.add_argument('--json')
    a = ap.parse_args(argv)
    doc = {'kind': 'react-exam', 'variant': a.variant, 'base': a.base or 'shipped', 'decks': {}}
    tot = {arm: collections.Counter() for arm in ('base', 'cand')}
    for deck in a.decks:
        pb = json.load(open(os.path.join(ROOT, 'playbook', 'variants', f'{deck}-{a.variant}.json'), encoding='utf-8'))['playbook']
        cards = []
        for r in pb['cast']['rules']:
            for c in r.get('reserve', []) + (r.get('play', []) if r.get('phase') in ('defend', 'end') else []):
                if c not in cards:
                    cards.append(c)
        arms = {'base': read_arm(os.path.join(a.results, f'ab-{deck}' + (f'@{a.base}' if a.base else '')), deck, cards),
                'cand': read_arm(os.path.join(a.results, f'ab-{deck}@{a.variant}'), deck, cards)}
        doc['decks'][deck] = {'cards': cards, **{arm: {'games': x['games'], 'wins': x['wins'], 'combat_deaths': x['combat_deaths'], 'casts': dict(x['casts']),
                                                       'cards': {c: dict(v) for c, v in x['cards'].items()}, 'at_attacker': x['at_attacker'],
                                                       'counters': dict(x['counters'])} for arm, x in arms.items()}}
        print(f"{deck}: {', '.join(cards)}")
        for arm, x in arms.items():
            held = sum(v['games_held'] for v in x['cards'].values()); cast = sum(v['games_cast'] for v in x['cards'].values())
            n = sum(x['casts'].values()); other = n - x['casts']['own turn']
            print(f"   {arm:5} {x['games']} games, {x['wins']} wins | card-games held {held}, cast {cast} ({100 * cast / max(1, held):.0f}%) | casts {n}: own turn {x['casts']['own turn']}, "
                  f"another player's turn {other} ({100 * other / max(1, n):.0f}%), of them at an attacker {x['casts']['at an attacker']} | deaths in combat {x['combat_deaths']}")
            for key in ('games', 'wins', 'combat_deaths'):
                tot[arm][key] += x[key]
            tot[arm]['held'] += held; tot[arm]['cast'] += cast; tot[arm]['casts'] += n; tot[arm]['other'] += other; tot[arm]['at_attacker'] += x['casts']['at an attacker']
            tot[arm]['out_after_answer'] += sum(1 for r in x['at_attacker'] if r.get('out'))
            for k, v in x['counters'].items():
                tot[arm]['c:' + k] += v
        for r in arms['cand']['at_attacker']:
            print(f"      t{r['t']} {r['card']} at the attacking {r['attacker']} ({r['attackers']} attackers): life {r.get('life')}, through the blocks made {r.get('incoming')}, "
                  f"through the best blocks {r.get('best')}{'; OUT that turn' if r.get('out') else ''}  [{r['where']}]")
    print('ALL')
    for arm in ('base', 'cand'):
        t = tot[arm]
        print(f"   {arm:5} {t['games']} games, {t['wins']} wins | card-games held {t['held']}, cast {t['cast']} ({100 * t['cast'] / max(1, t['held']):.1f}%) | casts {t['casts']}: "
              f"another player's turn {t['other']} ({100 * t['other'] / max(1, t['casts']):.1f}%), at an attacker {t['at_attacker']} (the seat out that turn after {t['out_after_answer']}) | "
              f"deaths in combat {t['combat_deaths']}")
        print('         counters', {k[2:]: v for k, v in sorted(t.items()) if k.startswith('c:')})
    doc['all'] = {arm: dict(t) for arm, t in tot.items()}
    if a.json:
        json.dump(doc, open(a.json, 'w', encoding='utf-8'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
