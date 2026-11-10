#!/usr/bin/env python3
"""What one seat did with its cards, read from the JSONL event logs. Read-only; prints text.

  runner/hands.py game EVENTS.jsonl[.gz] [--deck ID | --seat N]
      one game turn by turn for one seat: the hand it started the turn with, the land, every spell and
      ability, the attacks, everyone's life. This is the page a playbook's cast rules are written from.

  runner/hands.py held RESULTS_DIR... [--deck ID] [--arm ARM] [--from-turn 3] [--top 30]
      over all games of the runs: how much of its mana the seat left unspent, and the cards it kept in
      hand on turns when the unspent mana would have paid for them.

  runner/hands.py compare RESULTS_A RESULTS_B [--deck ID] [--out FILE.json]
      two goldfish runs of one deck on the same seeds (runner/goldfish.sh with and without -P): kill
      turn by run, and the paired difference with its 95% interval. --out keeps the comparison as a
      file (kind "goldfish-pair": both runs' settings, and per_game with every game's seed and kill turn).

RESULTS_DIR is a goldfish, pod or league run (shard-*/run.json), a harness output directory (run.json)
or an ab.py run (arm-*/g*/run.json; --arm picks the arm, default every arm). The seat is the deck
named by --deck, else the deck under test of an A/B run, else the first deck of the run.

Mana is approximate, as in playstyle.py: lands in play (with the turn's land drop) against the mana
value of the spells cast that turn. Rituals, mana rocks, Treasures, cost reducers, activated abilities,
X and colour are not counted, so "unspent" is an upper bound for a deck with other mana sinks, and a
card counts as kept only when it was in hand at the start of two consecutive turns of the seat."""
import argparse, collections, datetime, glob, gzip, json, math, os, signal, statistics as st, sys


def open_events(path):
    return gzip.open(path, 'rt', encoding='utf-8') if path.endswith('.gz') else open(path, encoding='utf-8')


def is_copy(e):
    """A copy of a spell (Zada, storm, replicate): logged as a cast, but no card left a hand for it. Harness 0.3.0
    marks it; before that a copy is the spell cast from no zone at all."""
    return bool(e.get('copy')) or (bool(e.get('spell')) and e.get('from') is None)


def read_events(path):
    with open_events(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_dirs(rd, arm=None):
    """Directories holding a run.json under a results directory, with the A/B arm (or None)."""
    out = []
    if os.path.exists(os.path.join(rd, 'run.json')):
        out.append((rd, None))
    out += [(d, None) for d in sorted(glob.glob(os.path.join(rd, 'shard-*'))) if os.path.exists(os.path.join(d, 'run.json'))]
    for a in sorted(glob.glob(os.path.join(rd, 'arm-*'))):
        name = os.path.basename(a)[4:]
        if arm and name != arm:
            continue
        out += [(d, name) for d in sorted(glob.glob(os.path.join(a, 'g*'))) if os.path.exists(os.path.join(d, 'run.json'))]
    return out


def focus_deck(rd, run, deck):
    """The deck id whose seat is read: --deck, the A/B's deck under test, or the run's first deck."""
    if deck:
        return deck
    ab = os.path.join(rd, 'ab.json')
    if os.path.exists(ab):
        return json.load(open(ab)).get('deck')
    return run['decks'][0]['id']


def games_of(rd, deck=None, arm=None):
    """Yields (run, seat, game summary, events path, arm) for every finished game of the deck in a results dir."""
    for d, a in run_dirs(rd, arm):
        run = json.load(open(os.path.join(d, 'run.json')))
        did = focus_deck(rd, run, deck)
        seats = [x['seat'] for x in run['decks'] if x['id'] == did]
        if not seats:
            continue
        for g in run.get('games', []):
            path = os.path.join(d, g['events'])
            if not os.path.exists(path) and os.path.exists(path + '.gz'):
                path += '.gz'
            if os.path.exists(path):
                yield run, seats[0], g, path, a


# ---------------------------------------------------------------------------------------------- game

def cmd_game(args):
    ev = read_events(args.events)
    seat = args.seat
    if seat is None:
        run_json = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(args.events))), 'run.json')
        seat = 0
        if os.path.exists(run_json):
            run = json.load(open(run_json))
            ids = {d['id']: d['seat'] for d in run['decks']}
            if args.deck:
                if args.deck not in ids:
                    sys.exit(f"no deck {args.deck} in {run_json}: {sorted(ids)}")
                seat = ids[args.deck]
            print(f"# {os.path.basename(args.events)}: seat {seat} = {run['decks'][seat]['id']}"
                  + (f", playbook {run['decks'][seat]['playbook'].get('file')}" if run['decks'][seat].get('playbook') else '')
                  + (f", data {run['decks'][seat]['data'].get('file')}" if run['decks'][seat].get('data') else ''))
    mine = None                       # the global turn number while it is the seat's own turn
    for e in ev:
        k = e['e']
        if k == 'turn':
            mine = e['t'] if e['seat'] == seat else None
            if mine is not None:
                s = e['state'][seat]
                others = ' '.join(str(x['life']) if x.get('alive', True) else 'x' for i, x in enumerate(e['state']) if i != seat)
                print(f"\nT{e['own_turn']:<2} life {s['life']}  lands {s['lands']}  permanents {s['bf']}  library {s['lib']}  others' life {others}")
                print(f"    hand ({len(s['hand'])}): {', '.join(s['hand']) or '-'}")
            continue
        if k == 'mulligan' and e.get('seat') == seat:
            print('mulligan')
        if k == 'lost':
            print(f"    -- seat {e['seat']} lost ({e.get('reason')}) on turn {e['t']}")
        if k == 'game_end':
            me = next((p for p in e['players'] if p['seat'] == seat), {})
            print(f"\nend: {e.get('reason')}, winner seat {e.get('winner')}, game turn {e['t']}, own turns {me.get('turns_played')}, life {me.get('life')}")
        if e.get('seat') != seat:
            continue
        where = '' if mine is not None and e.get('t') == mine else f"  [turn {e.get('t')}, not its own]"
        if k == 'land':
            print(f"    land   {e['card']}{where}")
        elif k == 'cast' and e.get('spell'):
            aim = f"  -> {', '.join(e['targets'])}" if e.get('targets') else ''
            aim += ''.join(f"  -> seat {t}" for t in e.get('target_seats', []))
            if is_copy(e):
                print(f"      copy   {e['card']}{aim}{where}")
            else:
                frm = '' if e.get('from') in ('Hand', None) else f" (from {e['from']})"
                print(f"    CAST   {e['card']}{frm}{aim}{where}")
        elif k == 'cast':
            print(f"      ability  {e['card']}: {(e.get('ability') or '')[:110]}{where}")
        elif k == 'attack':
            to = collections.Counter(a['defender_seat'] for a in e['attacks'])
            print(f"    ATTACK {len(e['attacks'])} attacker(s): " + ', '.join(f"{n} at seat {s}" for s, n in sorted(to.items())) + where)


