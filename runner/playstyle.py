#!/usr/bin/env python3
"""How the bots play after the mulligan, read from the JSONL event logs of finished runs:
attack targeting, combat tempo, mana use and closing speed. Read-only; prints a text report.

Usage: runner/playstyle.py RESULTS_DIR... [--by-profile]
  RESULTS_DIR   a run dir holding shard-*/run.json and shard-*/games/*.events.jsonl,
                or an ab.py run (ab.json, arm-*/g*/run.json): seats are then labelled
                <arm>/focus (the deck under test) and <arm>/opps (its stock opponents)
  --by-profile  label seats by their AI profile name instead of the arm labels
                heuristic / mc-on / mc-max (Vibefish-MC* profiles count as Monte Carlo)

Mana use is approximate: mana value of spells cast on the seat's own turn over lands in play,
abilities and X not counted. Block events before harness 0.1.1 overstate blocking (DESIGN.md §6)
and are not used here."""
import argparse, json, sys, glob, os, collections, statistics as st

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('runs', nargs='+', metavar='RESULTS_DIR')
ap.add_argument('--by-profile', action='store_true')
ARGS = ap.parse_args()

def arm_of(profile, run_id):
    if ARGS.by_profile:
        return profile or 'Default'
    if profile in ('Vibefish-MC', 'Vibefish-MCHard'):
        return 'mc-max' if 'mcmax' in run_id else 'mc-on'
    return 'heuristic'

A = collections.defaultdict(lambda: collections.Counter())   # attack targeting per arm
T = collections.defaultdict(lambda: collections.defaultdict(list))  # mana use per arm per bucket
IDLE = collections.defaultdict(lambda: collections.Counter())
RECV = collections.Counter(); EXPO = collections.Counter()    # attackers received per deck, exposure (opponent turns alive)
CLOSE = collections.defaultdict(list); DMG = collections.Counter(); KILL = collections.Counter()
LINGER = collections.defaultdict(list)
SPLIT = collections.defaultdict(lambda: collections.Counter())
TEMPO = collections.defaultdict(lambda: collections.Counter())
BLK = collections.Counter()
games = 0

def bucket(ot): return 'T1-4' if ot <= 4 else 'T5-8' if ot <= 8 else 'T9-12' if ot <= 12 else 'T13+'

def run_dirs(rd):
    """(directory holding run.json, A/B arm or None): shard-* of a pod or league run, arm-*/g* of an ab.py run."""
    out = [(d, None) for d in sorted(glob.glob(os.path.join(rd, 'shard-*'))) if os.path.isdir(d)]
    for arm in sorted(glob.glob(os.path.join(rd, 'arm-*'))):
        out += [(d, os.path.basename(arm)[4:]) for d in sorted(glob.glob(os.path.join(arm, 'g*'))) if os.path.isdir(d)]
    return out

