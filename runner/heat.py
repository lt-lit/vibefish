#!/usr/bin/env python3
"""Who gets the heat: where a table's attackers and aimed spells go, from the JSONL event logs. Read-only; prints text.

  runner/heat.py RUN_DIR [RUN_DIR ...] [--arm stock] [--by-deck] [--json OUT.json]

RUN_DIR is anything that holds run.json files with their games/ beside them: a league run (shard-*/g*/), an ab.py
run or its unzipped shard artifacts (arm-*/g*/), a pod run (shard-*/). --arm keeps the games of one A/B arm.

Every attack declaration and every aimed spell made while the seat had two or more opponents alive is asked the
same question: which opponent got it? An aim is a spell or ability on the stack with a player target that is an
opponent, or a card target that only one opponent's list holds (targets[] carry names, not controllers: tokens and
cards two seats play are left out, so aims are a floor, as in losses.py). Copies of spells are not counted.

For each kind the share that went at
  biggest board   the opponent with the most nonland permanents (bf minus lands in the last turn event)
  highest life    the opponent with the most life;  lowest life: the one with the least
  the winner      the opponent who went on to win the game (hindsight)
  hurt me most    the opponent who has dealt this seat the most damage so far in the game
  hurt the table  the opponent who has dealt the most damage to all players so far
  attacked me     the one opponent who sent attackers at this seat since its last turn (attacks only)
beside the share chance would give (one over the opponents alive, over the same events). A category counts an
event only when it names one opponent without a tie. Seats are grouped by pilot: `bot` has a playbook, `stock` has
none (--by-deck groups by deck instead).
"""
import argparse, collections, glob, gzip, json, os, sys

CATS = ('biggest board', 'highest life', 'lowest life', 'the winner', 'hurt me most', 'hurt the table', 'attacked me')


