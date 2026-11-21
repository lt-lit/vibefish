#!/usr/bin/env python3
"""unfinished.py RUN_DIR... [-v]: the games of ab.py run directories that ended without a winner. A session helper.

How each ended (Forge's clock, a draw Forge declared, an exception), how long those games took beside all the games, and
what the last turn was made of: the card with the most cast and zone lines in it and whose it was. A chain of forty lines
or more of one card is named as the loop it almost always is. On 2026-11-21 this showed that 22 of the 25 games without a
winner in 2,000 (and a sixth of the play time) were one deck's trigger rule saying yes to a copy that copies itself
(Miracle Worker's Ondu Spiritdancer with Secret Arcade; DESIGN.md section 34). -v lists the games.
"""
import collections, glob, gzip, json, os, sys


def main(argv):
    verbose = '-v' in argv
    roots = [a for a in argv if a != '-v']
    tot = collections.Counter(); by = collections.Counter(); secs = allsecs = 0.0; games = 0
    rows = []
    for root in roots:
        for rj in sorted(glob.glob(os.path.join(root, 'arm-*', '*', 'run.json'))):
            run = json.load(open(rj)); gm = run['games'][0]; games += 1
            allsecs += (gm.get('duration_ms') or 0) / 1000
            if gm.get('winner') is not None:
                continue
            ids = {d['seat']: d['id'] for d in run['decks']}
            evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(gm['events']))
            if not os.path.exists(evf):
                evf += '.gz'
            op = gzip.open if evf.endswith('.gz') else open
            evs = [json.loads(l) for l in op(evf, 'rt') if l.strip()]
            lt = max(e.get('t') or 0 for e in evs)
            last = [e for e in evs if e.get('t') == lt]
            c = collections.Counter((ids.get(e.get('seat')), e.get('card')) for e in last if e['e'] in ('cast', 'zone') and e.get('card'))
            (who, card), n = c.most_common(1)[0] if c else ((None, None), 0)
            tot[gm.get('reason')] += 1
            secs += (gm.get('duration_ms') or 0) / 1000
            by[(gm.get('reason'), f'{who}: {card}' if n >= 40 else 'no long chain in the last turn')] += 1
            rows.append((os.path.basename(root), os.path.basename(os.path.dirname(rj)), gm.get('reason'), lt, len(last), who, card, n))
    print(f"{games} games ({allsecs / 3600:.1f} hours of play), {sum(tot.values())} without a winner {dict(tot)}, which took {secs / 3600:.1f} hours")
    for (reason, what), n in sorted(by.items(), key=lambda x: -x[1]):
        print(f"   {n:3}  {reason:9} {what}")
    if verbose:
        for r in rows:
            print('     ', *r)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