# ---------------------------------------------------------------------------------------------- held

def cmd_held(args):
    held = collections.Counter(); seen = collections.Counter(); cmc_of = {}
    turns = left_sum = avail_sum = stuck = idle = games = 0
    for rd in args.runs:
        for run, seat, g, path, _arm in games_of(rd, args.deck, args.arm):
            cards = {c['name']: c for c in run['decks'][seat]['cards'] + run['decks'][seat].get('commander_cards', [])}
            ev = read_events(path)
            games += 1
            own = [e for e in ev if e['e'] == 'turn' and e['seat'] == seat]
            casts = collections.defaultdict(list); landed = collections.Counter()
            for e in ev:
                if e['e'] == 'cast' and e.get('seat') == seat and e.get('spell') and not is_copy(e):
                    casts[e['t']].append(e['card'])
                elif e['e'] == 'land' and e.get('seat') == seat:
                    landed[e['t']] += 1
            for i, e in enumerate(own[:-1]):
                if e['own_turn'] < args.from_turn:
                    continue
                s = e['state'][seat]
                lands = s['lands'] + landed[e['t']]
                spent = sum(cards.get(c, {}).get('cmc', 0) for c in casts[e['t']])
                left = max(0, lands - spent)
                turns += 1; left_sum += left; avail_sum += lands
                nxt = collections.Counter(own[i + 1]['state'][seat]['hand'])
                any_kept = False
                for c in s['hand']:
                    info = cards.get(c)
                    if not info or info.get('land'):
                        continue
                    cmc_of[c] = info.get('cmc', 0)
                    seen[c] += 1
                    if nxt[c] > 0:
                        nxt[c] -= 1
                        if info.get('cmc', 0) <= left:
                            held[c] += 1
                            any_kept = True
                stuck += any_kept
                idle += (not casts[e['t']]) and any_kept
    if not turns:
        sys.exit('no turns found (check the directory, --deck and --arm)')
    print(f"{games} games, {turns} own turns from turn {args.from_turn} on")
    print(f"mana left unspent: {left_sum / turns:.1f} of {avail_sum / turns:.1f} lands a turn ({left_sum / avail_sum:.0%})")
    print(f"turns that ended with a card in hand the unspent mana would have paid for: {stuck / turns:.0%}"
          f" (and nothing at all cast: {idle / turns:.0%})")
    print(f"\n{'kept':>5} {'in hand':>8}  {'mv':>2}  card   (turns kept with the mana for it unspent / turns it started in hand)")
    for c, h in sorted(held.items(), key=lambda kv: (-kv[1], kv[0]))[:args.top]:
        print(f"{h:>5} {seen[c]:>8}  {cmc_of[c]:>2}  {c}")


# ------------------------------------------------------------------------------------------- compare

