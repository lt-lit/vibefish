#!/usr/bin/env python3
"""finish_candidate.py DECK NAME BASE: check a candidate against its validation run, write its Forge-attack sibling,
copy the goldfish pair into demo-data. BASE is the validation seed base (e.g. 21101)."""
import json, os, shutil, subprocess, sys, collections
deck, name, base = sys.argv[1], sys.argv[2], int(sys.argv[3])
R = '/home/user/vibefish'; S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = f'{S}/batch/{deck}'
out = subprocess.run(['python3', '-I', f'{S}/bin/verify_batch.py', deck, name], capture_output=True, text=True, cwd=R)
print((out.stdout + out.stderr)[-1500:])
cand_p = f'{R}/playbook/variants/{deck}-{name}.json'
cand = json.load(open(cand_p), object_pairs_hook=collections.OrderedDict)
pb = cand['playbook']
if pb.get('attack'):
    sib = collections.OrderedDict(cand)
    sib['variant'] = f'{name}-forgeattack'; sib['of'] = f'playbook/variants/{deck}-{name}.json'
    sib['about'] = (f"The {name} candidate's cast and trigger rules with the attack left to Forge (no attack policy), for a "
                    "side-by-side run on the same tables. Only the playbook object is read.")
    sib['playbook'] = collections.OrderedDict((k, v) for k, v in pb.items() if k != 'attack')
    sp = f'{R}/playbook/variants/{deck}-{name}-forgeattack.json'
    json.dump(sib, open(sp, 'w'), indent=1, ensure_ascii=False); open(sp, 'a').write('\n')
    print('sibling written:', os.path.relpath(sp, R))
else:
    print('candidate has no attack block: no sibling needed (it IS the Forge-attack version)')
pairs = [f for f in os.listdir(W) if f.endswith('pair.json')]
dst_dir = f'{R}/demo-data/goldfish/2026-11-13'; os.makedirs(dst_dir, exist_ok=True)
if pairs:
    src = os.path.join(W, sorted(pairs)[0]); dst = f'{dst_dir}/{deck}-seeds-{base}-{base+39}.json'
    shutil.copy(src, dst); p = json.load(open(dst))
    print('pair copied:', os.path.relpath(dst, R), '|', json.dumps({k: v for k, v in p['paired'].items()})[:300],
          '| stock', p['a'].get('kill_turn_mean'), 'candidate', p['b'].get('kill_turn_mean'), 'games', p['a'].get('games'), p['b'].get('games'))
else:
    print('NO pair file in', W, os.listdir(W))
