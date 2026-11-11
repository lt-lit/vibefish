#!/usr/bin/env python3
"""How the deck under test played the table and how it lost, per arm of an A/B run, from the JSONL event logs.
Read-only; prints text.

  runner/losses.py RUN_DIR [--json OUT.json] [--top 10]

RUN_DIR is an ab.py run (ab.json, arm-*/g*/run.json with games/*.events.jsonl[.gz]: the shard artifacts of ab-run
unzipped into one directory). For the seat of the deck under test, in every arm:

  the table      wins, game length, the winner's own turns
  the losses     whether the seat was the first, second or third out; the game turn it lost on
  its last turn  life, lands and permanents at the start of its last own turn, the nonland cards still in hand and
                 how many of them its lands would have paid for (mana value against lands in play, as hands.py)
  the last blow  damage taken from the start of that turn until it lost, and the share one opponent dealt
  interaction    spells a game that target an opponent or an opponent's card, attackers sent at the seat, the
                 share of them it blocked, its own creatures that died on its own turns
  mulligans      games in which the seat took one

This is the other half of hands.py and playstyle.py: those say whether the seat runs its deck, this says what the
seat does about the other three. A card counts as an opponent's when it is in an opponent's list and not in ours;
tokens and cards both sides play are not counted, so "interaction" is a floor."""
import argparse, collections, glob, gzip, json, os, statistics as st, sys


