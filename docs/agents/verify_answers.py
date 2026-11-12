#!/usr/bin/env python3
"""verify_answers.py DECK: the candidate playbook/variants/DECK-answers.json against the shipped playbook and
against the playbook recorded in each of its agent's local runs."""
import json, glob, os, hashlib, sys
deck=sys.argv[1]
R='/home/user/vibefish'
W=f'/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/batch/answers-{deck}'
cand=json.load(open(f'{R}/playbook/variants/{deck}-answers.json'))
ship=json.load(open(f'{R}/playbook/precons/{deck}.json'))
pb=cand['playbook']; sp=ship['playbook']
rules=lambda b: b['cast']['rules'] if isinstance(b.get('cast'),dict) else b.get('cast')
print('top keys',list(cand.keys()),'| deck',cand.get('deck'),'| variant',cand.get('variant'),'| of',cand.get('of'),'| version',pb.get('version'),'(shipped',sp.get('version'),')')
print('attack as shipped:',pb.get('attack')==sp.get('attack'),'| triggers as shipped:',pb.get('triggers')==sp.get('triggers'),'| mulligan as shipped:',pb.get('mulligan')==sp.get('mulligan'),'| on as shipped:',pb.get('on')==sp.get('on'))
if isinstance(sp.get('cast'),dict):
    print('cast groups as shipped:',{k:(pb['cast'].get(k)==v) for k,v in sp['cast'].items() if k!='rules'}, '| extra cast keys in candidate:',[k for k in pb['cast'] if k not in sp['cast']])
cs=rules(sp); cc=rules(pb)
idx=[cc.index(r) if r in cc else None for r in cs]
print('shipped rules',len(cs),'candidate rules',len(cc),'| all shipped present:',None not in idx,'| in order:',[i for i in idx if i is not None]==sorted(i for i in idx if i is not None),'| positions',idx)
sig=lambda b: hashlib.sha1(json.dumps([b.get('cast'),b.get('triggers')],sort_keys=True).encode()).hexdigest()[:8]
print('candidate sig',sig(pb),'| shipped sig',sig(sp))
for rd in sorted(glob.glob(W+'/results/*')):
    if not os.path.isdir(rd): continue
    for arm in sorted(glob.glob(rd+'/arm-*')):
        seen={}
        for f in sorted(glob.glob(arm+'/g*/run.json')):
            run=json.load(open(f)); mine=[d for d in run['decks'] if d['id']==deck][0]
            body=mine.get('playbook')
            k=sig(body) if body else 'stock'
            won=any(p.get('won') and p.get('seat')==mine['seat'] for gm in run['games'] for p in gm.get('players',[]))
            s=seen.setdefault(k,{'g':[], 'w':0, 'seed':run.get('seed_base')}); s['g'].append(os.path.basename(os.path.dirname(f))); s['w']+=won
        for k,v in seen.items():
            tag='<- the candidate file' if k==sig(pb) else ('(shipped)' if k==sig(sp) else '')
            print(f"  {os.path.basename(rd)}/{os.path.basename(arm)}: {k} {v['g'][0]}..{v['g'][-1]} {len(v['g'])} tables, {v['w']} won {tag}")
print('new rules:')
for i,r in enumerate(cc):
    if r not in cs: print(f'  {i+1:2d}', json.dumps(r)[:260])
