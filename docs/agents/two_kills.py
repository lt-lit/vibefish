#!/usr/bin/env python3
"""two_kills.py RUN_DIR...: turns on which a seat was sure to kill two or more opponents (each by itself), took exactly one of them out,
and what became of the seat before its own next turn. Every seat of every game (league directories or ab run directories)."""
import collections, glob, gzip, json, os, sys


def games(roots):
    for root in roots:
        for rj in sorted(glob.glob(os.path.join(root, 'shard-*', '*', 'run.json')) + glob.glob(os.path.join(root, 'arm-*', '*', 'run.json'))):
            run = json.load(open(rj)); g = run['games'][0]
            fs = glob.glob(os.path.join(os.path.dirname(rj), 'games', '*events*'))
            if not fs:
                continue
            op = gzip.open if fs[0].endswith('.gz') else open
            with op(fs[0], 'rt', encoding='utf-8') as f:
                evs = [json.loads(l) for l in f if l.strip()]
            yield run, g, evs


def main(argv):
    C = collections.Counter(); ex = []
    for run, g, evs in games(argv):
        ids = {d['seat']: d['id'] for d in run['decks']}
        lost = {x['seat']: x['t'] for x in evs if x['e'] == 'lost'}
        turns = [(x['t'], x['seat']) for x in evs if x['e'] == 'turn']
        nxt_own = {}
        for i, (t, s) in enumerate(turns):
            nxt_own[(s, t)] = next((t2 for t2, s2 in turns[i + 1:] if s2 == s), None)
        order = [s for _, s in turns]
        last_dmg = {}                                   # seat -> (turn, source seat) of the last damage it took
        dmg_by_turn = collections.defaultdict(lambda: collections.Counter())
        for x in evs:
            if x['e'] == 'damage' and x.get('source_seat') is not None:
                dmg_by_turn[(x['seat'], x['t'])][x['source_seat']] += x.get('amount', 0)
        for x in evs:
            if x['e'] != 'combat':
                continue
            s, t = x.get('seat'), x['t']
            defs = [d for d in x.get('defenders') or [] if d['life'] > 0]
            kill = [d for d in defs if d['through'] >= d['life'] or ((d.get('cmd') or 0) >= 21)]
            if len(kill) < 2:
                continue
            C['turns'] += 1
            out = [d for d in kill if lost.get(d['seat']) == t]
            if len(defs) == len(kill) and len(out) == len(kill):
                C['killed all'] += 1
                continue
            if len(out) != 1:
                C['killed none' if not out else 'killed several, not all'] += 1
                continue
            C['killed exactly one'] += 1
            dg = lambda d: d['life'] + 2 * (d.get('permanents') or 0)
            took = out[0]; left = [d for d in kill if d is not took]
            top = max(kill, key=dg)
            which = 'the most dangerous of the killable' if dg(took) >= max(dg(d) for d in left) else 'a less dangerous one'
            n = nxt_own.get((s, t))
            dead = s in lost and lost[s] > t and (n is None or lost[s] < n)
            C[f'took {which}'] += 1
            if dead:
                C[f'took {which}: seat out before its next turn'] += 1
                killers = dmg_by_turn.get((s, lost[s]), {})
                k = max(killers, key=killers.get) if killers else None
                by = 'a killable one it left' if k in [d['seat'] for d in left] else 'another opponent' if k is not None else 'not by damage'
                C[f'took {which}: out, by {by}'] += 1
                if len(ex) < 12:
                    ex.append((ids[s], t, ids[took['seat']], [ids[d['seat']] for d in left], ids.get(k), which))
    for k, v in sorted(C.items()):
        print(f'  {v:6}  {k}')
    for e in ex:
        print('   ', e)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
