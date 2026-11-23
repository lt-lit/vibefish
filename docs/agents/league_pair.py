#!/usr/bin/env python3
"""league_pair.py BEFORE_DIR AFTER_DIR [--json OUT]: two league runs on the same seed and cycles, table by table. A session helper; read-only.

A league's schedule and its games' seeds follow from its seed and cycles, so two runs of the same league on the same seed
play the same tables, seat for seat and shuffle for shuffle; what differs is the playbooks (and the harness) they were played
under. This reads the two side by side (shard-N/gNNNNN against the same path): a game of the second run is the first run's
game up to the first decision that differs.

Per deck: the tables it won in both, only before, only after, with the exact test on the two counts. Every seat changes at
once between two leagues, so a deck's difference is its own playbook's and its opponents' together: a description of the
table before and after, not a measurement of one deck's change (that is what the paired A/B of one seat is for).
Over all tables: the same winner in both, the pairs that are the same game to the last cast, attack and loss, the turn and the
kind of the first of those lines that differs, the length of the games, the games without a winner.
"""
import argparse, collections, glob, gzip, json, math, os, sys


def exact(a, b):
    n = a + b
    if not n:
        return 1.0
    pr = [math.comb(n, k) / 2 ** n for k in range(n + 1)]
    return min(1.0, sum(q for q in pr if q <= pr[a] * (1 + 1e-9)))


def load(d):
    run = json.load(open(os.path.join(d, 'run.json')))
    g = run['games'][0]
    evf = os.path.join(d, 'games', os.path.basename(g['events']))
    if not os.path.exists(evf):
        evf += '.gz'
    op = gzip.open if evf.endswith('.gz') else open
    sig = []
    with op(evf, 'rt', encoding='utf-8') as f:
        for l in f:
            if not l.strip():
                continue
            e = json.loads(l)
            k = e['e']
            if k == 'cast':
                sig.append(('cast', e.get('t'), e.get('seat'), e.get('card'), bool(e.get('spell')), tuple(e.get('targets') or ())))
            elif k == 'attack':
                sig.append(('attack', e.get('t'), e.get('seat'), tuple(sorted((x.get('attacker'), x.get('defender')) for x in e.get('attacks') or []))))
            elif k == 'lost':
                sig.append(('lost', e.get('t'), e.get('seat')))
            elif k == 'land':
                sig.append(('land', e.get('t'), e.get('seat'), e.get('card')))
    ids = {x['seat']: x['id'] for x in run['decks']}
    w = next((p['seat'] for p in g['players'] if p.get('won')), None)
    return {'ids': ids, 'winner': ids.get(w), 'turns': g.get('turns') or 0, 'sig': sig, 'ver': {x['id']: (x.get('playbook') or {}).get('version') for x in run['decks']},
            'secs': (g.get('duration_ms') or 0) / 1000}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('before')
    ap.add_argument('after')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    D = collections.defaultdict(collections.Counter)
    T = collections.Counter()
    first = collections.Counter()
    first_t = []
    vers = {'before': {}, 'after': {}}
    for d in sorted(glob.glob(os.path.join(a.before, 'shard-*', 'g*'))):
        e = os.path.join(a.after, os.path.relpath(d, a.before))
        if not os.path.exists(os.path.join(e, 'run.json')):
            T['missing_after'] += 1
            continue
        A, B = load(d), load(e)
        if A['ids'] != B['ids']:
            T['other_seating'] += 1
            continue
        vers['before'].update(A['ver']); vers['after'].update(B['ver'])
        T['tables'] += 1
        T['turns_before'] += A['turns']; T['turns_after'] += B['turns']
        T['secs_before'] += A['secs']; T['secs_after'] += B['secs']
        T['no_winner_before'] += A['winner'] is None; T['no_winner_after'] += B['winner'] is None
        T['same_winner'] += A['winner'] == B['winner']
        i = 0
        sa, sb = A['sig'], B['sig']
        while i < min(len(sa), len(sb)) and sa[i] == sb[i]:
            i += 1
        if i == len(sa) == len(sb):
            T['same_game'] += 1
        else:
            x = sb[i] if i < len(sb) else sa[i]
            first[x[0]] += 1
            first_t.append(x[1] or 0)
        for deck in A['ids'].values():
            c = D[deck]
            c['tables'] += 1
            wa, wb = A['winner'] == deck, B['winner'] == deck
            c['before'] += wa; c['after'] += wb
            c['both' if wa and wb else 'only_before' if wa else 'only_after' if wb else 'neither'] += 1
    n = T['tables'] or 1
    first_t.sort()
    print(f"{T['tables']} tables played in both leagues ({T['missing_after']} missing in the second, {T['other_seating']} with another seating)")
    print(f"  the same winner in both: {T['same_winner']} ({100 * T['same_winner'] / n:.1f}%); the same game to the last cast, attack and loss: {T['same_game']}")
    if first_t:
        print(f"  the first line that differs: turn {first_t[len(first_t) // 2]} at the median (a quarter by turn {first_t[len(first_t) // 4]}, three quarters by turn {first_t[3 * len(first_t) // 4]}); "
              + ', '.join(f'{k} {v}' for k, v in first.most_common()))
    print(f"  turns a game: {T['turns_before'] / n:.1f} before, {T['turns_after'] / n:.1f} after; seconds a game: {T['secs_before'] / n:.0f}, {T['secs_after'] / n:.0f}; "
          f"games without a winner: {T['no_winner_before']}, {T['no_winner_after']}")
    print(f"  {'deck':22} {'versions':>9} {'tables':>6} {'before':>6} {'after':>6}  {'both':>5} {'only before':>11} {'only after':>10}  exact test")
    out = {'kind': 'league-pair', 'tables': dict(T), 'first_difference': dict(first), 'decks': {}}
    for deck, c in sorted(D.items(), key=lambda kv: -kv[1]['after']):
        p = exact(c['only_after'], c['only_before'])
        v = f"{vers['before'].get(deck)} > {vers['after'].get(deck)}"
        print(f"  {deck:22} {v:>9} {c['tables']:6} {c['before']:6} {c['after']:6}  {c['both']:5} {c['only_before']:11} {c['only_after']:10}  {p:.2f}")
        out['decks'][deck] = dict(c, exact_p=round(p, 4), version_before=vers['before'].get(deck), version_after=vers['after'].get(deck))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
