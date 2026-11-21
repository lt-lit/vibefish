#!/usr/bin/env python3
"""first_change.py BASE_RUN_DIR CAND_RUN_DIR DECK: table by table, where a candidate's game first departs from the base
game, and how each ended. A session helper.

For a trial of one deck's candidate on replayed tables (both run directories hold arm-playbook/gNNNN, the output of
runner/ab.py or of docs/agents/shards.sh): the first cast, attack, land, turn or loss at which the two games of a table
differ, whose it was (SEAT is the seat under test), and both outcomes; then the pairs counted by who made the first
difference. It is the ten-minute reading that says what a candidate's rule actually changed: on 2026-11-21 it showed a
Nesting Grounds rule taking the -1/-1 counters off Tree of Perdition, which the deck puts there on purpose, on tables
whose win counts alone (picked for long games) could not have said so. `first_difference.py` is the same idea for a
whole exam, filed by kind of difference.
"""
import json, os, gzip, glob, sys
base, cand, deck = sys.argv[1:4]
def load(rj):
    run=json.load(open(rj)); g=run['games'][0]
    evf=os.path.join(os.path.dirname(rj),'games',os.path.basename(g['events']))
    if not os.path.exists(evf): evf+='.gz'
    op=gzip.open if evf.endswith('.gz') else open
    return run, g, [json.loads(l) for l in op(evf,'rt') if l.strip()]
def key(e):
    k=e['e']
    if k=='cast': return (k,e['t'],e.get('seat'),e.get('card'),tuple(e.get('targets') or ()), (e.get('ability') or '')[:24])
    if k=='attack': return (k,e['t'],e.get('seat'),tuple(sorted((a['attacker'],a.get('defender_seat')) for a in e['attacks'])))
    if k in ('turn','lost','land','resolve'): return (k,e['t'],e.get('seat'),e.get('card'))
    return None
tot={}
for rj in sorted(glob.glob(os.path.join(cand,'arm-playbook','*','run.json'))):
    t=os.path.basename(os.path.dirname(rj))
    bj=os.path.join(base,'arm-playbook',t,'run.json')
    if not os.path.exists(bj): continue
    a=load(bj); b=load(rj)
    ids={d['seat']:d['id'] for d in a[0]['decks']}
    seat=next(s for s,i in ids.items() if i==deck)
    ka=[k for k in map(key,a[2]) if k]; kb=[k for k in map(key,b[2]) if k]
    f=next((i for i,(x,y) in enumerate(zip(ka,kb)) if x!=y), None)
    won=lambda g: bool(next(p for p in g['players'] if p['seat']==seat).get('won'))
    def short(k):
        return f"{k[0]} t{k[1]} {'SEAT' if k[2]==seat else str(ids.get(k[2],'-'))[:8]} {k[3] if k[0]!='attack' else len(k[3])}" + (f" [{k[5]}]" if k[0]=='cast' and k[5] else '')
    who = 'none' if f is None else ('seat' if kb[f][2]==seat or ka[f][2]==seat else 'other')
    o=('W' if won(a[1]) else 'L')+('W' if won(b[1]) else 'L')
    tot.setdefault(who,{}).setdefault(o,0); tot[who][o]+=1
    print(t, 'base', 'WON ' if won(a[1]) else 'lost', a[1].get('turns'), '| cand', 'WON ' if won(b[1]) else 'lost', b[1].get('turns'), '|', 'identical' if f is None else f"t{kb[f][1]}: {short(ka[f])}  /  {short(kb[f])}")
print('by who made the first difference (base outcome, candidate outcome):', tot)