def events(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def mean(xs, nd=2):
    xs = [x for x in xs if x is not None]
    return round(st.fmean(xs), nd) if xs else None


def share(k, n, nd=3):
    return round(k / n, nd) if n else None


def profile(rd):
    ab = json.load(open(os.path.join(rd, 'ab.json')))
    focus_id = ab['deck']
    arms = {}
    for arm_dir in sorted(glob.glob(os.path.join(rd, 'arm-*'))):
        S = collections.defaultdict(list); C = collections.Counter()
        held = collections.Counter(); castable_held = collections.Counter(); aimed = collections.Counter()
        for gd in sorted(glob.glob(os.path.join(arm_dir, 'g*'))):
            rj = os.path.join(gd, 'run.json')
            if not os.path.exists(rj):
                continue
            run = json.load(open(rj))
            focus = next(d['seat'] for d in run['decks'] if d['id'] == focus_id)
            own = {c['name']: c for d in run['decks'] if d['seat'] == focus for c in d['cards']}
            theirs = {c['name'] for d in run['decks'] if d['seat'] != focus for c in d['cards']} - set(own)
            for g in run['games']:
                evf = os.path.join(gd, 'games', os.path.basename(g['events']))
                if not os.path.exists(evf):
                    evf += '.gz'
                    if not os.path.exists(evf):
                        continue
                me = next(p for p in g['players'] if p['seat'] == focus)
                C['games'] += 1; C['wins'] += bool(me.get('won')); C['draws'] += g.get('winner') is None
                C['mulligan_games'] += bool(me.get('mulligans'))
                S['game_turns'].append(g['turns'])
                S['winner_own_turns'].append(next((p['turns_played'] for p in g['players'] if p.get('won')), None))
                cur = None; last_src = {}; my_turn = None; my_turn_t = None; taken = []
                n = collections.Counter()
                for e in events(evf):
                    k = e['e']
                    if k == 'turn':
                        cur = e['seat']
                        if cur == focus:
                            my_turn = next(x for x in e['state'] if x['seat'] == focus); my_turn_t = e['t']
                    elif k == 'cast' and e.get('seat') == focus and e.get('spell') and not (e.get('copy') or e.get('from') is None):
                        n['spells'] += 1
                        if [s for s in (e.get('target_seats') or []) if s != focus] or any(t in theirs for t in (e.get('targets') or [])):
                            n['aimed'] += 1; aimed[e['card']] += 1
                    elif k == 'attack' and e['seat'] != focus:
                        n['attackers_at_seat'] += sum(1 for a in e['attacks'] if a.get('defender_seat') == focus)
                    elif k == 'block' and e.get('seat') == focus:
                        n['blocked'] += sum(1 for b in e.get('blocks') or [] if b.get('blockers'))
                    elif (k == 'zone' and e.get('seat') == focus and cur == focus and e.get('from') == 'Battlefield'
                          and e.get('to') in ('Graveyard', 'Exile')):
                        n['own_turn_deaths'] += 1
                    elif k == 'damage':
                        if e.get('source_seat') == focus and e['seat'] != focus:
                            n['dealt'] += e['amount']
                        if e['seat'] == focus:
                            n['taken'] += e['amount']; taken.append((e['t'], e.get('source_seat'), e['amount']))
                        last_src[e['seat']] = e.get('source_seat')
                    elif k == 'lost':
                        if e['seat'] != focus and last_src.get(e['seat']) == focus:
                            n['kills'] += 1
                        if e['seat'] == focus:
                            C['losses'] += 1
                            C['out_%d' % (1 + sum(1 for p in g['players'] if p['seat'] != focus
                                                  and p.get('turn_lost') is not None and p['turn_lost'] < e['t']))] += 1
                            S['lost_turn'].append(e['t']); S['lost_own_turn'].append(me.get('turns_played'))
                            ms = my_turn or {}
                            lands = ms.get('lands') or 0
                            hand = [c for c in (ms.get('hand') or []) if not own.get(c, {}).get('land')]
                            can = [c for c in hand if (own.get(c, {}).get('cmc') or 0) <= lands]
                            S['hand'].append(len(hand)); S['castable'].append(len(can)); S['lands'].append(lands)
                            S['permanents'].append(ms.get('bf')); S['life'].append(ms.get('life'))
                            held.update(hand); castable_held.update(can)
                            by = collections.Counter()
                            for t, src, amt in taken:
                                if my_turn_t is not None and t >= my_turn_t and src is not None and src != focus:
                                    by[src] += amt
                            if by:
                                S['last_blow'].append(sum(by.values())); S['last_blow_top'].append(max(by.values()) / sum(by.values()))
                for key in ('spells', 'aimed', 'attackers_at_seat', 'blocked', 'own_turn_deaths', 'dealt', 'taken', 'kills'):
                    S[key].append(n[key])
        games = C['games']; losses = C['losses']
        arms[os.path.basename(arm_dir)[4:]] = {
            'games': games, 'wins': C['wins'], 'draws': C['draws'], 'losses': losses,
            'game_turns': mean(S['game_turns']), 'winner_own_turns': mean(S['winner_own_turns']),
            'out_first': C['out_1'], 'out_second': C['out_2'], 'out_third': C['out_3'],
            'lost_on_game_turn': mean(S['lost_turn']), 'lost_on_own_turn': mean(S['lost_own_turn']),
            'last_turn': {'life': mean(S['life']), 'lands': mean(S['lands']), 'permanents': mean(S['permanents']),
                          'nonland_cards_in_hand': mean(S['hand']), 'of_them_castable': mean(S['castable']),
                          'losses_with_a_castable_card': share(sum(1 for x in S['castable'] if x), len(S['castable']))},
            'last_blow': {'damage': mean(S['last_blow']), 'top_opponent_share': mean(S['last_blow_top']),
                          'one_opponent_did_80pct': share(sum(1 for x in S['last_blow_top'] if x >= 0.8), len(S['last_blow_top']))},
            'per_game': {'spells': mean(S['spells']), 'spells_aimed_at_opponents': mean(S['aimed']),
                         'attackers_at_seat': mean(S['attackers_at_seat']), 'own_creatures_lost_on_own_turns': mean(S['own_turn_deaths']),
                         'damage_dealt': mean(S['dealt']), 'damage_taken': mean(S['taken']), 'opponents_killed': mean(S['kills'])},
            'blocked_share': share(sum(S['blocked']), sum(S['attackers_at_seat'])),
            'games_with_a_mulligan': share(C['mulligan_games'], games),
            'held_castable': castable_held.most_common(), 'held': held.most_common(), 'aimed_spells': aimed.most_common(),
        }
    return {'kind': 'ab-losses', 'deck': focus_id, 'seed': ab.get('seed'), 'opponents': ab.get('opponents', 3),
            'forge_version': ab.get('forge_version'), 'arms': arms}


def text(res, top):
    arms = list(res['arms'])
    out = [f"{res['deck']} (seed {res['seed']}, {res['forge_version']}): the seat under test, by arm"]
    rows = [
        ('wins / games (draws)', lambda a: f"{a['wins']} / {a['games']} ({a['draws']})"),
        ('game turns; the winner\'s own turns', lambda a: f"{a['game_turns']}; {a['winner_own_turns']}"),
        ('losses: out first / second / third', lambda a: f"{a['out_first']} / {a['out_second']} / {a['out_third']} of {a['losses']}"),
        ('lost on game turn (own turn)', lambda a: f"{a['lost_on_game_turn']} ({a['lost_on_own_turn']})"),
        ('last own turn: life, lands, permanents', lambda a: f"{a['last_turn']['life']}, {a['last_turn']['lands']}, {a['last_turn']['permanents']}"),
        ('  nonland cards in hand, castable', lambda a: f"{a['last_turn']['nonland_cards_in_hand']}, {a['last_turn']['of_them_castable']}"),
        ('  losses holding a castable card', lambda a: pct(a['last_turn']['losses_with_a_castable_card'])),
        ('last blow: damage, one opponent\'s share', lambda a: f"{a['last_blow']['damage']}, {pct(a['last_blow']['top_opponent_share'])}"),
        ('  losses where one opponent did 80%+', lambda a: pct(a['last_blow']['one_opponent_did_80pct'])),
        ('a game: spells, aimed at opponents', lambda a: f"{a['per_game']['spells']}, {a['per_game']['spells_aimed_at_opponents']}"),
        ('  attackers at the seat, share blocked', lambda a: f"{a['per_game']['attackers_at_seat']}, {pct(a['blocked_share'])}"),
        ('  own creatures lost on own turns', lambda a: f"{a['per_game']['own_creatures_lost_on_own_turns']}"),
        ('  damage dealt / taken, opponents killed', lambda a: f"{a['per_game']['damage_dealt']} / {a['per_game']['damage_taken']}, {a['per_game']['opponents_killed']}"),
        ('games with a mulligan', lambda a: pct(a['games_with_a_mulligan'])),
    ]
    out.append(f"  {'':42s}" + ''.join(f"{n:>26s}" for n in arms))
    for label, f in rows:
        out.append(f"  {label:42s}" + ''.join(f"{f(res['arms'][n]):>26s}" for n in arms))
    for n in arms:
        a = res['arms'][n]
        out.append(f"\n  {n}: castable cards in hand on the last own turn of a loss (losses): "
                   + ', '.join(f"{c} {k}" for c, k in a['held_castable'][:top]))
        out.append(f"  {n}: spells aimed at opponents (casts over all games): " + ', '.join(f"{c} {k}" for c, k in a['aimed_spells'][:top]))
    return '\n'.join(out)


def pct(x):
    return 'n/a' if x is None else f"{100 * x:.0f}%"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dir')
    ap.add_argument('--json', help='also write the numbers here (kind "ab-losses")')
    ap.add_argument('--top', type=int, default=10, help='cards listed per arm')
    args = ap.parse_args(argv)
    if not os.path.exists(os.path.join(args.run_dir, 'ab.json')):
        sys.exit(f"losses.py: {args.run_dir} is not an ab.py run (no ab.json)")
    res = profile(args.run_dir)
    if not any(a['games'] for a in res['arms'].values()):
        sys.exit("losses.py: no finished games with event logs found")
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(res, f, indent=1)
            f.write('\n')
    print(text(res, args.top))


if __name__ == '__main__':
    main(sys.argv[1:])
