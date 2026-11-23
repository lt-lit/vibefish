#!/usr/bin/env python3
"""received.py RUN_DIR... [--json OUT] [--arm ARM]: the game a seat is given, counted from the receiving side. A session helper; read-only.

What the other three players do to a seat's board (DESIGN.md section 29: an opponent's job is to give the deck under test the
game a table would): how often its commander is taken off the battlefield and by what, how many of its other permanents are
answered, and on whose turn. RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory (arm-*/gNNNN); every seat of
every game is counted and grouped by deck.

Every time a card that is not a token and not a land leaves the battlefield (to the graveyard, exile, a hand, a library or the
command zone) the cause is read off the lines around it:

  targeted   the spell that is resolving (the next line that is not a zone or life line is its `resolve`), or the nearest
             earlier cast of the turn, names this card among its targets and is another player's
  swept      the spell that is resolving is another player's and does not name it (a wipe, an edict), or the card left
             right after such a spell resolved
  combat     the nearest earlier line of the turn that is not a zone, life or cast line is a block or combat damage
  own        the resolving spell, or the cast just before, is the seat's own (a cost, a sacrifice, its own wipe)
  other      none of these (an ability without a target, a state the lines do not explain)

The turn is the remover's own, the seat's own (its permanent is answered on its own turn: an attacker, a response), or a third
player's. A removal on a turn that is not the remover's is play on another player's turn (DESIGN.md section 39).
Abilities have no `resolve` line, so a removal by an ability is found through its target only, and a mass effect of an
ability is filed under other. A commander that is removed and put into the command zone is one exit.
"""
import argparse, collections, glob, gzip, json, os, sys

SKIP = {'zone', 'life'}
WINDOW = 40


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
            yield run, g, evs


