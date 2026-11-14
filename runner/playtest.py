#!/usr/bin/env python3
"""A playtest report for one deck: what the games of an ab.py run say about the deck in the focus seat.
Read-only; prints Markdown.

  runner/playtest.py RUN_DIR [RUN_DIR ...] [--arm ARM] [--goldfish GOLDFISH_DIR] [--min-drawn N]
                     [--md OUT.md] [--json OUT.json]

RUN_DIR is an ab.py run (ab.json, arm-*/g*/run.json): the deck under test in one seat of every table, its
opponents drawn from a pool, as `runner/ab.py play --deck ID [--deck-file LIST.dck] --pool ... --opponent-playbooks`
plays them. Several RUN_DIRs are the shards of one run (the same deck and seed; Actions' shard artifacts). --arm
picks the arm that is reported: the pilot of the deck (`stock` is Forge's AI, `playbook` the deck's playbook);
default `playbook` when the run has it. --goldfish adds the kill turns of a runner/goldfish.sh run of the same list.

What it reports, all of it for the focus seat:

  result     wins of the tables played, with a 95% Wilson interval, beside an even share (one in four); by seat;
             the place it finished in; what took it out
  opponents  per opposing deck: the tables it sat at, the focus deck's wins there, its own wins there, and how often
             it dealt the largest share of the damage of the focus seat's last turn cycle ("took it out")
  tempo      mulligans, lands and cards in hand at the start of its own turns 4, 6 and 8, the commander's first
             cast, spells a game, and idle turns: own turns from the third on with no spell cast although a nonland
             card in hand cost no more than the seat had lands (colours and mana rocks are not looked at, so this is
             a rough count in both directions)
  cards      per nonland card: games drawn (in hand at the start of a turn, or cast from hand), the share of those
             in which it was cast, the turn of the first cast, the deck's win rate in the games it was drawn beside
             its win rate in the games it was not, and how often it was still in hand when the seat lost

The per-card win rates are the noisiest figures here: a card drawn in half of 200 games leaves 100 games on each
side, and a difference under about fourteen points is inside the 95% interval of two such shares. They are sorted
to be looked at, not believed: a card that is cast in few of the games it is drawn, or sits in hand at the losses,
is the firmer finding. Who pilots the opponents is in the header: at a table of stock Forge AI nothing punishes a
slow or open deck, so read a result against the pilots it was earned against. Standard library only.
"""
import argparse
import collections
import glob
import gzip
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import rollup as rl          # noqa: E402  (wilson)

OWN_TURNS = (4, 6, 8)


def events(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def quartile(xs, p):
    xs = sorted(xs)
    return xs[int(p * (len(xs) - 1))] if xs else None


def mean(xs, nd=2):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), nd) if xs else None


def share(k, n, nd=3):
    return round(k / n, nd) if n else None