def events(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def run_files(roots, arm):
    for root in roots:
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            if arm and f'{os.sep}arm-{arm}{os.sep}' not in rj:
                continue
            yield rj


def unique(opp, key, rev):
    vals = sorted(((key(o), o) for o in opp), reverse=rev)
    return vals[0][1] if len(vals) > 1 and vals[0][0] != vals[1][0] else None


def collect(roots, arm=None, by_deck=False):
    G = collections.defaultdict(lambda: collections.defaultdict(float))   # group -> counter
    games = 0
    for rj in run_files(roots, arm):
        run = json.load(open(rj))
        ids = {d['seat']: d['id'] for d in run['decks']}
        pilot = {d['seat']: ('bot' if d.get('playbook') else 'stock') for d in run['decks']}
        label = (lambda s: ids[s]) if by_deck else (lambda s: pilot[s])
        lists = {d['seat']: {c['name'] for c in d['cards']} | set(d.get('commanders') or []) for d in run['decks']}
        cmdrs = {d['seat']: set(d.get('commanders') or []) for d in run['decks']}
        ctype = {c['name']: (c.get('type') or '') for d in run['decks'] for c in d['cards']}
        for g in run['games']:
            if not g.get('events'):
                continue
            evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                evf += '.gz'
                if not os.path.exists(evf):
                    continue
            games += 1
            winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
            state = None
            hurt = collections.defaultdict(collections.Counter)      # hurt[me][src] = damage so far
            dealt = collections.Counter()                            # damage dealt to other players so far, by source
            since = collections.defaultdict(collections.Counter)     # attackers at me since my last turn began
            recent = collections.defaultdict(collections.Counter)    # the same, frozen at the start of my turn
            for s in ids:
                G[label(s)]['seat_games'] += 1

            def ask(s, kind, by):
                """by: opponent seat -> weight (attackers, or aims). One event of `kind` by seat s."""
                opp = [o for o, x in state.items() if o != s and x['alive']]
                if len(opp) < 2:
                    return
                by = {o: k for o, k in by.items() if o in opp}
                n = sum(by.values())
                if not n:
                    return
                c = G[label(s)]
                c[kind + ' events'] += 1; c[kind + ' n'] += n
                picks = {
                    'biggest board': unique(opp, lambda o: state[o]['bf'] - state[o]['lands'], True),
                    'highest life': unique(opp, lambda o: state[o]['life'], True),
                    'lowest life': unique(opp, lambda o: state[o]['life'], False),
                    'the winner': winner if winner in opp else None,
                    'hurt me most': unique(opp, lambda o: hurt[s][o], True),
                    'hurt the table': unique(opp, lambda o: dealt[o], True),
                }
                if kind == 'attack':
                    who = [o for o in opp if recent[s][o] > 0]
                    picks['attacked me'] = who[0] if len(who) == 1 else None
                for cat, tgt in picks.items():
                    if tgt is None:
                        continue
                    c[f'{kind} {cat} n'] += n; c[f'{kind} {cat} hit'] += by.get(tgt, 0); c[f'{kind} {cat} chance'] += n / len(opp)

            for e in events(evf):
                et = e['e']
                if et == 'turn':
                    state = {x['seat']: x for x in e['state']}
                    s = e['seat']
                    recent[s] = since[s]; since[s] = collections.Counter()
                elif state is None:
                    continue
                elif et == 'damage':
                    src = e.get('source_seat')
                    if src is not None and src != e['seat']:
                        hurt[e['seat']][src] += e['amount']; dealt[src] += e['amount']
                elif et == 'attack':
                    s = e['seat']
                    by = collections.Counter(a['defender_seat'] for a in e['attacks'] if a.get('defender_seat') is not None)
                    ask(s, 'attack', by)
                    for d, k in by.items():
                        since[d][s] += k
                elif et == 'cast' and not e.get('copy'):
                    s = e['seat']
                    by = collections.Counter(); what = collections.Counter()
                    for o in e.get('target_seats') or []:
                        if o != s:
                            by[o] += 1; what['a player'] += 1
                    for name in e.get('targets') or []:
                        owners = [o for o, l in lists.items() if name in l]
                        if len(owners) == 1 and owners[0] != s:
                            o = owners[0]; by[o] += 1
                            t = ctype.get(name, '')
                            what['a commander' if name in cmdrs[o] else 'a creature' if 'Creature' in t else 'another permanent or spell'] += 1
                    if by:
                        c = G[label(s)]
                        c['aims all'] += sum(by.values())
                        c['aims by spell'] += sum(by.values()) if e.get('spell') else 0
                        for k, v in what.items():
                            c['aim at ' + k] += v
                        ask(s, 'aim', by)
    return games, G


def report(games, G):
    out = {'games': games, 'groups': {}}
    for grp in sorted(G):
        c = G[grp]; sg = c['seat_games'] or 1
        row = {'seat_games': int(c['seat_games']), 'aims_per_seat_game': round(c['aims all'] / sg, 2),
               'aims_by_spell_share': round(c['aims by spell'] / c['aims all'], 3) if c['aims all'] else None,
               'aim_at': {k[7:]: int(v) for k, v in c.items() if k.startswith('aim at ')}}
        for kind in ('attack', 'aim'):
            row[kind] = {'events': int(c[kind + ' events']), 'n': int(c[kind + ' n'])}
            for cat in CATS:
                n = c[f'{kind} {cat} n']
                if n:
                    row[kind][cat] = {'n': int(n), 'share': round(c[f'{kind} {cat} hit'] / n, 3), 'chance': round(c[f'{kind} {cat} chance'] / n, 3)}
        out['groups'][grp] = row
    return out


def text(res):
    print(f"{res['games']} games")
    for grp, r in res['groups'].items():
        print(f"\n{grp}: {r['seat_games']} seat-games; {r['aims_per_seat_game']} aims at an opponent a game "
              f"({(r['aims_by_spell_share'] or 0) * 100:.0f}% by spells), at {r['aim_at']}")
        for kind, word in (('attack', 'attackers'), ('aim', 'aims')):
            k = r[kind]
            print(f"  {k['n']} {word} in {k['events']} events with two or more opponents alive; share at (chance):")
            for cat in CATS:
                if cat in k:
                    x = k[cat]
                    print(f"    {cat:<15} {x['share'] * 100:5.1f}%  ({x['chance'] * 100:.1f}%)  of {x['n']}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--by-deck', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    games, G = collect(a.runs, a.arm, a.by_deck)
    res = report(games, G)
    text(res)
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