def kill_turns(rd, deck, meta=None):
    """seed -> the deck's own turn of the win, or None when it did not win (capped, clock, lost)."""
    out = {}
    for run, seat, g, _path, _arm in games_of(rd, deck):
        me = next(p for p in g['players'] if p['seat'] == seat)
        out[g['seed']] = me['turns_played'] if g.get('winner') == seat else None
        if meta is not None:
            d = run['decks'][seat]
            meta.update({'run': os.path.basename(rd.rstrip('/')), 'deck': d['id'], 'deck_file': d.get('file'), 'vibefish': run.get('vibefish'),
                         'forge_version': run.get('forge_version'), 'forge_build': run.get('forge_build'), 'clock_s': run.get('clock_s'),
                         'turn_cap': run.get('turn_cap'), 'profile': d.get('profile'), 'playbook': d.get('playbook'),
                         'data': d.get('data'), 'opponents': [x['id'] for x in run['decks'] if x['seat'] != seat]})
            meta.setdefault('per_game', []).append({'seed': g['seed'], 'kill_turn': out[g['seed']], 'game_turns': g.get('turns'),
                                                    'reason': g.get('reason'), 'mulligans': me.get('mulligans'),
                                                    'duration_ms': g.get('duration_ms')})
    return out


def kill_summary(kills):
    k = [x for x in kills if x is not None]
    dist = collections.Counter(k)
    return {'games': len(kills), 'wins': len(k), 'not_finished': len(kills) - len(k),
            'kill_turn_mean': round(st.fmean(k), 3) if k else None, 'kill_turn_sd': round(st.stdev(k), 3) if len(k) > 1 else None,
            'kill_turn_median': st.median(k) if k else None, 'kill_turn_min': min(k) if k else None, 'kill_turn_max': max(k) if k else None,
            'kill_turn_distribution': {str(t): dist[t] for t in sorted(dist)}}


def describe(name, kills, n):
    k = [x for x in kills if x is not None]
    if not k:
        return f"{name}: {n} games, no wins"
    dist = collections.Counter(k)
    sd = st.stdev(k) if len(k) > 1 else 0.0
    return (f"{name}: {n} games, {len(k)} wins, kill turn mean {st.fmean(k):.2f} (sd {sd:.2f}), median {st.median(k):g}, "
            f"range {min(k)}-{max(k)}   " + ' '.join(f"{t}:{dist[t]}" for t in sorted(dist)))


def cmd_compare(args):
    ma, mb = {}, {}
    a, b = kill_turns(args.a, args.deck, ma), kill_turns(args.b, args.deck, mb)
    if not a or not b:
        sys.exit('no games found in one of the runs')
    print(describe('A ' + os.path.basename(args.a.rstrip('/')), list(a.values()), len(a)))
    print(describe('B ' + os.path.basename(args.b.rstrip('/')), list(b.values()), len(b)))
    both = sorted(s for s in a if s in b)
    d = [a[s] - b[s] for s in both if a[s] is not None and b[s] is not None]
    unfinished = sum(1 for s in both if a[s] is None or b[s] is None)
    if len(d) < 2:
        sys.exit(f"{len(both)} seeds in common, {len(d)} won by both: nothing to pair")
    m, sd = st.fmean(d), st.stdev(d)
    se = sd / math.sqrt(len(d))
    print(f"paired on {len(d)} seeds won by both ({unfinished} not finished by one of them): A - B = {m:+.2f} turns "
          f"(95% {m - 1.96 * se:+.2f} to {m + 1.96 * se:+.2f}; sd {sd:.2f}); B faster in {sum(x > 0 for x in d)}, "
          f"same in {sum(x == 0 for x in d)}, slower in {sum(x < 0 for x in d)}")
    if args.out:
        for meta, kills in ((ma, a), (mb, b)):
            meta.update(kill_summary(list(kills.values())))
            meta['per_game'] = sorted(meta.pop('per_game'), key=lambda g: g['seed'])     # the per-game list last
        result = {'kind': 'goldfish-pair', 'generated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                  'deck': ma.get('deck'), 'a': ma, 'b': mb,
                  'paired': {'seeds': len(d), 'not_finished_by_one': unfinished, 'a_minus_b_turns': round(m, 3),
                             'ci95': [round(m - 1.96 * se, 3), round(m + 1.96 * se, 3)], 'sd': round(sd, 3),
                             'b_faster': sum(x > 0 for x in d), 'same': sum(x == 0 for x in d), 'b_slower': sum(x < 0 for x in d)}}
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
            f.write('\n')
        print(f"wrote {args.out}")


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)      # piping into head is the normal way to read a digest
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('game'); g.add_argument('events'); g.add_argument('--deck'); g.add_argument('--seat', type=int)
    h = sub.add_parser('held'); h.add_argument('runs', nargs='+', metavar='RESULTS_DIR'); h.add_argument('--deck'); h.add_argument('--arm')
    h.add_argument('--from-turn', type=int, default=3); h.add_argument('--top', type=int, default=30)
    c = sub.add_parser('compare'); c.add_argument('a'); c.add_argument('b'); c.add_argument('--deck'); c.add_argument('--out')
    args = ap.parse_args()
    {'game': cmd_game, 'held': cmd_held, 'compare': cmd_compare}[args.cmd](args)


if __name__ == '__main__':
    main()