def cause(evs, i, casts, x, card, active):
    """(kind, remover seat or None, by a spell?, the card that did it or None) for the zone line evs[i]."""
    def names(c):
        return any(n == card and (k >= len(c.get('target_ctrl') or []) or c['target_ctrl'][k] == x) for k, n in enumerate(c.get('targets') or []))
    j = i + 1
    while j < len(evs) and evs[j]['e'] in SKIP:
        j += 1
    if j < len(evs) and evs[j]['e'] == 'resolve':                     # it left while a spell resolved
        c = casts.get(evs[j].get('id'))
        if c is not None:
            if c['seat'] == x:
                return 'own', None, True, c.get('card')
            return ('targeted' if names(c) else 'swept'), c['seat'], True, c.get('card')
    seen = 0
    for k in range(i - 1, -1, -1):
        e = evs[k]
        if e['e'] in SKIP:
            continue
        if e['e'] == 'turn':
            break
        seen += 1
        if seen > WINDOW:
            break
        if e['e'] == 'cast':
            if e.get('seat') != x and names(e):
                return 'targeted', e['seat'], bool(e.get('spell')), e.get('card')
            if seen == 1 and e.get('seat') == x:
                return 'own', None, bool(e.get('spell')), e.get('card')
            continue
        if e['e'] in ('block', 'attack') or (e['e'] == 'damage' and e.get('combat')):
            return 'combat', None, False, None
        if e['e'] == 'resolve':
            c = casts.get(e.get('id'))
            if c is not None and seen <= 3:
                return ('own', None, True, c.get('card')) if c['seat'] == x else ('swept', c['seat'], True, c.get('card'))
            break
    return 'other', None, False, None


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    D = collections.defaultdict(collections.Counter)
    CARDS = collections.defaultdict(collections.Counter)                # what did the answering, by kind
    ngames = 0
    for run, g, evs in games(a.run_dirs, a.arm):
        ngames += 1
        ids = {d['seat']: d['id'] for d in run['decks']}
        cmds = {d['seat']: set(d.get('commanders') or []) for d in run['decks']}
        lands = {d['seat']: {c['name'] for c in d.get('cards') or [] if c.get('land')} for d in run['decks']}
        for s in ids:
            D[ids[s]]['seat_games'] += 1
        casts = {}
        active = None
        hit = collections.defaultdict(set)                            # per seat: what happened to it in this game
        last = {}                                                     # (seat, card id) -> index of its last counted exit, to count one exit once
        for i, e in enumerate(evs):
            k = e['e']
            if k == 'turn':
                active = e.get('seat')
            elif k == 'cast':
                if e.get('id') is not None and e.get('spell'):
                    casts[e['id']] = e
                s = e.get('seat')
                if e.get('spell') and e.get('commander') and e.get('from') == 'Command' and s in ids:
                    D[ids[s]]['commander_casts'] += 1
                for n, t in enumerate(e.get('target_ctrl') or []):
                    if t is not None and t != s and t in ids and n < len(e.get('targets') or []):
                        d = D[ids[t]]
                        d['aimed_spells' if e.get('spell') else 'aimed_abilities'] += 1
                        if e['targets'][n] in cmds[t]:
                            d['aimed_at_commander'] += 1
            elif k == 'zone' and e.get('from') == 'Battlefield' and not e.get('token'):
                x = e.get('seat')
                if x not in ids or e.get('card') in lands[x]:
                    continue
                key = (x, e.get('id'))
                if key in last and i - last[key] <= 3:
                    continue
                last[key] = i
                what, by, spell, with_card = cause(evs, i, casts, x, e.get('card'), active)
                d = D[ids[x]]
                is_cmd = e.get('card') in cmds[x]
                pre = 'cmd_' if is_cmd else 'perm_'
                d[pre + 'exits'] += 1
                d[pre + what] += 1
                if what in ('targeted', 'swept'):
                    CARDS[(pre + what)][with_card] += 1
                    when = 'removers_turn' if active == by else 'own_turn' if active == x else 'third_turn'
                    d[pre + 'answered'] += 1
                    d[pre + 'answered_' + when] += 1
                    d[pre + ('by_spell' if spell else 'by_ability')] += 1
                    if is_cmd:
                        hit[x].add('cmd')
                        d['cmd_answered_turn_sum'] += e.get('t') or 0
                    hit[x].add('any')
        for s, h in hit.items():
            if 'cmd' in h:
                D[ids[s]]['games_cmd_answered'] += 1
            if 'any' in h:
                D[ids[s]]['games_answered'] += 1
    tot = collections.Counter()
    for v in D.values():
        tot.update(v)
    out = {'kind': 'received', 'games': ngames, 'decks': {k: dict(v) for k, v in sorted(D.items())}, 'all': dict(tot),
           'by_card': {k: dict(v.most_common(40)) for k, v in sorted(CARDS.items())}}
    pc = lambda x, y: f'{100 * x / y:5.1f}%' if y else '    - '

    def line(name, v):
        sg = v['seat_games'] or 1
        ca = v['cmd_answered']
        return (f"  {name:22} {v['seat_games']:5}  {v['commander_casts'] / sg:5.2f}  {100 * ca / sg:6.1f}  {pc(v['games_cmd_answered'], sg)}  {v['cmd_targeted']:4} {v['cmd_swept']:4} {v['cmd_combat']:4} {v['cmd_own'] + v['cmd_other']:4}"
                f"   {pc(v['cmd_answered_removers_turn'], ca)} {pc(v['cmd_answered_own_turn'], ca)} {pc(v['cmd_answered_third_turn'], ca)}"
                f"   {v['perm_answered'] / sg:5.2f} {v['perm_targeted'] / sg:5.2f} {v['perm_swept'] / sg:5.2f} {v['perm_combat'] / sg:5.2f}"
                f"   {pc(v['perm_answered_removers_turn'], v['perm_answered'])}   {(v['aimed_spells'] + v['aimed_abilities']) / sg:5.2f} {pc(v['aimed_at_commander'], v['aimed_spells'] + v['aimed_abilities'])}")
    print(f"{ngames} games, every seat, by the deck that receives")
    print("  a deck's commander: casts from the command zone a seat-game; taken off the battlefield by another player's spell or ability, a hundred seat-games; the seat-games in which that")
    print("  happened at least once; exits by cause (targeted, swept, combat, own or other); and of the answers the share on the remover's own turn, on the seat's own turn, on a third player's.")
    print("  its other nonland permanents (no tokens): answered a seat-game, of which targeted and swept; lost in combat; the share of the answers on the remover's own turn.")
    print("  aimed: other players' spells and abilities with one of its permanents as a target, a seat-game, and the share of them at its commander.")
    print(f"  {'':22} {'seats':>5}  {'casts':>5}  {'cmd/100':>6}  {'games':>6}  {'tgt':>4} {'swp':>4} {'cbt':>4} {'oth':>4}   {'theirs':>6} {'own':>6} {'third':>6}   {'ans':>5} {'tgt':>5} {'swp':>5} {'cbt':>5}   {'theirs':>6}   {'aimed':>5} {'at cmd':>6}")
    for k, v in sorted(D.items()):
        print(line(k, v))
    print(line('all decks', tot))
    for k, v in sorted(CARDS.items()):
        print(f"  {k.replace('cmd_', 'a commander ').replace('perm_', 'another permanent ')}, by: " + ', '.join(f'{c} {n}' for c, n in v.most_common(14)))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