def collect(run_dirs, arm=None):
    metas = [json.load(open(os.path.join(rd, 'ab.json'), encoding='utf-8')) for rd in run_dirs]
    m0 = metas[0]
    for rd, m in zip(run_dirs[1:], metas[1:]):
        if (m['deck'], m['seed'], m.get('pool'), m.get('deck_file_sha256')) != (m0['deck'], m0['seed'], m0.get('pool'), m0.get('deck_file_sha256')):
            raise SystemExit(f"{rd}: deck {m['deck']} seed {m['seed']} is not the run of {run_dirs[0]} ({m0['deck']}, seed {m0['seed']})")
    deck = m0['deck']
    arms = sorted({os.path.basename(a)[4:] for rd in run_dirs for a in glob.glob(os.path.join(rd, 'arm-*'))})
    arm = arm or ('playbook' if 'playbook' in arms else (arms[0] if arms else None))
    if arm not in arms:
        raise SystemExit(f"no arm {arm} in {run_dirs[0]} (it has {', '.join(arms) or 'none'})")

    C = collections.Counter()
    by_seat = [[0, 0] for _ in range(4)]
    S = collections.defaultdict(list)
    opp = collections.defaultdict(collections.Counter)
    cards = collections.defaultdict(lambda: {'drawn': 0, 'played': 0, 'turns': [], 'won_drawn': 0, 'held_at_loss': 0})
    info = {}
    commanders = set()
    pilot = None
    opp_pilots = collections.Counter()
    reasons = collections.Counter()
    seen = set()
    for rd in run_dirs:
        for gd in sorted(glob.glob(os.path.join(rd, f'arm-{arm}', 'g*'))):
            rj = os.path.join(gd, 'run.json')
            if not os.path.exists(rj) or os.path.basename(gd) in seen:
                continue
            run = json.load(open(rj, encoding='utf-8'))
            if not run.get('games'):
                continue
            g = run['games'][0]
            evf = os.path.join(gd, 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                evf += '.gz'
                if not os.path.exists(evf):
                    continue
            seen.add(os.path.basename(gd))
            decks = sorted(run['decks'], key=lambda d: d['seat'])
            me_d = next(d for d in decks if d['id'] == deck)
            fs = me_d['seat']
            ids = {d['seat']: d['id'] for d in decks}
            for c in me_d['cards']:
                info[c['name']] = c
            commanders |= set(me_d.get('commanders') or [])
            pb = me_d.get('playbook')
            pilot = pilot or ({'playbook': os.path.basename(pb.get('file') or ''), 'version': pb.get('version'),
                               'attack': (pb.get('attack') or {}).get('policy')} if pb else {'playbook': None})
            for d in decks:
                if d['seat'] != fs:
                    opp_pilots['playbook' if d.get('playbook') else 'stock'] += 1
            me = next(p for p in g['players'] if p['seat'] == fs)
            won = bool(me.get('won'))
            C['games'] += 1; C['wins'] += won; C['not_finished'] += g.get('winner') is None
            by_seat[fs][0] += 1; by_seat[fs][1] += won
            C['mulligan_games'] += bool(me.get('mulligans'))
            S['game_turns'].append(g.get('turns'))
            (S['own_turns_won'] if won else S['own_turns_lost']).append(me.get('turns_played'))
            for s, i in ids.items():
                if s != fs:
                    opp[i]['tables'] += 1; opp[i]['focus_wins'] += won; opp[i]['wins'] += g.get('winner') == s

            own = 0; cur = None
            first_in_hand = {}; first_cast = {}
            state_at = {}; last_state = None; last_state_t = None
            taken = []; cast_this_turn = 0; castable_at_start = False
            n = collections.Counter()
            cmd_first = None
            lost_order = []

            def close_turn():
                # an own turn from the third on that cast no spell although something in hand was affordable
                if own >= 3:
                    n['own_turns_3plus'] += 1
                    if cast_this_turn == 0 and castable_at_start:
                        n['idle'] += 1

            for e in events(evf):
                k = e['e']
                if k == 'turn':
                    if cur == fs:
                        close_turn()
                    cur = e['seat']
                    mine = next(x for x in e['state'] if x['seat'] == fs)
                    for c in mine.get('hand') or []:
                        first_in_hand.setdefault(c, own if cur != fs else e['own_turn'])
                    if cur == fs:
                        own = e['own_turn']; cast_this_turn = 0
                        last_state = mine; last_state_t = e['t']
                        state_at[own] = mine
                        lands = mine.get('lands') or 0
                        castable_at_start = any((info.get(c, {}).get('cmc') or 0) <= lands and not info.get(c, {}).get('land')
                                                for c in mine.get('hand') or [] if c in info)
                elif k == 'cast' and e.get('seat') == fs and e.get('spell') and not e.get('copy'):
                    if cur == fs:
                        cast_this_turn += 1
                    n['spells'] += 1
                    if e.get('commander'):
                        n['commander_casts'] += 1
                        if cmd_first is None:
                            cmd_first = own
                    elif e.get('from') == 'Hand':
                        first_cast.setdefault(e['card'], own)
                elif k == 'damage':
                    if e['seat'] == fs:
                        n['taken'] += e['amount']; taken.append((e['t'], e.get('source_seat'), e['amount']))
                    elif e.get('source_seat') == fs:
                        n['dealt'] += e['amount']
                        if e.get('source_commander'):
                            n['commander_dealt'] += e['amount']
                elif k == 'lost':
                    lost_order.append(e['seat'])
                    if e['seat'] == fs:
                        reasons[e.get('reason') or 'unknown'] += 1
                        by = collections.Counter()
                        for t, src, amt in taken:
                            if last_state_t is not None and t >= last_state_t and src is not None and src != fs:
                                by[src] += amt
                        if by:
                            top = max(by, key=by.get)
                            opp[ids[top]]['took_it_out'] += 1
            if cur == fs:
                close_turn()
            if not won and g.get('winner') is not None:
                C['losses'] += 1
                place = lost_order.index(fs) + 1 if fs in lost_order else None
                C[f'out_{place}'] += 1
                ms = last_state or {}
                lands = ms.get('lands') or 0
                hand = [c for c in (ms.get('hand') or []) if c in info and not info[c].get('land')]
                S['hand_at_loss'].append(len(hand))
                S['castable_at_loss'].append(sum(1 for c in hand if (info[c].get('cmc') or 0) <= lands))
                for c in set(hand):
                    cards[c]['held_at_loss'] += 1
            for t in OWN_TURNS:
                if t in state_at:
                    S[f'lands_{t}'].append(state_at[t].get('lands'))
                    S[f'hand_{t}'].append(len(state_at[t].get('hand') or []))
            if 5 in state_at:
                C['reached_5'] += 1; C['short_of_4_lands'] += (state_at[5].get('lands') or 0) < 4
            S['cmd_first'].append(cmd_first)
            for key in ('spells', 'commander_casts', 'dealt', 'taken', 'commander_dealt'):
                S[key].append(n[key])
            C['own_turns_3plus'] += n['own_turns_3plus']; C['idle'] += n['idle']
            for c in set(first_in_hand) | set(first_cast):
                if c in commanders or c not in info or info[c].get('land'):
                    continue
                r = cards[c]; r['drawn'] += 1; r['won_drawn'] += won
                if c in first_cast:
                    r['played'] += 1; r['turns'].append(first_cast[c])

    games = C['games']
    if not games:
        raise SystemExit(f"no finished games of arm {arm} under {', '.join(run_dirs)}")
    wins = C['wins']
    seats = (m0.get('opponents') or 3) + 1
    rows = {}
    for c, r in cards.items():
        nd = games - r['drawn']
        rows[c] = {'drawn': r['drawn'], 'played': r['played'], 'played_share': share(r['played'], r['drawn']),
                   'median_turn': st.median(r['turns']) if r['turns'] else None,
                   'win_rate_drawn': share(r['won_drawn'], r['drawn']), 'win_rate_not_drawn': share(wins - r['won_drawn'], nd),
                   'held_at_loss': r['held_at_loss'], 'mv': info[c].get('cmc'), 'type': info[c].get('type')}
    cf = [x for x in S['cmd_first'] if x is not None]
    return {
        'kind': 'playtest', 'deck': deck, 'deck_file': m0.get('deck_file'), 'deck_file_sha256': m0.get('deck_file_sha256'),
        'arm': arm, 'pilot': pilot, 'commanders': sorted(commanders),
        'table': {'pool': m0.get('pool') or m0.get('league'), 'seats': seats, 'seed': m0.get('seed'), 'forge_version': m0.get('forge_version'),
                  'opponent_seats_under_a_playbook': opp_pilots['playbook'], 'opponent_seats_under_stock_ai': opp_pilots['stock']},
        'result': {'games': games, 'wins': wins, 'win_rate': share(wins, games), 'win_rate_ci95': rl.wilson(wins, games),
                   'even_share': round(1 / seats, 3), 'not_finished': C['not_finished'],
                   'by_seat': [{'games': a, 'wins': b} for a, b in by_seat[:seats]],
                   'losses': C['losses'], 'out_first': C['out_1'], 'out_second': C['out_2'], 'out_third': C['out_3'],
                   'loss_reasons': dict(reasons.most_common()),
                   'game_turns': mean(S['game_turns'], 1), 'own_turns_when_won': mean(S['own_turns_won'], 1),
                   'own_turns_when_lost': mean(S['own_turns_lost'], 1)},
        'opponents': {i: {'tables': o['tables'], 'focus_wins': o['focus_wins'], 'focus_win_rate': share(o['focus_wins'], o['tables']),
                          'its_wins': o['wins'], 'its_win_rate': share(o['wins'], o['tables']), 'took_it_out': o['took_it_out']}
                      for i, o in sorted(opp.items(), key=lambda kv: (-(kv[1]['focus_wins'] / kv[1]['tables']), kv[0]))},
        'tempo': {'games_with_a_mulligan': share(C['mulligan_games'], games),
                  'lands_at_own_turn': {str(t): mean(S[f'lands_{t}']) for t in OWN_TURNS},
                  'cards_in_hand_at_own_turn': {str(t): mean(S[f'hand_{t}']) for t in OWN_TURNS},
                  'short_of_four_lands_at_turn_5': share(C['short_of_4_lands'], C['reached_5']),
                  'commander_first_cast': {'median': st.median(cf) if cf else None, 'p25': quartile(cf, .25), 'p75': quartile(cf, .75),
                                           'never_cast': share(len(S['cmd_first']) - len(cf), len(S['cmd_first'])),
                                           'casts_per_game': mean(S['commander_casts'])},
                  'spells_per_game': mean(S['spells'], 1), 'idle_turn_share': share(C['idle'], C['own_turns_3plus']),
                  'damage_dealt_per_game': mean(S['dealt'], 1), 'damage_taken_per_game': mean(S['taken'], 1),
                  'commander_damage_dealt_per_game': mean(S['commander_dealt'], 1),
                  'nonland_cards_in_hand_at_loss': mean(S['hand_at_loss']), 'of_them_affordable': mean(S['castable_at_loss'])},
        'cards': rows,
    }


def pct(x, nd=0):
    return 'n/a' if x is None else f"{100 * x:.{nd}f}%"


def goldfish(path):
    for cand in (path, os.path.join(path, 'goldfish.json')):
        if os.path.isfile(cand):
            return json.load(open(cand, encoding='utf-8'))
    raise SystemExit(f"{path}: no goldfish.json")


def render(res, min_drawn, gf=None):
    r = res['result']; t = res['table']; tp = res['tempo']
    p = res['pilot'] or {}
    pilot = (f"playbook `{p['playbook']}` version {p.get('version')}" + (f", {p['attack']} attack" if p.get('attack') else ", Forge's attack")
             if p.get('playbook') else "stock Forge AI")
    out = [f"# Playtest: {res['deck']}", '']
    out.append(f"- List: `{res['deck_file']}`" + (f" (sha256 {res['deck_file_sha256'][:12]})" if res.get('deck_file_sha256') else ''))
    out.append(f"- Pilot: {pilot} (arm `{res['arm']}`). Commander: {', '.join(res['commanders']) or 'none'}")
    out.append(f"- Table: {t['seats']} players, opponents drawn from `{t['pool']}`; {t['opponent_seats_under_a_playbook']} opponent seats under their "
               f"playbook, {t['opponent_seats_under_stock_ai']} under stock Forge AI; seed {t['seed']}, {t['forge_version']}")
    out += ['', '## Result', '']
    lo, hi = r['win_rate_ci95']
    out.append(f"**{r['wins']} wins in {r['games']} tables: {pct(r['win_rate'], 1)}** (95% {pct(lo)} to {pct(hi)}); an even share is {pct(r['even_share'])}. "
               f"{r['not_finished']} games were not finished (turn cap or clock).")
    out.append('')
    out.append("By seat (first to act is seat 1): " + ', '.join(f"{s['wins']} of {s['games']}" for s in r['by_seat']) + '.')
    out.append(f"Games ran {r['game_turns']} turns in all."
               + (f" It won on its own turn {r['own_turns_when_won']} on average." if r['own_turns_when_won'] is not None else '')
               + (f" When it lost it was out by its own turn {r['own_turns_when_lost']}." if r['own_turns_when_lost'] is not None else ''))
    if r['losses']:
        out.append(f"Of its {r['losses']} losses it was the first player out in {r['out_first']}, the second in {r['out_second']}, the last opponent standing in {r['out_third']}. "
                   "What took it out: " + ', '.join(f"{k} {v}" for k, v in r['loss_reasons'].items()) + '.')
    opps = res['opponents']
    floor = 8 if len(opps) > 24 else 1          # a large pool: each deck is met a handful of times, which says nothing
    shown = {i: o for i, o in opps.items() if o['tables'] >= floor}
    out += ['', '## Opponents', '']
    if floor > 1:
        out += [f"{len(opps)} different decks were met; the {len(shown)} met at {floor} tables or more are listed (the rest are in the JSON).", '']
    out += ['| Opponent | Tables | This deck won | The opponent won | Took this deck out |', '|---|---|---|---|---|']
    for i, o in shown.items():
        out.append(f"| {i} | {o['tables']} | {o['focus_wins']} ({pct(o['focus_win_rate'])}) | {o['its_wins']} ({pct(o['its_win_rate'])}) | {o['took_it_out']} |")
    out += ['', '## Tempo', '']
    la, ha, cf = tp['lands_at_own_turn'], tp['cards_in_hand_at_own_turn'], tp['commander_first_cast']
    out.append(f"- A mulligan in {pct(tp['games_with_a_mulligan'])} of games. Lands at the start of its own turns 4, 6, 8: {la['4']}, {la['6']}, {la['8']}; "
               f"cards in hand: {ha['4']}, {ha['6']}, {ha['8']}. Short of four lands at the start of turn 5 in {pct(tp['short_of_four_lands_at_turn_5'])} of games.")
    out.append(f"- Commander first cast on its own turn {cf['median']} (median; quartiles {cf['p25']} to {cf['p75']}), never cast in {pct(cf['never_cast'])} of games, "
               f"{cf['casts_per_game']} casts a game.")
    out.append(f"- {tp['spells_per_game']} spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): {pct(tp['idle_turn_share'])}.")
    out.append(f"- Damage dealt {tp['damage_dealt_per_game']} a game ({tp['commander_damage_dealt_per_game']} of it by the commander), taken {tp['damage_taken_per_game']}.")
    if tp['nonland_cards_in_hand_at_loss'] is not None:
        out.append(f"- When it lost it held {tp['nonland_cards_in_hand_at_loss']} nonland cards, {tp['of_them_affordable']} of them affordable with its lands.")
    if gf:
        dist = ', '.join(f"{k}: {v}" for k, v in sorted(gf.get('kill_turn_distribution', {}).items(), key=lambda kv: int(kv[0])))
        out += ['', '## Goldfish', '',
                f"Alone against three decks that do nothing ({gf.get('games')} games): the table is dead on turn {gf.get('kill_turn_mean')} on average "
                f"(median {gf.get('kill_turn_median')}, fastest {gf.get('kill_turn_min')}, slowest {gf.get('kill_turn_max')}); {gf.get('not_finished', 0)} games not finished. "
                f"By turn: {dist}."]
    rows = [(c, x) for c, x in res['cards'].items() if x['drawn'] >= min_drawn]
    base = r['win_rate']

    def line(c, x):
        d = None if x['win_rate_drawn'] is None or x['win_rate_not_drawn'] is None else x['win_rate_drawn'] - x['win_rate_not_drawn']
        return (f"| {c} | {x['mv'] if x['mv'] is not None else ''} | {x['drawn']} | {pct(x['played_share'])} | {x['median_turn'] if x['median_turn'] is not None else ''} "
                f"| {pct(x['win_rate_drawn'])} | {pct(x['win_rate_not_drawn'])} | {'' if d is None else f'{100 * d:+.0f}'} | {x['held_at_loss']} |")

    head = ['| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |', '|---|---|---|---|---|---|---|---|---|']
    out += ['', '## Cards', '', f"Nonland cards drawn in at least {min_drawn} games ({len(rows)} cards); the deck won {pct(base, 1)} of all games. "
            "The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.", '']
    unplayed = sorted((kv for kv in rows if (kv[1]['played_share'] or 0) < 0.5), key=lambda kv: (kv[1]['played_share'] or 0, -kv[1]['drawn']))
    if unplayed:
        out += ['### Drawn and mostly not cast', '',
                "Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all "
                "(`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, "
                "and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.", '']
        out += head + [line(c, x) for c, x in unplayed] + ['']
    out += ['### Every card, by win rate when drawn', ''] + head
    out += [line(c, x) for c, x in sorted(rows, key=lambda kv: (-(kv[1]['win_rate_drawn'] or 0), kv[0]))]
    return '\n'.join(out) + '\n'


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--goldfish', help='a runner/goldfish.sh run directory (or its goldfish.json) of the same list')
    ap.add_argument('--min-drawn', type=int, help='list cards drawn in at least this many games (default: a tenth of the games, at least 5)')
    ap.add_argument('--md', help='also write the report here')
    ap.add_argument('--json', help='also write the numbers here (kind "playtest")')
    a = ap.parse_args(argv)
    res = collect(a.run_dirs, a.arm)
    gf = goldfish(a.goldfish) if a.goldfish else None
    if gf:
        res['goldfish'] = {k: gf.get(k) for k in ('games', 'wins', 'not_finished', 'kill_turn_mean', 'kill_turn_median', 'kill_turn_min', 'kill_turn_max', 'kill_turn_distribution')}
    md = render(res, a.min_drawn if a.min_drawn is not None else max(5, res['result']['games'] // 10), gf)
    sys.stdout.write(md)
    if a.md:
        with open(a.md, 'w', encoding='utf-8') as f:
            f.write(md)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
