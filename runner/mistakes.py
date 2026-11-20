#!/usr/bin/env python3
"""Mistakes that need no human to define, counted from the JSONL event logs. Read-only; prints text.

  runner/mistakes.py RUN_DIR [RUN_DIR ...] [--arm stock] [--by-deck] [--deck ID] [--json OUT.json] [--show N]

RUN_DIR is anything that holds run.json files with their games/ beside them (a league run, an ab.py run or its
unzipped shard artifacts, a pod run), played on harness 0.4.0 or later: the counts come from the `combat` line the
logger writes as a player's declare-attackers step begins and from the facts on the `block` line (DESIGN.md §6).
--arm keeps the games of one A/B arm. Seats are grouped by pilot (`bot` has a playbook, `stock` has none) unless
--by-deck groups them by deck; --deck keeps one deck's seats.

What is counted, per seat:

  a kill not taken   On its own turn the seat could attack an opponent for at least that opponent's life whatever
                     that opponent blocked (`through >= life`: Forge's own rules for who may attack and block whom,
                     one blocker an attacker, no trample credited, infect left out, no attack that costs anything),
                     and at the end of the turn no opponent was out of the game (when another opponent than the
                     one it was sure to kill went out that turn, the turn is listed apart and not as a miss).
                     Split by what the seat did: it did not attack that opponent at all, or it did and with too
                     little. Tricks, fogs and life gain can undo a sure kill, so read the count as "nearly always a
                     mistake"; a seat that takes the kill and is stopped by one of those is counted as having missed.
  a death by a block not made
                     The seat was attacked, what its blocks left unblocked was at least its life, it lost that turn,
                     and the best blocks its creatures could have made would have left less than its life.
  a death tapped out No block could have saved it, but its own tapped creatures could have, had they been untapped:
                     it attacked (or tapped them for something else) and died to the answer. Not always a mistake
                     (a race can be right), so read it beside the other two.
  an open board not attacked
                     A turn on which some opponent had no creature that could block and the seat had a creature
                     that could attack that opponent: did anything attack that opponent? Not a mistake by itself
                     (the creature may be wanted at home); the share says how a table uses free damage.
  attacks            Of the turns on which the seat had a creature that could attack someone, the share on which it
                     attacked, and the share of the damage it could have sent that it did send.
"""
import argparse, collections, glob, gzip, json, os, sys


