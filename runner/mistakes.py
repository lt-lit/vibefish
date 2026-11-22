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
                     little. Tricks, fogs and life gain can undo a sure kill (about one in twenty-five of the kills
                     a seat goes for), and a seat that takes the kill and is stopped is counted as having missed.
                     Not every such turn is a mistake, and the count says which are (DESIGN.md §34, the exam of
                     `finish`): the turns are split by where the table stood. The opponent that could be killed was
                     the last one (the kill wins the game), the most dangerous of several (the highest life + 2 x
                     nonland permanents among the opponents alive), or a less dangerous one while a more dangerous
                     one lived. A miss of the first two is a mistake. The third is not: at 2,000 tables a seat that
                     took every such kill lost more games than the same seat leaving the weaker opponent alive.
                     Set aside, and in none of these counts: a turn on which a permanent limits how many creatures
                     may attack (Silent Arbiter and the like, ATTACK_LIMITS below). The `combat` line's `through`
                     does not know the limit, so its sure kill is not one; such turns are counted as
                     `kill_limited_turns`. (Found on the pool of twelve, 2026-11-22: one deck there plays Silent
                     Arbiter, and a seat with eighty power that sends one creature at the last opponent is doing
                     all the card allows.)
  a death by a block not made
                     The seat was attacked, what its blocks left unblocked was at least its life, it lost that turn,
                     and the best blocks its creatures could have made would have left less than its life.
                     A death on a turn a permanent limited the number of blockers (the same cards) is in neither
                     this count nor the next: what the best blocks could have done is not known from the line
                     (`deaths_block_limited`).
  a death tapped out No block could have saved it, but its own tapped creatures could have, had they been untapped:
                     it attacked (or tapped them for something else) and died to the answer. Not always a mistake
                     (a race can be right), so read it beside the other two.
  a death by commander damage
                     The seat lost on a turn on which an attacking commander's damage brought its total on the seat
                     to 21. Since harness 0.4.3 the `block` line says so (`cmd`) and says whether any blocks could
                     have stopped every such attacker (`cmd_best`, `cmd_best_untapped`), and a death is a block not
                     made, or tapped out, only if the blocks that save the seat's life also stop that commander. In
                     older logs it is read off the damage dealt, and whether the commander could have been blocked
                     is not known: those deaths are counted here and in neither of the two above (at the owner's
                     table 81 of 135 deaths first counted as a block not made were of this kind, most of them to
                     one flying commander).
  an open board not attacked
                     A turn on which some opponent had no creature that could block and the seat had a creature
                     that could attack that opponent: did anything attack that opponent, did the seat attack only
                     opponents that could block, or nobody? Not a mistake by itself (the creature may be wanted at
                     home); the shares say how a table uses free damage. Forge's AI weighs an attack against one
                     opponent, so a creature it will not send into that opponent's blockers stays home whoever
                     else is open; a playbook's `"open": true` on its attack is the hook for it (harness 0.4.5).
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
        'kill_last_turns', 'kill_last_missed', 'kill_top_turns', 'kill_top_missed', 'kill_lesser_turns', 'kill_lesser_missed',
        'open_turns', 'open_attacked', 'open_elsewhere',
        'attacked_lethal', 'combat_deaths', 'block_not_made', 'died_tapped_out', 'commander_deaths',
        'kill_limited_turns', 'deaths_block_limited')

# Permanents whose static ability limits how many creatures may attack (Forge scripts with `Mode$ AttackRestrict |
# MaxAttackers$ N`, snapshot 2026-11-10): 'all' limits every combat, 'you' attacks on its controller. The harness's
# `through` and `best` do not know them (they are not an attack cost and not a rule about one creature), so a turn
# under one is set aside. Tracked by name through the zone lines; a copy under another name is not seen.
ATTACK_LIMITS = {'Silent Arbiter': 'all', 'Dueling Grounds': 'all', 'Caverns of Despair': 'all', 'Crawlspace': 'you', 'Judoon Enforcers': 'you'}
BLOCK_LIMITS = ('Silent Arbiter', 'Dueling Grounds', 'Caverns of Despair')


