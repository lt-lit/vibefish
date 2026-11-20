#!/usr/bin/env python3
"""tapped_out.py RUN_DIR...: the deaths tapped out (`runner/mistakes.py`), by what the seat did on its own turn before. A session helper.

Whether the seat attacked on its last turn before the death, with how many creatures, with everything that could attack, whether that attack took an
opponent out, and whether the player who then killed it was one it had attacked or another. Also every attack and every turn without one: how often the seat was then left where one opponent alone was sure to kill it before its own
next turn (its row of that opponent's `combat` line, harness 0.4.0 or later), and how often it then went out before that turn."""
import collections, glob, gzip, json, os, sys
C = collections.Counter()
natt = collections.Counter()
for root in sys.argv[1:]:
    for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
        run = json.load(open(rj))
        g = run['games'][0]
        evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
        if not os.path.exists(evf):
            evf += '.gz'
        op = gzip.open if evf.endswith('.gz') else open
        with op(evf, 'rt', encoding='utf-8') as f:
            evs = [json.loads(l) for l in f if l.strip()]
        winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
        lost_at = {e['seat']: e['t'] for e in evs if e['e'] == 'lost'}
        turn_seat = {e['t']: e['seat'] for e in evs if e['e'] == 'turn'}
        own_turns = collections.defaultdict(list)
        for t, s in sorted(turn_seat.items()):
            own_turns[s].append(t)
        attacks = collections.defaultdict(int)          # (seat, t) -> attackers declared at players
        aimed = collections.defaultdict(set)            # (seat, t) -> the seats it attacked
        for e in evs:
            if e['e'] == 'attack':
                attacks[(e['seat'], e['t'])] += sum(1 for a in e.get('attacks') or [] if a.get('defender_seat') is not None)
                aimed[(e['seat'], e['t'])].update(a['defender_seat'] for a in e.get('attacks') or [] if a.get('defender_seat') is not None)
        killed_on = collections.defaultdict(list)       # t -> seats that lost
        for s, t in lost_at.items():
            killed_on[t].append(s)
        able = {}
        for e in evs:
            if e['e'] == 'combat':
                able[(e['seat'], e['t'])] = len(e.get('able') or [])
        # deaths tapped out
        for e in evs:
            if e['e'] != 'block' or 'incoming' not in e:
                continue
            d = e['seat']
            if not (e['incoming'] >= e['life'] > 0 and lost_at.get(d) == e['t']):
                continue
            C['combat_deaths'] += 1
            if e['best'] < e['life']:
                continue
            if e.get('best_untapped', e['best']) >= e['life']:
                continue
            C['tapped_out'] += 1
            prev = [t for t in own_turns[d] if t < e['t']]
            if not prev:
                C['to_no_own_turn'] += 1
                continue
            p = prev[-1]
            n = attacks.get((d, p), 0)
            if n == 0:
                C['to_did_not_attack'] += 1
            else:
                C['to_attacked'] += 1
                natt[min(n, 8)] += 1
                took = [s for s in killed_on.get(p, []) if s != d]
                killer = turn_seat.get(e['t'])
                C['to_attacked_killed_by_a_player_it_had_attacked' if killer in aimed[(d, p)] else 'to_attacked_killed_by_another_player'] += 1
                C['to_attacked_and_took_a_player_out' if took else 'to_attacked_took_nobody_out'] += 1
                if n >= able.get((d, p), n):
                    C['to_attacked_with_everything_able'] += 1
        # every attack: exposure after
        for (s, t), n in attacks.items():
            if n == 0:
                continue
            nxt = next((x for x in own_turns[s] if x > t), None)
            exposed = False
            for e in evs:
                if e['e'] == 'combat' and e['t'] > t and (nxt is None or e['t'] < nxt) and e['seat'] != s:
                    for dd in e.get('defenders') or []:
                        if dd['seat'] == s and dd['life'] > 0 and dd['through'] >= dd['life']:
                            exposed = True
            C['attacks'] += 1
            dead = s in lost_at and lost_at[s] > t and (nxt is None or lost_at[s] < nxt)
            if exposed:
                C['attacks_then_exposed'] += 1
                C['attacks_then_exposed_dead'] += dead
            else:
                C['attacks_not_exposed_dead'] += dead
        # turns without an attack: exposure after
        for s, ts in own_turns.items():
            for t in ts:
                if attacks.get((s, t), 0):
                    continue
                if s in lost_at and lost_at[s] <= t:
                    continue
                nxt = next((x for x in own_turns[s] if x > t), None)
                exposed = False
                for e in evs:
                    if e['e'] == 'combat' and e['t'] > t and (nxt is None or e['t'] < nxt) and e['seat'] != s:
                        for dd in e.get('defenders') or []:
                            if dd['seat'] == s and dd['life'] > 0 and dd['through'] >= dd['life']:
                                exposed = True
                C['no_attack_turns'] += 1
                dead = s in lost_at and lost_at[s] > t and (nxt is None or lost_at[s] < nxt)
                if exposed:
                    C['no_attack_then_exposed'] += 1
                    C['no_attack_then_exposed_dead'] += dead
for k in sorted(C):
    print(f"{k:42} {C[k]}")
print('attackers on the turn before a death tapped out (8 = eight or more):', sorted(natt.items()))