def events(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def run_files(roots, arm):
    for root in roots:
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            if arm and f'{os.sep}arm-{arm}{os.sep}' not in rj:
                continue
            yield rj


KEYS = ('seat_games', 'turns_able', 'turns_attacked', 'power_able', 'power_sent',
        'kill_turns', 'kill_taken', 'kill_other', 'kill_missed', 'kill_missed_no_attack', 'kill_missed_short', 'kill_missed_then_lost', 'kill_missed_then_won',
        'open_turns', 'open_attacked',
        'attacked_lethal', 'combat_deaths', 'block_not_made', 'died_tapped_out')


def close_turn(G, label, turn, lost_at, examples, where):
    """Counts one finished turn. turn: {'seat', 'combat', 'attacks': {defender_seat: [attacker names]}, 'blocks': [...], 't'}."""
    a = turn.get('seat')
    c = turn.get('combat')
    if a is not None and c is not None and c.get('seat') == a:
        g = G[label(a)]
        able = collections.Counter()
        power_by_name = collections.defaultdict(list)
        for name, p in c.get('able') or []:
            power_by_name[name].append(p)
        for name in power_by_name:
            power_by_name[name].sort(reverse=True)
        defenders = c.get('defenders') or []
        best_power = max([d['power'] for d in defenders] or [0])
        if c.get('able'):
            g['turns_able'] += 1
            g['power_able'] += best_power
            sent = 0
            took = collections.Counter()
            for ds, names in turn['attacks'].items():
                for n in names:
                    k = took[n]
                    took[n] += 1
                    if n in power_by_name:
                        sent += power_by_name[n][min(k, len(power_by_name[n]) - 1)]
            if turn['attacks']:
                g['turns_attacked'] += 1
            g['power_sent'] += min(sent, best_power) if best_power else 0
        killable = [d for d in defenders if d['life'] > 0 and d['through'] >= d['life']]
        if killable:
            g['kill_turns'] += 1
            if any(lost_at.get(d['seat']) == turn['t'] for d in killable):
                g['kill_taken'] += 1
            elif any(lost_at.get(d['seat']) == turn['t'] for d in defenders):
                g['kill_other'] += 1                     # another opponent went out that turn instead: not counted as missed
            else:
                g['kill_missed'] += 1
                attacked = any(turn['attacks'].get(d['seat']) for d in killable)
                g['kill_missed_short' if attacked else 'kill_missed_no_attack'] += 1
                turn['missed'] = True
                if len(examples) < 400:
                    examples.append({'where': where, 't': turn['t'], 'seat': a, 'deck': label(a),
                                     'killable': [{k: d[k] for k in ('seat', 'life', 'power', 'blockers', 'through')} for d in killable],
                                     'attacked': {str(k): len(v) for k, v in turn['attacks'].items()}})
        open_def = [d for d in defenders if d['blockers'] == 0 and d['attackers'] > 0 and d['power'] > 0]
        if open_def:
            g['open_turns'] += 1
            if any(turn['attacks'].get(d['seat']) for d in open_def):
                g['open_attacked'] += 1
    for b in turn['blocks']:
        d = b.get('seat')
        if d is None or 'incoming' not in b:
            continue
        g = G[label(d)]
        if b['incoming'] >= b['life'] > 0:
            g['attacked_lethal'] += 1
            if lost_at.get(d) == turn['t']:
                g['combat_deaths'] += 1
                if b['best'] < b['life']:
                    g['block_not_made'] += 1
                elif b.get('best_untapped', b['best']) < b['life']:
                    g['died_tapped_out'] += 1


def collect(roots, arm=None, by_deck=False, deck=None):
    G = collections.defaultdict(collections.Counter)
    examples = []
    games = old = 0
    for rj in run_files(roots, arm):
        run = json.load(open(rj))
        ids = {d['seat']: d['id'] for d in run['decks']}
        pilot = {d['seat']: ('bot' if d.get('playbook') else 'stock') for d in run['decks']}
        keep = (lambda s: deck is None or ids.get(s) == deck)
        label = (lambda s: ids[s]) if by_deck else (lambda s: pilot[s])
        for g in run['games']:
            if not g.get('events'):
                continue
            evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
            if not os.path.exists(evf):
                evf += '.gz'
                if not os.path.exists(evf):
                    continue
            winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
            evs = list(events(evf))
            if not any(e['e'] == 'combat' for e in evs):
                old += 1
                continue
            games += 1
            lost_at = {e['seat']: e['t'] for e in evs if e['e'] == 'lost'}
            local = collections.defaultdict(collections.Counter)
            turns = []
            cur = None
            for e in evs:
                k = e['e']
                if k == 'turn':
                    cur = {'seat': e.get('seat'), 't': e['t'], 'combat': None, 'attacks': collections.defaultdict(list), 'blocks': []}
                    turns.append(cur)
                elif cur is None:
                    continue
                elif k == 'combat':
                    cur['combat'] = e
                elif k == 'attack' and e.get('seat') == cur['seat']:
                    for at in e.get('attacks') or []:
                        if not at.get('planeswalker') and at.get('defender_seat') is not None:
                            cur['attacks'][at['defender_seat']].append(at.get('attacker'))
                elif k == 'block':
                    cur['blocks'].append(e)
            where = os.path.relpath(evf, roots[0]) if len(roots) == 1 else evf
            for t in turns:
                close_turn(local, lambda s: s, t, lost_at, examples, where)
                if t.get('missed'):
                    s = t['seat']
                    local[s]['kill_missed_then_won' if winner == s else 'kill_missed_then_lost'] += 1
            for ex in examples:
                if isinstance(ex.get('deck'), int) and ex['where'] == where:
                    ex['deck'] = ids.get(ex['deck'], ex['deck'])
            for s in ids:
                if not keep(s):
                    continue
                grp = G[label(s)]
                grp['seat_games'] += 1
                grp.update(local.get(s, {}))
    return G, games, old, examples


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def render(G, games, old, examples, show):
    out = [f'{games} games' + (f' ({old} games without combat lines were left out: played before harness 0.4.0)' if old else '')]
    if not games:
        return '\n'.join(out)
    names = sorted(G)
    w = max(len(n) for n in names) + 2
    out += ['', 'KILLS: turns on which a kill no block prevents was there; taken; another opponent went out instead; missed (the seat did not attack that opponent /',
            '       attacked it with too little); a game in which the seat missed one and went on to lose it',
            f'  {"":{w}} {"there":>6} {"taken":>6} {"another":>8} {"missed":>7} {"share":>6} {"no attack":>10} {"too little":>11} {"missed, lost":>13}   a seat-game']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["kill_turns"]:>6} {g["kill_taken"]:>6} {g["kill_other"]:>8} {g["kill_missed"]:>7} {pct(g["kill_missed"], g["kill_turns"]):>6} '
                   f'{g["kill_missed_no_attack"]:>10} {g["kill_missed_short"]:>11} {g["kill_missed_then_lost"]:>13}   '
                   f'{g["kill_missed"] / g["seat_games"]:.2f} missed' if g['seat_games'] else '')
    out += ['', 'BLOCKS: attacks that left at least the seat\'s life unblocked; the seat lost that turn; of those, its creatures could have blocked enough to live;',
            '        and those no block could stop that its own tapped creatures would have, had they stayed home',
            f'  {"":{w}} {"lethal attacks":>15} {"died":>6} {"a block not made":>17} {"tapped out":>11}']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["attacked_lethal"]:>15} {g["combat_deaths"]:>6} {g["block_not_made"]:>17} {g["died_tapped_out"]:>11}')
    out += ['', 'ATTACKS: turns with a creature that could attack; attacked; the damage sent of the damage that could be; turns with an opponent who could not block: attacked it',
            f'  {"":{w}} {"turns":>7} {"attacked":>9} {"damage sent":>12} {"open board":>11} {"attacked it":>12}']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["turns_able"]:>7} {pct(g["turns_attacked"], g["turns_able"]):>9} {pct(g["power_sent"], g["power_able"]):>12} '
                   f'{g["open_turns"]:>11} {pct(g["open_attacked"], g["open_turns"]):>12}')
    if show and examples:
        out += ['', f'KILLS NOT TAKEN, the first {min(show, len(examples))} (game, turn, deck: the opponent it could have killed, what it sent where)']
        for ex in examples[:show]:
            k = '; '.join(f'seat {d["seat"]} at {d["life"]} life, {d["through"]} sure of {d["power"]} against {d["blockers"]} blockers' for d in ex['killable'])
            out.append(f'  {ex["where"]} turn {ex["t"]} {ex["deck"]}: {k}; attackers sent {ex["attacked"] or "nowhere"}')
    return '\n'.join(out)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run_dirs', nargs='+')
    ap.add_argument('--arm')
    ap.add_argument('--by-deck', action='store_true')
    ap.add_argument('--deck')
    ap.add_argument('--json')
    ap.add_argument('--show', type=int, default=0, help='list this many kills not taken')
    a = ap.parse_args(argv)
    G, games, old, examples = collect(a.run_dirs, a.arm, a.by_deck, a.deck)
    print(render(G, games, old, examples, a.show))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'kind': 'mistakes', 'games': games, 'games_without_combat_lines': old, 'arm': a.arm, 'by_deck': a.by_deck, 'deck': a.deck,
                       'groups': {n: {k: G[n].get(k, 0) for k in KEYS} for n in sorted(G)}, 'kills_not_taken': examples}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