def danger(d, turn):
    """How dangerous an opponent looks: its life + 2 x its nonland permanents (DESIGN.md §33; a playbook's default weights).
    The permanents are on the combat line since harness 0.4.1 and are taken from the start of the turn before."""
    n = d.get('permanents')
    if n is None:
        st = (turn.get('state') or {}).get(d['seat']) or {}
        n = st.get('bf', 0) - st.get('lands', 0)
    return d['life'] + 2 * n


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
        if killable and (turn.get('limit_all') or turn.get('limit_you')):
            free = [d for d in killable if not turn.get('limit_all') and d['seat'] not in turn['limit_you']]
            if len(free) < len(killable):
                g['kill_limited_turns'] += 1
            killable = free
        if killable:
            g['kill_turns'] += 1
            live = [d for d in defenders if d['life'] > 0]
            top = max(danger(d, turn) for d in live)
            stood = 'last' if len(live) == 1 else ('top' if any(danger(d, turn) == top for d in killable) else 'lesser')
            g[f'kill_{stood}_turns'] += 1
            if any(lost_at.get(d['seat']) == turn['t'] for d in killable):
                g['kill_taken'] += 1
            elif any(lost_at.get(d['seat']) == turn['t'] for d in defenders):
                g['kill_other'] += 1                     # another opponent went out that turn instead: not counted as missed
            else:
                g['kill_missed'] += 1
                g[f'kill_{stood}_missed'] += 1
                attacked = any(turn['attacks'].get(d['seat']) for d in killable)
                g['kill_missed_short' if attacked else 'kill_missed_no_attack'] += 1
                turn['missed'] = True
                if len(examples) < 400:
                    examples.append({'where': where, 't': turn['t'], 'seat': a, 'deck': label(a), 'stood': stood,
                                     'killable': [{k: d[k] for k in ('seat', 'life', 'power', 'blockers', 'through')} for d in killable],
                                     'attacked': {str(k): len(v) for k, v in turn['attacks'].items()}})
        open_def = [d for d in defenders if d['blockers'] == 0 and d['attackers'] > 0 and d['power'] > 0]
        if open_def:
            g['open_turns'] += 1
            if any(turn['attacks'].get(d['seat']) for d in open_def):
                g['open_attacked'] += 1
            elif any(turn['attacks'].values()):
                g['open_elsewhere'] += 1                # it attacked, and only opponents that could block
    for b in turn['blocks']:
        d = b.get('seat')
        if d is None or 'incoming' not in b:
            continue
        g = G[label(d)]
        if 'cmd' in b:                                   # 0.4.3: the line says it
            cmd, cmd_best, cmd_best_u = b['cmd'], b.get('cmd_best', False), b.get('cmd_best_untapped', b.get('cmd_best', False))
        else:                                            # before: read off the damage dealt; whether a block could have stopped it is not known
            cmd = cmd_best = cmd_best_u = d in turn.get('cmd_dealt', ())
        if b['life'] > 0 and (b['incoming'] >= b['life'] or cmd):
            g['attacked_lethal'] += 1
            if lost_at.get(d) == turn['t']:
                g['combat_deaths'] += 1
                g['commander_deaths'] += bool(cmd)
                if b.get('block_limited'):
                    g['deaths_block_limited'] += 1
                elif b['best'] < b['life'] and not cmd_best:
                    g['block_not_made'] += 1
                elif b.get('best_untapped', b['best']) < b['life'] and not cmd_best_u:
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
            dealt = collections.Counter()               # (seat, commander) -> the combat damage it has dealt to that seat
            limits = {}                                 # id -> (name, its controller's seat) of the limiting permanents on the battlefield
            for e in evs:
                k = e['e']
                if k == 'zone':
                    if e.get('card') in ATTACK_LIMITS:
                        if e.get('to') == 'Battlefield':
                            limits[e.get('id')] = (e['card'], e.get('seat'))
                        elif e.get('from') == 'Battlefield':
                            limits.pop(e.get('id'), None)
                    continue
                if k == 'turn':
                    cur = {'seat': e.get('seat'), 't': e['t'], 'combat': None, 'attacks': collections.defaultdict(list), 'blocks': [],
                           'state': {x['seat']: x for x in e.get('state') or []}}
                    turns.append(cur)
                elif cur is None:
                    continue
                elif k == 'combat':
                    cur['combat'] = e
                    cur['limit_all'] = any(ATTACK_LIMITS[n] == 'all' for n, _ in limits.values())
                    cur['limit_you'] = {s for n, s in limits.values() if ATTACK_LIMITS[n] == 'you'}
                elif k == 'attack' and e.get('seat') == cur['seat']:
                    for at in e.get('attacks') or []:
                        if not at.get('planeswalker') and at.get('defender_seat') is not None:
                            cur['attacks'][at['defender_seat']].append(at.get('attacker'))
                elif k == 'block':
                    if any(n in BLOCK_LIMITS for n, _ in limits.values()):
                        e = dict(e, block_limited=True)
                    cur['blocks'].append(e)
                elif k == 'damage' and e.get('combat') and e.get('source_commander') and e.get('seat') is not None:
                    dealt[(e['seat'], e.get('source'))] += e.get('amount', 0)
                    if dealt[(e['seat'], e.get('source'))] >= 21:
                        cur.setdefault('cmd_dealt', set()).add(e['seat'])
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
    if any(G[n]['kill_limited_turns'] or G[n]['deaths_block_limited'] for n in names):
        out += ['  set aside (a permanent limited the number of attackers or blockers, which the lines do not know): '
                + '; '.join(f'{n} {G[n]["kill_limited_turns"]} turns with a kill by the count, {G[n]["deaths_block_limited"]} deaths in combat' for n in names)]
    out += ['', 'KILLS BY WHERE THE TABLE STOOD: the opponent that could be killed was the last one (the kill wins the game); the most dangerous of several',
            '       (life + 2 x nonland permanents); a less dangerous one while a more dangerous one lived. A miss of the first two is a mistake; the third is not (DESIGN §34)',
            f'  {"":{w}} {"last":>6} {"missed":>7} {"share":>6}   {"most dangerous":>15} {"missed":>7} {"share":>6}   {"a lesser one":>13} {"missed":>7} {"share":>6}   mistakes a seat-game']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["kill_last_turns"]:>6} {g["kill_last_missed"]:>7} {pct(g["kill_last_missed"], g["kill_last_turns"]):>6}   '
                   f'{g["kill_top_turns"]:>15} {g["kill_top_missed"]:>7} {pct(g["kill_top_missed"], g["kill_top_turns"]):>6}   '
                   f'{g["kill_lesser_turns"]:>13} {g["kill_lesser_missed"]:>7} {pct(g["kill_lesser_missed"], g["kill_lesser_turns"]):>6}   '
                   + (f'{(g["kill_last_missed"] + g["kill_top_missed"]) / g["seat_games"]:.3f}' if g['seat_games'] else ''))
    out += ['', 'BLOCKS: attacks that left at least the seat\'s life unblocked; the seat lost that turn; of those, its creatures could have blocked enough to live;',
            '        and those no block could stop that its own tapped creatures would have, had they stayed home; deaths on a turn a commander\'s damage reached 21',
            '        (in logs before harness 0.4.3 those are in neither of the two columns before: whether that commander could have been blocked is not known)',
            f'  {"":{w}} {"lethal attacks":>15} {"died":>6} {"a block not made":>17} {"tapped out":>11} {"commander damage":>17}']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["attacked_lethal"]:>15} {g["combat_deaths"]:>6} {g["block_not_made"]:>17} {g["died_tapped_out"]:>11} {g["commander_deaths"]:>17}')
    out += ['', 'ATTACKS: turns with a creature that could attack; attacked; the damage sent of the damage that could be; turns with an opponent who could not block: '
            'attacked it, attacked only opponents that could block, attacked nobody',
            f'  {"":{w}} {"turns":>7} {"attacked":>9} {"damage sent":>12} {"open board":>11} {"attacked it":>12} {"another":>8} {"nobody":>7}']
    for n in names:
        g = G[n]
        out.append(f'  {n:{w}} {g["turns_able"]:>7} {pct(g["turns_attacked"], g["turns_able"]):>9} {pct(g["power_sent"], g["power_able"]):>12} '
                   f'{g["open_turns"]:>11} {pct(g["open_attacked"], g["open_turns"]):>12} {pct(g["open_elsewhere"], g["open_turns"]):>8} '
                   f'{pct(g["open_turns"] - g["open_attacked"] - g["open_elsewhere"], g["open_turns"]):>7}')
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
