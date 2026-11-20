#!/usr/bin/env python3
"""block_check.py CARDSFOLDER_ZIP RUN_DIR...: the deaths by a block not made (`runner/mistakes.py`), checked. A session helper.

How many had an attacker with trample in its card script (a block does not stop all of a trampler's damage; logs of harness 0.4.0 credit the block in
full, 0.4.1 and later count a trampler as not stopped), in how many the seat made no block at all, and how far under the seat's life the best blocks
would have left the attack. CARDSFOLDER_ZIP is forge/runtime-snapshot/res/cardsfolder/cardsfolder.zip."""
import collections, glob, gzip, json, os, sys, zipfile, re
z = zipfile.ZipFile(sys.argv[1])
trample = set()
for n in z.namelist():
    if not n.endswith('.txt'):
        continue
    t = z.read(n).decode('utf-8', 'replace')
    m = re.search(r'^Name:(.+)$', t, re.M)
    if not m:
        continue
    names = re.findall(r'^Name:(.+)$', t, re.M)
    if re.search(r'^K:Trample', t, re.M):
        trample.update(x.strip() for x in names)
C = collections.Counter()
margin = collections.Counter()
ex = []
for root in sys.argv[2:]:
    for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
        run = json.load(open(rj))
        ids = {d['seat']: d['id'] for d in run['decks']}
        g = run['games'][0]
        evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
        if not os.path.exists(evf):
            evf += '.gz'
        op = gzip.open if evf.endswith('.gz') else open
        with op(evf, 'rt', encoding='utf-8') as f:
            evs = [json.loads(l) for l in f if l.strip()]
        lost_at = {e['seat']: e['t'] for e in evs if e['e'] == 'lost'}
        for e in evs:
            if e['e'] != 'block' or 'incoming' not in e:
                continue
            d = e['seat']
            if not (e['incoming'] >= e['life'] > 0 and lost_at.get(d) == e['t']):
                continue
            C['combat_deaths'] += 1
            if e['best'] < e['life']:
                C['block_not_made'] += 1
                att = [b['attacker'] for b in e['blocks']]
                tr = [a for a in att if a in trample]
                blocked = sum(1 for b in e['blocks'] if b['blockers'])
                C['with_trampler' if tr else 'no_trampler'] += 1
                C['made_no_block_at_all' if blocked == 0 else 'made_some_blocks'] += 1
                margin[min(10, e['life'] - e['best'])] += 1
                if not tr and len(ex) < 12:
                    ex.append((os.path.relpath(evf, root), e['t'], ids[d], e['life'], e['incoming'], e['best'], len(att), blocked))
print(dict(C))
print('life minus what the best blocks would have let through (10 = ten or more):', sorted(margin.items()))
for x in ex:
    print('  ', x)
