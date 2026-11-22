"""The sure kills of the most dangerous opponent that the seat under test missed, by what the attack it declared was worth:
not gone for; declared and lethal through the defender's best blocks (the block line's `best` >= life) yet survived;
declared and not enough.  python3 -I docs/agents/kill_force.py EXAM_DIR/results ARM_SUFFIX OUT.json DECK...
ARM_SUFFIX is "" for the deck's own arm and "@name" for a candidate's (the directories are ab-<deck><suffix>/arm-playbook).
A reading aid: the count itself is runner/mistakes.py (kill_top_missed, kill_top_no_attack).  DESIGN.md section 38."""
import sys, os, json, collections, importlib.util
spec = importlib.util.spec_from_file_location('mistakes', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'runner', 'mistakes.py'))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
root, suffix, outp, decks = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
orig = M.close_turn
rows = []
def wrapped(G, label, turn, lost_at, examples, where):
    before = len(examples)
    orig(G, label, turn, lost_at, examples, where)
    if turn.get('missed') and len(examples) > before:
        ex = examples[-1]
        c = turn['combat']
        live = [d for d in c['defenders'] if d['life'] > 0]
        kill = [d for d in live if d['through'] >= d['life']]
        sent = {int(k): v for k, v in ex['attacked'].items()}
        blocks = {b.get('seat'): b for b in turn['blocks'] if 'incoming' in b}
        went = [d for d in kill if sent.get(d['seat'])]
        if not went:
            kind = 'not gone for'
        else:
            kinds = []
            for d in went:
                b = blocks.get(d['seat'])
                if b is None:
                    kinds.append('no block line')
                elif b['best'] >= b['life']:
                    kinds.append('lethal as declared, survived')
                else:
                    kinds.append('declared attack not enough')
            kind = 'lethal as declared, survived' if 'lethal as declared, survived' in kinds else kinds[0]
        rows.append({'ex': ex, 'stood': ex['stood'], 'kind': kind, 'able': len(c.get('able') or []), 't': turn['t'], 'where': where,
                     'sent': sent, 'need': [(d['seat'], d['life'], d['through']) for d in kill],
                     'block': {s: (b['life'], b['incoming'], b['best']) for s, b in blocks.items() if s in [d['seat'] for d in went]}})
M.close_turn = wrapped
keep = []
for deck in decks:
    d = os.path.join(root, f'ab-{deck}{suffix}')
    n0 = len(rows)
    M.collect([d], 'playbook', False, deck)
    for r in rows[n0:]:
        if r['ex']['deck'] == deck:
            r['deck'] = deck
            keep.append(r)
out = {}
for stood in ('top', 'last', 'lesser'):
    c = collections.Counter(r['kind'] for r in keep if r['stood'] == stood)
    out[stood] = dict(c)
by = collections.defaultdict(collections.Counter)
for r in keep:
    if r['stood'] == 'top':
        by[r['deck']][r['kind']] += 1
print(suffix or 'shipped', json.dumps(out))
print('   top by deck:', {d: dict(c) for d, c in by.items()})
json.dump({'arm': suffix.lstrip('@') or 'shipped', 'split': out, 'top_by_deck': {d: dict(c) for d, c in by.items()},
           'rows': [{k: v for k, v in r.items() if k != 'ex'} for r in keep if r['stood'] in ('top', 'last')]}, open(outp, 'w'), indent=1)
