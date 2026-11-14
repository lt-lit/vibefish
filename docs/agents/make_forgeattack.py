#!/usr/bin/env python3
"""make_forgeattack.py DECK NAME [DECK NAME ...]: for each candidate playbook/variants/DECK-NAME.json that has an
attack block, write its sibling DECK-NAME-forgeattack.json: the same cast and trigger rules with the attack left to
Forge, for a side-by-side playbook-only arm on the same tables. A session helper (finish_candidate.py does the same
for a deck-writing agent's candidate)."""
import collections, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
args = sys.argv[1:]
assert args and len(args) % 2 == 0, __doc__
for deck, name in zip(args[0::2], args[1::2]):
    p = f'{R}/playbook/variants/{deck}-{name}.json'
    cand = json.load(open(p, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
    pb = cand['playbook']
    if not pb.get('attack'):
        print(f'{deck}-{name}: no attack block, it is the Forge-attack version already'); continue
    sib = collections.OrderedDict(cand)
    sib['variant'] = f'{name}-forgeattack'; sib['of'] = f'playbook/variants/{deck}-{name}.json'
    sib['about'] = (f"The {name} candidate's cast and trigger rules with the attack left to Forge (no attack policy), for a "
                    "side-by-side run on the same tables. Only the playbook object is read.")
    sib['playbook'] = collections.OrderedDict((k, v) for k, v in pb.items() if k != 'attack')
    sp = f'{R}/playbook/variants/{deck}-{name}-forgeattack.json'
    with open(sp, 'w', encoding='utf-8') as f:
        json.dump(sib, f, indent=1, ensure_ascii=False); f.write('\n')
    rules = pb['cast']['rules'] if isinstance(pb.get('cast'), dict) else pb.get('cast') or []
    print(f'{os.path.relpath(sp, R)}: {len(rules)} cast rules, {len(pb.get("triggers") or [])} trigger rules, attack left to Forge (the candidate has {json.dumps(pb["attack"])[:60]}...)')
