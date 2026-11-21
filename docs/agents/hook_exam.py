#!/usr/bin/env python3
"""hook_exam.py EXAM_RESULTS_DIR ROLLUPS_DIR OUT_DIR --pair BASE:CAND [--pair ...] DECK...: an exam of attack hooks, read. A session helper.

EXAM_RESULTS_DIR holds the run directories `shards.sh` makes (ab-DECK, ab-DECK@VARIANT), ROLLUPS_DIR what `exam_summary.py --out`
wrote (DECK-join.json with the arms `shipped` and each variant, DECK-VARIANT.json). For every pair of arms named (`shipped:leader`,
`leader:leaderguard`, ...), deck by deck and over all the decks together:

  wins          each arm's wins and the pair's discordant tables with the exact test (from the join)
  mistakes      the seat under test's counts in each arm (`runner/mistakes.py --deck`): sure kills missed by where the table stood,
                deaths in combat, by a block not made, tapped out
  the hook      its own counters for the seat (`playbook_focus` of the candidate's rollup)
  its tables    `first_difference.py` on the pair: the tables on which the seat's own attack declaration is the first thing that
                differs, how those pairs ended, and from the same position how often the seat was out before its next turn

Everything is written to OUT_DIR (`hook-exam.json`, the mistakes of each arm, `first-difference-BASE-CAND.json`). It prints what a
rule needs and decides nothing: the rule an exam is read by is in CLAUDE.md, In flight, fixed before the run.
"""
import argparse, collections, json, math, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MK = ('kill_turns', 'kill_missed', 'kill_last_turns', 'kill_last_missed', 'kill_top_turns', 'kill_top_missed', 'kill_lesser_turns', 'kill_lesser_missed',
      'attacked_lethal', 'combat_deaths', 'block_not_made', 'died_tapped_out', 'turns_able', 'turns_attacked')


def exact(a, b):
    n = a + b
    if not n:
        return 1.0
    pr = [math.comb(n, k) / 2 ** n for k in range(n + 1)]
    return min(1.0, sum(q for q in pr if q <= pr[a] * (1 + 1e-9)))


def entry(deck, arm):
    return deck if arm == 'shipped' else f'{deck}@{arm}'