for rd in ARGS.runs:
    run_id = os.path.basename(rd.rstrip('/'))
    focus = json.load(open(os.path.join(rd, 'ab.json'))).get('deck') if os.path.exists(os.path.join(rd, 'ab.json')) else None
    for shard, ab_arm in run_dirs(rd):
        if not os.path.exists(os.path.join(shard, 'run.json')): continue
        run = json.load(open(os.path.join(shard, 'run.json')))
        cmc = {}; cmdrs = {}
        deck_id = {d['seat']: d['id'] for d in run['decks']}
        def label(s):   # A/B runs: the arm, split into the deck under test and its three stock opponents
            if ab_arm and not ARGS.by_profile:
                return f"{ab_arm}/{'focus' if deck_id[s] == focus else 'opps'}"
            return arm_of(prof[s], run_id)
        def rkey(s):    # per-deck tables collapse to the same split in A/B runs
            return label(s) if ab_arm and not ARGS.by_profile else deck_id[s]
        for d in run['decks']:
            for c in d['cards']: cmc[c['name']] = c.get('cmc', 0)
            cmdrs[d['seat']] = set(d['commanders'])
        for g in run['games']:
            evf = os.path.join(shard, 'games', os.path.basename(g['events'])) if g.get('events') else None
            if not evf or not os.path.exists(evf): continue
            games += 1
            prof = g.get('profiles') or [pl.get('profile') or 'Default' for pl in sorted(g['players'], key=lambda x: x['seat'])]; winner = next((p['seat'] for p in g['players'] if p['won']), None)
            state = None; cur = None; pending_block = False; spent = 0; lands = 0; hand = 0; ncmd = collections.Counter()
            lost_t = {}; last_dmg_src = {}; end_t = 0; low_turns = collections.Counter(); turn_att = {'n': 0, 'dmg': 0}
            def flush():
                if cur is None: return
                s, ot = cur
                arm0 = label(s); TEMPO[arm0][bucket(ot)+' turns'] += 1
                TEMPO[arm0][bucket(ot)+' attacked'] += 1 if turn_att['n'] else 0
                TEMPO[arm0][bucket(ot)+' attackers'] += turn_att['n']; TEMPO[arm0][bucket(ot)+' dmg'] += turn_att['dmg']
                if ot >= 4 and lands >= 3:
                    arm = label(s)
                    T[arm][bucket(ot)].append(min(spent / lands, 1.5))
                    IDLE[arm][bucket(ot) + ' turns'] += 1
                    if spent == 0 and hand >= 3: IDLE[arm][bucket(ot) + ' idle'] += 1
            for line in open(evf):
                e = json.loads(line); et = e['e']; end_t = max(end_t, e.get('t', 0))
                if et == 'turn':
                    flush()
                    state = {x['seat']: x for x in e['state']}
                    s = e['seat']; cur = (s, e['own_turn']); spent = 0; turn_att = {'n': 0, 'dmg': 0}
                    lands = state[s]['lands']; hand = len(state[s].get('hand') or [])
                    if state[s]['life'] <= 10: low_turns[s] += 1
                    for o, x in state.items():
                        if o != s and x['alive']: EXPO[rkey(o)] += 1
                elif et == 'cast' and e.get('spell') and not (e.get('copy') or e.get('from') is None):   # copies cost no mana
                    s = e['seat']
                    if cur and s == cur[0]:
                        c = cmc.get(e['card'], 0)
                        if e.get('commander'):
                            c += 2 * ncmd[s]; ncmd[s] += 1
                        spent += c
                elif et == 'attack' and state:
                    s = e['seat']; arm = label(s)
                    opp = {o: x for o, x in state.items() if o != s and x['alive']}
                    by = collections.Counter(a['defender_seat'] for a in e['attacks'] if a.get('defender_seat') is not None)
                    turn_att['n'] += sum(by.values())
                    if not by or len(opp) < 2: continue
                    n = sum(by.values()); A[arm]['declarations'] += 1; A[arm]['attackers'] += n
                    weakest = min(opp, key=lambda o: opp[o]['life']); leader = max(opp, key=lambda o: opp[o]['bf'])
                    lifes = sorted(x['life'] for x in opp.values()); bfs = sorted(x['bf'] for x in opp.values())
                    if weakest != leader and lifes[0] != lifes[1] and bfs[-1] != bfs[-2]:
                        SPLIT[arm]['n'] += n; SPLIT[arm]['weakest'] += by.get(weakest, 0); SPLIT[arm]['leader'] += by.get(leader, 0)
                    if len(by) == 1: A[arm]['single_target'] += 1
                    for d, k in by.items(): RECV[rkey(d)] += k
                    def uniq(key, rev):
                        vals = sorted(((x[key], o) for o, x in opp.items()), reverse=rev)
                        return vals[0][1] if vals[0][0] != vals[1][0] else None
                    for name, key, rev in (('lowest_life', 'life', False), ('highest_life', 'life', True), ('biggest_board', 'bf', True), ('smallest_board', 'bf', False)):
                        tgt = uniq(key, rev)
                        if tgt is not None:
                            A[arm][name + '_n'] += n; A[arm][name] += by.get(tgt, 0)
                elif et == 'block':
                    if pending_block and e.get('blocks'): BLK['blocked'] += 1; pending_block = False
                elif et == 'damage':
                    DMG['total'] += e['amount']
                    if e.get('combat') and cur and e.get('source_seat') == cur[0]: turn_att['dmg'] += e['amount']
                    if e.get('combat'): DMG['combat'] += e['amount']
                    if e.get('source_commander'): DMG['commander'] += e['amount']
                    last_dmg_src[e['seat']] = e.get('source_seat')
                elif et == 'lost':
                    lost_t[e['seat']] = e['t']
                    src = last_dmg_src.get(e['seat'])
                    if e.get('reason') == 'LifeReachedZero' and src is not None:
                        KILL['kills'] += 1
                        if src == winner: KILL['by_winner'] += 1
                        if src == e['seat']: KILL['self'] += 1
                    LINGER[rkey(e['seat'])].append(low_turns[e['seat']])
            flush()
            if lost_t:
                CLOSE['first_loss_t'].append(min(lost_t.values())); CLOSE['end_t'].append(end_t)
                CLOSE['first_to_end'].append(end_t - min(lost_t.values()))

