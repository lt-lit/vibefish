#!/usr/bin/env python3
"""read_confirming.py HOOK_EXAM_JSON [JOIN_DIR_OF_46]: ab-run #57 (the confirming run of the next versions at the owner's table) read by the rule in
CLAUDE.md, In flight, fixed 2026-11-21 before it was queued. HOOK_EXAM_JSON is what hook_exam.py wrote for the pairs before:shipped and
shipped:guard. A session helper for that one run.
Prints each rule's numbers; decides nothing that the rule does not say."""
import json, math, os, sys

OPEN = ['blight-curse', 'mutant-menace', 'blood-rites', 'death-toll', 'miracle-worker', 'ahoy-mateys']
NO_BLOCK = ['blood-rites', 'miracle-worker']
NO_AIM = ['revenant-recon']


def exact(a, b):
    n = a + b
    if not n:
        return 1.0
    pr = [math.comb(n, k) / 2 ** n for k in range(n + 1)]
    return min(1.0, sum(q for q in pr if q <= pr[a] * (1 + 1e-9)))


def pct(a, b, nd=1):
    return f'{100 * a / b:.{nd}f}%' if b else '-'


def main(argv):
    j = json.load(open(argv[0]))
    decks = list(j['decks'])
    D = j['decks']
    print(f'{len(decks)} decks: {", ".join(decks)}')
    print()
    print('RULE 1. The next versions together (before -> shipped):')
    co = sum(D[d]['pairs']['before:shipped']['cand_only'] for d in decks)
    bo = sum(D[d]['pairs']['before:shipped']['base_only'] for d in decks)
    wb = sum(D[d]['wins']['before'] for d in decks); ws = sum(D[d]['wins']['shipped'] for d in decks); wg = sum(D[d]['wins']['guard'] for d in decks)
    n = sum(D[d]['games']['shipped'] for d in decks)
    p = exact(co, bo)
    print(f'   wins of {n}: before {wb}, next version {ws}, guard {wg}')
    print(f'   tables only the next version won {co}, only the version before won {bo}, exact test {p:.4f}')
    print('   -> ' + ('STAND (at least as many)' if co >= bo else ('STAND (fewer, inside noise)' if p > 0.05 else 'DO NOT STAND: all ten go back')))
    print()
    print('RULE 2. Each deck (goes back only if behind with an exact test below 0.05):')
    for d in decks:
        pr = D[d]['pairs']['before:shipped']
        back = pr['cand_only'] < pr['base_only'] and pr['exact_p'] is not None and pr['exact_p'] < 0.05
        ex = f"{pr['exact_p']:.3f}" if pr['exact_p'] is not None else 'none discordant'
        print(f"   {d:16} before {D[d]['wins']['before']:3} next {D[d]['wins']['shipped']:3}  {pr['difference'] * 100:+5.1f} ({pr['ci95'][0] * 100:+.0f} to {pr['ci95'][1] * 100:+.0f})  only next {pr['cand_only']:2} only before {pr['base_only']:2}  exact {ex}  {'GOES BACK' if back else 'keeps'}")
    print()
    print('RULE 3. The mistakes, the seat under test, version before -> next version (beside what each part did by itself):')

    def sm(arm, key, ds=decks):
        return sum(D[d]['mistakes'][arm][key] for d in ds)

    def sa(arm, key, ds=decks):
        return sum(D[d]['aim'][arm].get(key, 0) for d in ds)

    for arm in ('before', 'shipped', 'guard'):
        print(f"   {arm:8} kill of the most dangerous of several missed {sm(arm, 'kill_top_missed')}/{sm(arm, 'kill_top_turns')} ({pct(sm(arm, 'kill_top_missed'), sm(arm, 'kill_top_turns'))}); "
              f"last {sm(arm, 'kill_last_missed')}/{sm(arm, 'kill_last_turns')} ({pct(sm(arm, 'kill_last_missed'), sm(arm, 'kill_last_turns'))}); "
              f"lesser {sm(arm, 'kill_lesser_missed')}/{sm(arm, 'kill_lesser_turns')} ({pct(sm(arm, 'kill_lesser_missed'), sm(arm, 'kill_lesser_turns'))})")
    print('            by itself (leader, #46): 12/266 (4.5%) from 38/279 (13.6%): -9.1 points; half of that is 4.6')
    for arm in ('before', 'shipped', 'guard'):
        print(f"   {arm:8} attackers at the most dangerous opponent, three alive {sa(arm, '3 at_top')}/{sa(arm, '3 attackers')} ({pct(sa(arm, '3 at_top'), sa(arm, '3 attackers'))}); two alive {sa(arm, '2 at_top')}/{sa(arm, '2 attackers')} ({pct(sa(arm, '2 at_top'), sa(arm, '2 attackers'))})")
    print('            by itself (swing, #47): 61.2% from 47.7%: +13.5 points; half of that is 6.8')
    op = [d for d in decks if d in OPEN]; nop = [d for d in decks if d not in OPEN]
    for arm in ('before', 'shipped', 'guard'):
        print(f"   {arm:8} an opponent who cannot block attacked: the {len(op)} decks with open {sm(arm, 'open_attacked', op)}/{sm(arm, 'open_turns', op)} ({pct(sm(arm, 'open_attacked', op), sm(arm, 'open_turns', op))}); "
              f"the {len(nop)} without {sm(arm, 'open_attacked', nop)}/{sm(arm, 'open_turns', nop)} ({pct(sm(arm, 'open_attacked', nop), sm(arm, 'open_turns', nop))})")
    print('            by itself (open, #49, ten decks): 62% from 30%: +32 points; half of that is 16')
    bl = [d for d in decks if d not in NO_BLOCK]; nbl = [d for d in decks if d in NO_BLOCK]
    for arm in ('before', 'shipped', 'guard'):
        print(f"   {arm:8} deaths on a turn a commander's damage reached 21: the {len(bl)} decks with block {sm(arm, 'commander_deaths', bl)} of {sm(arm, 'combat_deaths', bl)} deaths in combat; the {len(nbl)} without {sm(arm, 'commander_deaths', nbl)} of {sm(arm, 'combat_deaths', nbl)}; "
              f"block not made {sm(arm, 'block_not_made')}, tapped out {sm(arm, 'died_tapped_out')}, deaths in combat {sm(arm, 'combat_deaths')} (ten decks)")
    print('            by itself (block, #48, ten decks): 106 from 127: -21; half of that is about 10 (for eight decks about 8)')
    print()
    print('RULE 4. The guard (next version -> guard):')
    gco = sum(D[d]['pairs']['shipped:guard']['cand_only'] for d in decks)
    gbo = sum(D[d]['pairs']['shipped:guard']['base_only'] for d in decks)
    gp = exact(gco, gbo)
    ts, tg = sm('shipped', 'died_tapped_out'), sm('guard', 'died_tapped_out')
    print(f'   tables only the guard arm won {gco}, only the next version won {gbo}, exact test {gp:.4f} -> wins ' + ('hold' if gco >= gbo or gp > 0.05 else 'DO NOT hold'))
    print(f'   deaths tapped out: guard {tg}, next version {ts}; nine tenths of the next version\'s is {0.9 * ts:.1f} -> ' + ('holds' if tg <= 0.9 * ts else 'DOES NOT hold'))
    print('   -> the guard ' + ('HOLDS' if (gco >= gbo or gp > 0.05) and tg <= 0.9 * ts else 'DOES NOT HOLD'))
    for d in decks:
        pr = D[d]['pairs']['shipped:guard']
        ex = f"{pr['exact_p']:.3f}" if pr['exact_p'] is not None else 'none discordant'
        behind = pr['cand_only'] < pr['base_only'] and pr['exact_p'] is not None and pr['exact_p'] < 0.05
        m, g = D[d]['mistakes']['shipped'], D[d]['mistakes']['guard']
        print(f"   {d:16} next {D[d]['wins']['shipped']:3} guard {D[d]['wins']['guard']:3}  only guard {pr['cand_only']:2} only next {pr['base_only']:2}  exact {ex}  tapped out {m['died_tapped_out']:3} -> {g['died_tapped_out']:3}  attacked {pct(m['turns_attacked'], m['turns_able'], 0)} -> {pct(g['turns_attacked'], g['turns_able'], 0)}  {'guard arm BEHIND' if behind else ''}")
    print()
    print('RULE 5. Reported whatever it says:')
    j46 = argv[1] if len(argv) > 1 else None
    for d in decks:
        w46 = ''
        if j46 and os.path.exists(os.path.join(j46, d + '-join.json')):
            a = json.load(open(os.path.join(j46, d + '-join.json')))['arm_stats']
            w46 = f"   in #46 (other tables, other opponents): version before {a['shipped']['wins']}"
        print(f"   {d:16} next version {D[d]['wins']['shipped']:3} of {D[d]['games']['shipped']}, before {D[d]['wins']['before']:3}, guard {D[d]['wins']['guard']:3}{w46}")
    for arm in ('before', 'shipped', 'guard'):
        print(f"   {arm:8} attacked on {pct(sm(arm, 'turns_attacked'), sm(arm, 'turns_able'))} of the turns with an able attacker, sent {pct(sm(arm, 'power_sent'), sm(arm, 'power_able'))} of the damage it could")
    for arm in ('before', 'shipped', 'guard'):
        h = j['hook'][arm]
        print(f"   {arm:8} counters: " + ', '.join(f'{k} {v}' for k, v in sorted(h.items())))
    for pair in ('before:shipped', 'shipped:guard'):
        fd = j['pairs'][pair]['first_difference']
        print(f'   first difference, {pair}:')
        for k, v in fd.items():
            print(f'      {k:18} {json.dumps(v)[:300]}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
