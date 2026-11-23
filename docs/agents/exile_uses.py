#!/usr/bin/env python3
"""exile_uses.py RUN_DIR... --deck ID [--ability TEXT] [--arm ARM] [--show] [--json OUT]: what a trigger that exiles cards from
its controller's graveyard took, use by use. A session helper; read-only.

Written for Winter, Cynical Opportunist (DESIGN.md section 47): "Delirium: at the beginning of your end step, you may exile any
number of cards from your graveyard with four or more card types among them. If you do, put a permanent card from among them
onto the battlefield." Forge's AI answers "any number" with the whole graveyard.

RUN_DIR is a league run (shard-N/gNNNNN) or an ab.py run directory (arm-*/gNNNN); several are read as one. For the seat of
the deck named: every line on which an ability whose text holds TEXT (default "Delirium") goes on the stack, the cards that
then leave its graveyard for exile before anything else is cast, the size of its graveyard before, and the card that comes
from exile onto the battlefield. Then the sums: the triggers, the uses (at least one card exiled), the cards exiled a use,
the uses that took the whole graveyard or all but one card, and what was brought back, by card.
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
    ap.add_argument('--deck', required=True)
    ap.add_argument('--ability', default='Delirium')
    ap.add_argument('--arm')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    T = collections.Counter()
    back = collections.Counter()
    rows = []
    stats = collections.Counter()
    for rj, run, g, evs in games(a.run_dirs, a.arm):
        ids = {d['seat']: d['id'] for d in run['decks']}
        s = next((k for k, v in ids.items() if v == a.deck), None)
        if s is None:
            continue
        T['games'] += 1
        T['wins'] += any(p.get('won') and p['seat'] == s for p in g['players'])
        for k, v in ((g.get('playbook_stats_by_seat') or {}).get(a.deck) or {}).items():
            if k.startswith('trigger_types'):
                stats[k] += v
        gy = 0
        for i, e in enumerate(evs):
            k = e['e']
            if k == 'turn':
                st = next((p for p in e.get('state') or [] if p['seat'] == s), None)
                if st is not None:
                    gy = st.get('gy') or 0
            elif k == 'zone' and e.get('seat') == s:
                gy += (e.get('to') == 'Graveyard') - (e.get('from') == 'Graveyard')
            elif k == 'cast' and e.get('seat') == s and not e.get('spell') and a.ability in str(e.get('ability')):
                T['triggers'] += 1
                n, came = 0, None
                for x in evs[i + 1:i + 400]:
                    if x['e'] in ('turn', 'cast'):
                        break
                    if x['e'] == 'zone' and x.get('seat') == s:
                        if x.get('from') == 'Graveyard' and x.get('to') == 'Exile':
                            n += 1
                        elif x.get('from') == 'Exile' and x.get('to') == 'Battlefield':
                            came = x.get('card') or '(no name in the log)'
                if n:
                    T['uses'] += 1
                    T['exiled'] += n
                    T['graveyard_before'] += gy
                    T['whole'] += n >= gy - 1
                    T['four_or_fewer'] += n <= 4
                    back[came] += 1
                    rows.append({'game': os.path.relpath(os.path.dirname(rj), os.path.dirname(os.path.dirname(os.path.dirname(rj)))), 't': e['t'],
                                 'graveyard': gy, 'exiled': n, 'back': came})
    u = T['uses'] or 1
    print(f"{a.deck}: {T['games']} games ({T['wins']} won); the trigger {T['triggers']} times, used {T['uses']} "
          f"({T['uses'] / max(1, T['games']):.2f} a game)")
    print(f"  a use: {T['exiled'] / u:.1f} cards exiled from a graveyard of {T['graveyard_before'] / u:.1f}; the whole graveyard or all but one card "
          f"{T['whole']} ({100 * T['whole'] / u:.0f}%); four cards or fewer {T['four_or_fewer']} ({100 * T['four_or_fewer'] / u:.0f}%)")
    print('  brought back: ' + ', '.join(f'{c} {n}' for c, n in back.most_common(14)))
    if stats:
        print('  ' + ', '.join(f'{k} {v}' for k, v in sorted(stats.items())))
    if a.show:
        for r in rows:
            print(f"    {r['game']:22} turn {r['t']:3}: {r['exiled']} of {r['graveyard']} exiled, back {r['back']}")
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'exile-uses', 'deck': a.deck, 'ability': a.ability, 'totals': dict(T), 'back': dict(back), 'counters': dict(stats), 'uses': rows}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
