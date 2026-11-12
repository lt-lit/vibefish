#!/usr/bin/env python3
"""verify_batch.py DECK NAME [STOCK_DIR PLAYBOOK_DIR]: the candidate playbook/variants/DECK-NAME.json against the playbook
its validation run recorded; then the pair of kill turns."""
import json, glob, os, sys, subprocess
deck,name=sys.argv[1],sys.argv[2]
R='/home/user/vibefish'
W=f'/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/batch/{deck}'
sd=sys.argv[3] if len(sys.argv)>3 else W+'/results/val-stock'
pd=sys.argv[4] if len(sys.argv)>4 else W+'/results/val-playbook'
cand=json.load(open(f'{R}/playbook/variants/{deck}-{name}.json'))
pb=cand['playbook']
print('keys',list(cand.keys()),'| deck',cand.get('deck'),'| variant',cand.get('variant'),'| of',cand.get('of'))
rules=lambda b: b['cast']['rules'] if isinstance(b.get('cast'),dict) else (b.get('cast') or [])
print('cast rules',len(rules(pb)),'| trigger rules',len(pb.get('triggers') or []),'| attack',json.dumps(pb.get('attack'))[:150],'| mulligan',json.dumps(pb.get('mulligan'))[:80])
n=same=0; seeds=[]
for f in sorted(glob.glob(pd+'/**/run.json',recursive=True)):
    run=json.load(open(f)); mine=[d for d in run['decks'] if d['id']==deck or deck in d.get('file','').lower().replace(' ','-')]
    if not mine: mine=[d for d in run['decks'] if d.get('playbook')]
    body=mine[0].get('playbook') or {}
    n+=1; seeds.append(run.get('seed_base'))
    att=dict(body.get('attack') or {}); att.pop('damage_per_loss',None)
    catt=dict(pb.get('attack') or {}); catt.pop('damage_per_loss',None)
    ok=(body.get('cast')==pb.get('cast') and (body.get('triggers') or [])==(pb.get('triggers') or []) and att==catt and body.get('mulligan')==pb.get('mulligan'))
    same+=ok
    if not ok and n<=2:
        for k in ('cast','triggers','attack','mulligan'): print('   differs' if body.get(k)!=pb.get(k) else '   same   ',k)
print(f'validation run: {n} run.json files, recorded playbook equals the file in {same}; seed bases {min(seeds) if seeds else None}..{max(seeds) if seeds else None}')
out=subprocess.run(['python3',R+'/runner/hands.py','compare',sd,pd],capture_output=True,text=True)
print((out.stdout or out.stderr)[-900:])
