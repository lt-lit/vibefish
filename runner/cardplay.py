#!/usr/bin/env python3
"""What a seat did with each card it drew, from the JSONL event logs: the sim's side of Playgroup's card pages.
Read-only; prints text.

  runner/cardplay.py RUN_DIR --deck ID [--arm ARM] [--reference runner/reference/playgroup-cards.json]
                     [--min-drawn 10] [--lands] [--json OUT.json]

RUN_DIR is a league run (shard-*/g*/run.json), an ab.py run (arm-*/g*/run.json; --arm picks the arm, default
`playbook` when the run has one) or a pod or goldfish run (shard-*/run.json). For every card of the deck, over the
games the deck played in that run:

  drawn       games in which the card was in the seat's hand at the start of a turn, or was cast from hand
  played      games in which the seat cast it (a land: played it)
  share       played / drawn: Playgroup's "Drawn -> Played"
  turn        the seat's own turn of the first cast: median, with the quartiles
  same turn   share of those casts made on the turn the card was drawn (it was not in hand at the start of an
              earlier own turn)

With --reference only the cards the reference has are listed, each beside people's figures for the same card and
the gap in points. The reference (runner/reference/playgroup-cards.json) is per card over every deck that runs
it, from games on Playgroup Live; the sim's figure is one deck at one kind of table. A card people play in two
games of three that a seat plays in one of thirty is a difference in how the deck is played; a few points are not.
Commanders are left out (they are not drawn). Standard library only."""
import argparse, collections, glob, json, os, signal, statistics as st, sys


