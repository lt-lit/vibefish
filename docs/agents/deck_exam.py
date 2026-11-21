#!/usr/bin/env python3
"""deck_exam.py BASE_RUN_DIR CAND_RUN_DIR --deck ID [--card NAME]... [--ability 'CARD|TEXT']... [--counters PREFIX,...]
[--arm playbook] [--json OUT]: one deck's own candidate beside its shipped playbook on the same tables. A session helper.

For the exam of a candidate that is one deck's rules (a card no pilot cast, an ability never used): the two run
directories are the merged shards of the base arm and of the candidate (docs/agents/shards.sh), paired by table. It
prints the wins of the seat under test on the tables both hold, the discordant tables with the exact (sign) test, the
length of the games, and what the candidate was written for: for each --card the games it was in the seat's hand at the
start of one of its turns and the games it was cast in, in each arm; for each --ability the times the seat used an
ability of CARD whose logged text contains TEXT; and with --counters the seat's playbook counters with those prefixes
(games played on harness 0.4.0 or later carry them for each seat).
"""
import argparse, collections, glob, gzip, json, math, os, sys


def games(root, deck, arm):
    out = {}
    for rj in glob.glob(os.path.join(root, '**', f'arm-{arm}', '*', 'run.json'), recursive=True):
        run = json.load(open(rj))
        ids = {d['seat']: d['id'] for d in run['decks']}
        seat = next((s for s, i in ids.items() if i == deck), None)
        if seat is None:
            continue
        for g in run['games']:
            evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                evf += '.gz'
            out[os.path.basename(os.path.dirname(rj))] = (run, g, seat, evf)
    return out


def read(evf):
    op = gzip.open if evf.endswith('.gz') else open
    with op(evf, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def exact(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def arm_stats(gs, tables, cards, abilities, prefixes):
    C = collections.Counter()
    for t in tables:
        run, g, seat, evf = gs[t]
        me = next(p for p in g['players'] if p['seat'] == seat)
        C['games'] += 1
        C['wins'] += bool(me.get('won'))
        C['turns'] += g.get('turns') or 0
        st = (g.get('playbook_stats_by_seat') or {}).get(run['decks'][seat]['id']) or {}
        for k, v in st.items():
            if any(k.startswith(p) for p in prefixes):
                C['counter ' + k] += v
        held = set(); cast = set()
        for e in read(evf):
            if e['e'] == 'turn' and e['seat'] == seat:
                hand = next(s for s in e['state'] if s['seat'] == seat)['hand']
                held.update(c for c in cards if c in hand)
            elif e['e'] == 'cast' and e.get('seat') == seat:
                if e.get('spell') and e.get('card') in cards:
                    cast.add(e['card'])
                elif not e.get('spell'):
                    for card, text in abilities:
                        if e.get('card') == card and text.lower() in (e.get('ability') or '').lower():
                            C[f'ability {card}|{text}'] += 1
        for c in cards:
            C['held ' + c] += c in held or c in cast
            C['cast ' + c] += c in cast
    return C


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('base'); ap.add_argument('cand')
    ap.add_argument('--deck', required=True)
    ap.add_argument('--card', action='append', default=[])
    ap.add_argument('--ability', action='append', default=[])
    ap.add_argument('--counters', default='')
    ap.add_argument('--arm', default='playbook')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    abilities = [tuple(x.split('|', 1)) for x in a.ability]
    prefixes = [p for p in a.counters.split(',') if p]
    b, c = games(a.base, a.deck, a.arm), games(a.cand, a.deck, a.arm)
    tables = sorted(set(b) & set(c))
    if not tables:
        sys.exit('no table in both run directories (check the paths, --deck and --arm)')
    won = lambda gs, t: bool(next(p for p in gs[t][1]['players'] if p['seat'] == gs[t][2]).get('won'))
    only_c = sum(1 for t in tables if won(c, t) and not won(b, t)); only_b = sum(1 for t in tables if won(b, t) and not won(c, t))
    both = sum(1 for t in tables if won(b, t) and won(c, t))
    B, K = arm_stats(b, tables, a.card, abilities, prefixes), arm_stats(c, tables, a.card, abilities, prefixes)
    n = len(tables)
    print(f'{a.deck}: {n} tables in both ({len(b)} base, {len(c)} candidate)')
    print(f'  wins: shipped {B["wins"]}, candidate {K["wins"]} ({100 * (K["wins"] - B["wins"]) / n:+.1f} points); only the candidate {only_c}, only the shipped playbook {only_b}, both {both}; exact test {exact(only_c, only_b):.3f}')
    print(f'  game length: shipped {B["turns"] / n:.1f} turns, candidate {K["turns"] / n:.1f}')
    for card in a.card:
        print(f'  {card}: shipped cast in {B["cast " + card]} of {B["held " + card]} games it was held, candidate {K["cast " + card]} of {K["held " + card]}')
    for card, text in abilities:
        k = f'ability {card}|{text}'
        print(f'  {card} ("{text}"): used {B[k]} times under the shipped playbook, {K[k]} under the candidate')
    for k in sorted(x for x in set(B) | set(K) if x.startswith('counter ')):
        print(f'  {k[8:]}: shipped {B[k]}, candidate {K[k]}')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'deck-exam', 'deck': a.deck, 'tables': n, 'only_candidate': only_c, 'only_shipped': only_b, 'both': both,
                       'exact_p': round(exact(only_c, only_b), 4), 'shipped': dict(B), 'candidate': dict(K)}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