print(f"games: {games}")
if not games: sys.exit("no finished games found")
print("\nATTACK TARGETING (share of attacking creatures sent at the unique opponent who is ...; ties skipped)")
for arm, c in sorted(A.items()):
    row = [f"{arm:18s} decl {c['declarations']:5d}  single-target {c['single_target']/c['declarations']:.0%}"]
    for k in ('lowest_life', 'highest_life', 'biggest_board', 'smallest_board'):
        row.append(f"{k} {c[k]/c[k+'_n']:.0%}" if c[k+'_n'] else f"{k} n/a")
    print('  ' + '  '.join(row))
print("  when the lowest-life opponent and the biggest-board opponent are different players:")
for arm, c in sorted(SPLIT.items()):
    print(f"    {arm:18s} attackers at weakest {c['weakest']/c['n']:.0%}, at leader {c['leader']/c['n']:.0%}, at the third {1-(c['weakest']+c['leader'])/c['n']:.0%}  (n={c['n']})")
print("\nCOMBAT TEMPO per own turn: share of turns with an attack / mean attackers / mean combat damage to players")
for arm, c in sorted(TEMPO.items()):
    print('  ' + f"{arm:18s} " + '  '.join(f"{b} {c[b+' attacked']/c[b+' turns']:.0%} / {c[b+' attackers']/c[b+' turns']:.1f} / {c[b+' dmg']/c[b+' turns']:.1f}" for b in ('T1-4','T5-8','T9-12','T13+') if c[b+' turns']))
print("\nATTACKERS RECEIVED per 100 opponent-turns alive, by deck")
for d in sorted(EXPO): print(f"  {d:16s} {100*RECV[d]/EXPO[d]:5.1f}")
print("\nMANA USE: mean (cmc cast on own turn / lands), own turns >= 4 with >= 3 lands, 0-cost and abilities not counted")
for arm, b in sorted(T.items()):
    print('  ' + f"{arm:18s} " + '  '.join(f"{k} {st.mean(v):.2f} (n={len(v)})" for k, v in sorted(b.items())))
print("\nIDLE TURNS: own turn with >= 3 lands, >= 3 cards in hand, no spell cast")
for arm, c in sorted(IDLE.items()):
    print('  ' + f"{arm:18s} " + '  '.join(f"{k.split()[0]} {c[k.split()[0]+' idle']/c[k]:.0%}" for k in sorted(c) if k.endswith('turns')))
print("\nCLOSING")
print(f"  first elimination at player-turn {st.mean(CLOSE['first_loss_t']):.1f} (median {st.median(CLOSE['first_loss_t']):.0f}); game ends at {st.mean(CLOSE['end_t']):.1f}; first elimination -> end {st.mean(CLOSE['first_to_end']):.1f} player-turns")
print(f"  player damage: combat {DMG['combat']/DMG['total']:.0%}, commander {DMG['commander']/DMG['total']:.0%}")
print(f"  life-zero eliminations {KILL['kills']}: dealt by the eventual winner {KILL['by_winner']/KILL['kills']:.0%}, self-inflicted {KILL['self']/KILL['kills']:.0%}")
print("  own turns spent at <= 10 life before dying, by deck: " + ', '.join(f"{d} {st.mean(v):.1f}" for d, v in sorted(LINGER.items())))