def mistakes(exam, out, deck, arm):
    p = os.path.join(out, f'{deck}-{arm}-mistakes.json')
    subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'runner', 'mistakes.py'), os.path.join(exam, 'results', 'ab-' + entry(deck, arm)),
                    '--deck', deck, '--json', p], capture_output=True, text=True, check=True)
    j = json.load(open(p))
    j['kills_not_taken'] = j['kills_not_taken'][:20]
    json.dump(j, open(p, 'w'), indent=1)
    return j['groups'].get('bot') or {}


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exam')
    ap.add_argument('rollups')
    ap.add_argument('out')
    ap.add_argument('decks', nargs='+')
    ap.add_argument('--pair', action='append', required=True, help='BASE:CAND, arms as the join names them (shipped, or a variant)')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    pairs = [tuple(x.split(':')) for x in a.pair]
    arms = []
    for b, c in pairs:
        arms += [x for x in (b, c) if x not in arms]
    res = {'decks': {}, 'pairs': {}, 'arms': arms}
    M = {arm: collections.Counter() for arm in arms}
    H = {arm: collections.Counter() for arm in arms}
    W = {arm: 0 for arm in arms}
    for d in a.decks:
        j = json.load(open(os.path.join(a.rollups, f'{d}-join.json')))
        row = {'wins': {}, 'games': {}, 'mistakes': {}, 'hook': {}, 'pairs': {}}
        for arm in arms:
            st = j['arm_stats'][arm]
            row['wins'][arm], row['games'][arm] = st['wins'], st['games']
            W[arm] += st['wins']
            m = mistakes(a.exam, a.out, d, arm)
            row['mistakes'][arm] = {k: m.get(k, 0) for k in MK}
            M[arm].update(row['mistakes'][arm])
            if arm != 'shipped':
                foc = json.load(open(os.path.join(a.rollups, f'{d}-{arm}.json')))['arm_stats']['playbook'].get('playbook_focus') or {}
                row['hook'][arm] = {k: v for k, v in foc.items() if k.startswith(('attack_kill', 'attack_guard'))}
                H[arm].update(row['hook'][arm])
        for b, c in pairs:
            p = j['paired'][f'{c}_vs_{b}']
            row['pairs'][f'{b}:{c}'] = {'cand_only': p[f'{c}_only'], 'base_only': p[f'{b}_only'], 'difference': p['difference'], 'ci95': p['difference_ci95'], 'exact_p': p['exact_p']}
        res['decks'][d] = row
        print(f"{d}: wins " + ', '.join(f"{arm} {row['wins'][arm]} of {row['games'][arm]}" for arm in arms))
        for b, c in pairs:
            p = row['pairs'][f'{b}:{c}']
            print(f"    {c} on {b}: {p['difference'] * 100:+.1f} ({p['ci95'][0] * 100:+.0f} to {p['ci95'][1] * 100:+.0f}), only {c} {p['cand_only']}, only {b} {p['base_only']}, exact {p['exact_p']:.2f}"
                  f"   {'behind by more than two tables' if row['wins'][c] < row['wins'][b] - 2 else 'level or ahead (within two tables)'}")
        for arm in arms:
            m = row['mistakes'][arm]
            print(f"    {arm:11} sure kills missed: last {m['kill_last_missed']}/{m['kill_last_turns']}, most dangerous {m['kill_top_missed']}/{m['kill_top_turns']}, "
                  f"lesser {m['kill_lesser_missed']}/{m['kill_lesser_turns']} | deaths in combat {m['combat_deaths']}, block not made {m['block_not_made']}, tapped out {m['died_tapped_out']}"
                  + (f" | hook {row['hook'][arm]}" if arm != 'shipped' else ''))
    print()
    print(f"ALL {len(a.decks)} DECKS: wins " + ', '.join(f'{arm} {W[arm]}' for arm in arms) + f" of {200 * len(a.decks)}")
    for arm in arms:
        m = M[arm]
        print(f"    {arm:11} sure kills missed: last {m['kill_last_missed']}/{m['kill_last_turns']} ({pct(m['kill_last_missed'], m['kill_last_turns'])}), "
              f"most dangerous {m['kill_top_missed']}/{m['kill_top_turns']} ({pct(m['kill_top_missed'], m['kill_top_turns'])}), "
              f"lesser {m['kill_lesser_missed']}/{m['kill_lesser_turns']} ({pct(m['kill_lesser_missed'], m['kill_lesser_turns'])}) | deaths in combat {m['combat_deaths']}, "
              f"block not made {m['block_not_made']}, tapped out {m['died_tapped_out']} | attacked on {pct(m['turns_attacked'], m['turns_able'])} of its turns with an able attacker"
              + (f" | hook {dict(H[arm])}" if arm != 'shipped' else ''))
    for b, c in pairs:
        co = sum(res['decks'][d]['pairs'][f'{b}:{c}']['cand_only'] for d in a.decks)
        bo = sum(res['decks'][d]['pairs'][f'{b}:{c}']['base_only'] for d in a.decks)
        fd = os.path.join(a.out, f'first-difference-{b}-{c}.json')
        cmd = [sys.executable, '-I', os.path.join(ROOT, 'docs', 'agents', 'first_difference.py'), os.path.join(a.exam, 'results'), c] + a.decks + ['--json', fd]
        if b != 'shipped':
            cmd += ['--base', b]
        txt = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        files = json.load(open(fd))['files']
        res['pairs'][f'{b}:{c}'] = {'cand_only': co, 'base_only': bo, 'exact_p': exact(co, bo), 'first_difference': files}
        print()
        print(f"{c} beside {b}, all decks: tables only {c} won {co}, only {b} won {bo}, exact test {exact(co, bo):.4f}")
        print(txt.rstrip())
    res['mistakes'] = {arm: dict(M[arm]) for arm in arms}
    res['hook'] = {arm: dict(H[arm]) for arm in arms}
    res['wins'] = W
    json.dump(res, open(os.path.join(a.out, 'hook-exam.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
