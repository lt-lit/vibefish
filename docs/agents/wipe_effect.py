#!/usr/bin/env python3
"""wipe_effect.py RUN_DIR... --deck ID --card NAME [--card NAME]... [--runtime DIR] [--arm ARM] [--show] [--json OUT]:
what a board wipe took from each side, cast by cast. A session helper; read-only.

Written for the exam of Blight Curse's wipe rules (DESIGN.md section 44, `ab-run` #69): the rules had asked for six
creatures on one opponent's side, the candidate counts the opponents' creatures together, and the question after the
wins is what the casts were worth.

RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory (arm-*/gNNNN); several are read as one. For the seat
of the deck named and each card named: the card-games in which it was held (in the seat's hand at the start of some
turn, or cast) and cast; and per cast the turn, the opponents alive, and the permanents that left the battlefield
between the `cast` line and the next `turn` line, the caster's own and the opponents', so until the end of that turn
(a cast before combat counts that combat's dead as well). With --runtime the count is of creatures: a card by its type
in Forge's card script, a token by its name (Treasure, Food, Clue, Blood, Map and the like are not creatures; a token
that copies a card is looked up as that card), a permanent without a name in the log (face down) as a creature.
Without it, of all permanents, and the output says so.
"""
import argparse, collections, glob, gzip, json, os, statistics, sys

NOT_CREATURE_TOKENS = {'Treasure Token', 'Food Token', 'Clue Token', 'Blood Token', 'Map Token', 'Powerstone Token', 'Gold Token',
                       'Junk Token', 'Incubator Token', 'Shard Token', 'Lander Token', 'Mutagen Token', 'Walker Token'}


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


class Types:
    """Is this permanent a creature? By Forge's card script when a runtime is given; None when it cannot be said."""

    def __init__(self, runtime):
        self.scripts = None
        self.cache = {}
        if runtime:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'runner'))
            import deckdata
            self.scripts = deckdata.CardScripts(runtime)

    def creature(self, name, token):
        if self.scripts is None:
            return True                                   # no runtime: every permanent is counted
        if not name:
            return True                                   # face down: a 2/2 creature
        if token and name in NOT_CREATURE_TOKENS:
            return False
        if token and name.endswith(' Token'):
            return True
        if name not in self.cache:
            c = self.scripts.get(name)
            self.cache[name] = True if c is None else 'Creature' in c['types']
        return self.cache[name]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--deck', required=True)
    ap.add_argument('--card', action='append', required=True)
    ap.add_argument('--runtime')
    ap.add_argument('--arm')
    ap.add_argument('--show', action='store_true', help='print every cast')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    types = Types(a.runtime)
    what = 'creatures' if a.runtime else 'permanents'
    T = collections.Counter()
    per = {c: collections.Counter() for c in a.card}
    rows = []
    for rj, run, g, evs in games(a.run_dirs, a.arm):
        ids = {d['seat']: d['id'] for d in run['decks']}
        s = next((k for k, v in ids.items() if v == a.deck), None)
        if s is None:
            continue
        T['games'] += 1
        won = any(p.get('won') and p['seat'] == s for p in g['players'])
        T['wins'] += won
        held, cast = set(), set()
        alive = len(ids) - 1
        for i, e in enumerate(evs):
            k = e['e']
            if k == 'turn':
                st = e.get('state') or []
                alive = sum(1 for p in st if p['seat'] != s and p.get('alive'))
                me = next((p for p in st if p['seat'] == s), None)
                if me is not None:
                    for c in a.card:
                        if c in (me.get('hand') or []):
                            held.add(c)
            elif k == 'cast' and e.get('seat') == s and e.get('spell') and e.get('card') in per:
                cast.add(e['card'])
                own = theirs = 0
                by = collections.Counter()
                for x in evs[i + 1:]:
                    if x['e'] == 'turn':
                        break
                    if x['e'] == 'zone' and x.get('from') == 'Battlefield' and types.creature(x.get('card'), x.get('token')):
                        if x.get('seat') == s:
                            own += 1
                        else:
                            theirs += 1
                            by[x.get('seat')] += 1
                rows.append({'game': os.path.relpath(os.path.dirname(rj), os.path.dirname(os.path.dirname(os.path.dirname(rj)))), 'card': e['card'],
                             't': e['t'], 'opponents_alive': alive, 'own': own, 'theirs': theirs, 'sides_hit': len(by),
                             'most_on_one_side': max(by.values()) if by else 0, 'won': won})
        for c in a.card:
            per[c]['held'] += c in held or c in cast
            per[c]['cast'] += c in cast
    print(f"{a.deck}: {T['games']} games ({T['wins']} won); {what} that left the battlefield from the cast to the end of that turn")
    out = {'kind': 'wipe-effect', 'deck': a.deck, 'counted': what, 'games': T['games'], 'wins': T['wins'], 'cards': {}, 'casts': rows}
    for c in a.card + ['all the cards named']:
        rs = rows if c not in per else [r for r in rows if r['card'] == c]
        held = sum(p['held'] for p in per.values()) if c not in per else per[c]['held']
        cast = sum(p['cast'] for p in per.values()) if c not in per else per[c]['cast']
        n = len(rs)
        line = f"  {c}: held in {held} card-games, cast in {cast} ({100 * cast / max(1, held):.1f}%), {n} casts"
        d = {'held': held, 'cast': cast, 'casts': n}
        if n:
            d.update({'median_turn': statistics.median(r['t'] for r in rs), 'theirs_mean': round(sum(r['theirs'] for r in rs) / n, 2),
                      'own_mean': round(sum(r['own'] for r in rs) / n, 2), 'own_more_than_theirs': sum(r['own'] > r['theirs'] for r in rs),
                      'nothing_of_theirs': sum(r['theirs'] == 0 for r in rs), 'two_sides_or_more': sum(r['sides_hit'] >= 2 for r in rs),
                      'in_games_won': sum(r['won'] for r in rs)})
            line += (f"; at turn {d['median_turn']:.0f} at the median; a cast took {d['theirs_mean']:.1f} of the opponents' and {d['own_mean']:.1f} of its own; "
                     f"more of its own than of theirs {d['own_more_than_theirs']}; nothing of theirs {d['nothing_of_theirs']}; "
                     f"two or more opponents hit {d['two_sides_or_more']}; in games the seat won {d['in_games_won']}")
        print(line)
        out['cards'][c] = d
    if a.show:
        for r in rows:
            print(f"    {r['game']:24} turn {r['t']:3} {r['card']:20}: theirs {r['theirs']:2} (most on one side {r['most_on_one_side']}, {r['sides_hit']} of {r['opponents_alive']} opponents), "
                  f"own {r['own']}" + (', won the game' if r['won'] else ''))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