def events(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def game_dirs(rd, arm):
    """(directory holding run.json) for every game set of the run, narrowed to one arm of an A/B run."""
    if os.path.exists(os.path.join(rd, 'ab.json')):
        arms = sorted(os.path.basename(a)[4:] for a in glob.glob(os.path.join(rd, 'arm-*')))
        arm = arm or ('playbook' if 'playbook' in arms else arms[0])
        if arm not in arms:
            sys.exit(f"cardplay.py: no arm {arm} in {rd} (it has {', '.join(arms)})")
        return sorted(glob.glob(os.path.join(rd, f'arm-{arm}', 'g*'))), arm
    out = []
    for d in sorted(glob.glob(os.path.join(rd, 'shard-*'))):
        if os.path.exists(os.path.join(d, 'run.json')):
            out.append(d)
        else:
            out += sorted(glob.glob(os.path.join(d, 'g*')))
    return out, None


def quartile(xs, p):
    xs = sorted(xs)
    return xs[int(p * (len(xs) - 1))] if xs else None


def collect(rd, deck_id, arm, lands):
    dirs, arm = game_dirs(rd, arm)
    C = collections.defaultdict(lambda: {'drawn': 0, 'played': 0, 'turns': [], 'same': 0})
    games = 0; info = {}; halves = {}
    for gd in dirs:
        rj = os.path.join(gd, 'run.json')
        if not os.path.exists(rj):
            continue
        run = json.load(open(rj, encoding='utf-8'))
        mine = [d for d in run['decks'] if d['id'] == deck_id]
        if not mine:
            continue
        seat = mine[0]['seat']
        commanders = set(mine[0].get('commanders') or [])
        for c in mine[0]['cards']:
            info[c['name']] = c
            if ' // ' in c['name']:                     # a split card is cast by the name of one half
                for half in c['name'].split(' // '):
                    halves[half] = c['name']
        for g in run['games']:
            evf = os.path.join(gd, 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                continue
            games += 1
            own = 0; first_in_hand = {}; first_cast = {}
            for e in events(evf):
                k = e['e']
                if k == 'turn':
                    if e['seat'] == seat:
                        own = e['own_turn']
                    me = next(x for x in e['state'] if x['seat'] == seat)
                    for c in me.get('hand') or []:
                        first_in_hand.setdefault(c, own)
                elif k == 'cast' and e.get('seat') == seat and e.get('spell') and not e.get('copy') and e.get('from') == 'Hand':
                    first_cast.setdefault(halves.get(e['card'], e['card']), own)
                elif k == 'land' and e.get('seat') == seat and lands:
                    first_cast.setdefault(e['card'], own)
            for c in set(first_in_hand) | set(first_cast):
                if c in commanders or c not in info or (info[c].get('land') and not lands):
                    continue
                s = C[c]; s['drawn'] += 1
                if c in first_cast:
                    s['played'] += 1; s['turns'].append(first_cast[c])
                    # in hand at the start of this own turn already counts as drawn this turn only if it was not there
                    # at the start of an earlier own turn
                    if c not in first_in_hand or first_in_hand[c] >= first_cast[c]:
                        s['same'] += 1
    rows = {}
    for c, s in C.items():
        rows[c] = {'drawn': s['drawn'], 'played': s['played'], 'share': round(s['played'] / s['drawn'], 3) if s['drawn'] else None,
                   'median_turn': st.median(s['turns']) if s['turns'] else None, 'p25': quartile(s['turns'], .25), 'p75': quartile(s['turns'], .75),
                   'same_turn': round(s['same'] / s['played'], 3) if s['played'] else None,
                   'mv': info[c].get('cmc'), 'type': info[c].get('type')}
    return {'kind': 'cardplay', 'deck': deck_id, 'arm': arm, 'run': os.path.basename(os.path.abspath(rd)), 'games': games, 'cards': rows}


def pct(x):
    return '  n/a' if x is None else f"{100 * x:4.0f}%"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dir')
    ap.add_argument('--deck', required=True)
    ap.add_argument('--arm')
    ap.add_argument('--reference', help='per-card human figures (runner/reference/playgroup-cards.json): list those cards with the gap')
    ap.add_argument('--min-drawn', type=int, default=10, help='without --reference, list cards drawn in at least this many games')
    ap.add_argument('--lands', action='store_true', help='include lands')
    ap.add_argument('--json', help='also write the numbers here (kind "cardplay")')
    args = ap.parse_args(argv)
    res = collect(args.run_dir, args.deck, args.arm, args.lands)
    if not res['games']:
        sys.exit(f"cardplay.py: no games of {args.deck} with event logs in {args.run_dir}")
    ref = {}
    if args.reference:
        r = json.load(open(args.reference, encoding='utf-8'))
        ref = r.get('cards') or {}
        res['reference'] = {'file': args.reference, 'source': r.get('source'), 'retrieved': r.get('retrieved')}
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
            f.write('\n')
    print(f"{args.deck}{' (' + res['arm'] + ' arm)' if res['arm'] else ''}, {res['games']} games of {res['run']}")
    cards = res['cards']
    if ref:
        names = [c for c in ref if c in cards]
        print(f"  {'card':30s} {'drawn':>5s} {'played':>6s} {'share':>6s} {'turn':>12s}   | people {'share':>6s} {'turn':>10s}  drawn |  gap")
        for c in sorted(names, key=lambda n: (cards[n]['share'] or 0) - ref[n]['drawn_played']):
            s = cards[c]; h = ref[c]
            turn = f"{s['median_turn']:g} ({s['p25']}-{s['p75']})" if s['median_turn'] is not None else '-'
            hturn = f"{h['median_cast_turn']:g} ({h['p25']}-{h['p75']})"
            gap = 100 * ((s['share'] or 0) - h['drawn_played'])
            print(f"  {c:30s} {s['drawn']:5d} {s['played']:6d} {pct(s['share'])} {turn:>12s}   |        {pct(h['drawn_played'])} {hturn:>10s} {h['ever_drawn']:6d} | {gap:+5.0f}")
    else:
        print(f"  {'card':30s} {'mv':>3s} {'drawn':>5s} {'played':>6s} {'share':>6s} {'turn':>12s} {'same turn':>10s}")
        for c in sorted((n for n in cards if cards[n]['drawn'] >= args.min_drawn), key=lambda n: (cards[n]['share'] or 0, n)):
            s = cards[c]
            turn = f"{s['median_turn']:g} ({s['p25']}-{s['p75']})" if s['median_turn'] is not None else '-'
            print(f"  {c:30s} {s['mv'] if s['mv'] is not None else '':>3} {s['drawn']:5d} {s['played']:6d} {pct(s['share'])} {turn:>12s} {pct(s['same_turn']):>10s}")


if __name__ == '__main__':
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)      # piping into head is the normal way to read it
    main(sys.argv[1:])
