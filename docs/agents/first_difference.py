#!/usr/bin/env python3
"""first_difference.py EXAM_RESULTS_DIR VARIANT DECK... [--base NAME] [--json OUT.json]: two arms of an exam, table by table.

EXAM_RESULTS_DIR holds the run directories `docs/agents/shards.sh` makes (ab-DECK for the shipped playbook, ab-DECK@VARIANT for
a candidate), both played on the same tables with `arms: playbook`. --base NAME compares ab-DECK@NAME with ab-DECK@VARIANT.

A hook that changes one decision changes few games: on most tables the two games are the same to the last event, and the tables
that differ for another reason (Forge's own run-to-run differences) only add noise to the paired count of wins. So the two games
of a table are read side by side to the first event that differs, and the table is filed by what that event is:

  identical    the two games are the same to the end
  attack       the first difference is the seat under test's own attack declaration: the hook's doing. Filed further by where
               the table stood on that turn: the seat was sure to kill its last opponent, the most dangerous of several
               (life + 2 x nonland permanents), a less dangerous one, or nobody
  other        anything else (the same position played differently by Forge, or a hook that is not about the attack)

For each file: the tables, how the pair ended (both won, only the candidate, only the base, neither) with the exact test on the
two middle counts, and from the same position, in each game: did an opponent the seat was sure to kill go out that turn, was the
seat out before its own next turn, was it left where one opponent alone was sure to kill it before then, how many attackers it
sent. Read-only; a session helper.
"""
import argparse, collections, gzip, json, math, os, sys

KINDS = {'turn', 'land', 'cast', 'resolve', 'combat', 'attack', 'block', 'damage', 'life', 'lost', 'mulligan', 'zone', 'ability', 'trigger'}


def load(root, entry, idx, arm):
    d = os.path.join(root, 'ab-' + entry, 'arm-' + arm, f'g{idx:04d}')
    rj = os.path.join(d, 'run.json')
    if not os.path.exists(rj):
        return None
    run = json.load(open(rj))
    g = run['games'][0]
    evf = os.path.join(d, 'games', os.path.basename(g['events']))
    if not os.path.exists(evf):
        evf += '.gz'
        if not os.path.exists(evf):
            return None
    op = gzip.open if evf.endswith('.gz') else open
    with op(evf, 'rt', encoding='utf-8') as f:
        evs = [json.loads(l) for l in f if l.strip()]
    return {'evs': [e for e in evs if e['e'] in KINDS], 'ids': {x['seat']: x['id'] for x in run['decks']},
            'winner': next((p['seat'] for p in g['players'] if p.get('won')), None)}


def exact(a, b):
    n = a + b
    if not n:
        return 1.0
    pr = [math.comb(n, k) / 2 ** n for k in range(n + 1)]
    return min(1.0, sum(q for q in pr if q <= pr[a] * (1 + 1e-9)))


def danger(d, state):
    n = d.get('permanents')
    if n is None:
        st = state.get(d['seat']) or {}
        n = st.get('bf', 0) - st.get('lands', 0)
    return d['life'] + 2 * n


def after(evs, focus, t):
    """What became of the seat between turn t and its own next turn."""
    lost = {x['seat']: x['t'] for x in evs if x['e'] == 'lost'}
    nxt = next((x['t'] for x in evs if x['e'] == 'turn' and x.get('seat') == focus and x['t'] > t), None)
    exposed = False
    for x in evs:
        if x['e'] == 'combat' and x['t'] > t and (nxt is None or x['t'] < nxt) and x.get('seat') != focus:
            for d in x.get('defenders') or []:
                if d['seat'] == focus and d['life'] > 0 and d['through'] >= d['life']:
                    exposed = True
    dead = focus in lost and lost[focus] >= t and (nxt is None or lost[focus] < nxt)
    sent = sum(1 for x in evs if x['e'] == 'attack' and x['t'] == t and x.get('seat') == focus
               for at in x.get('attacks') or [] if at.get('defender_seat') is not None)
    return lost, dead, exposed, sent


def read(root, base, cand, deck, tables, arm):
    rows = []
    for idx in range(1, tables + 1):
        a, b = load(root, base, idx, arm), load(root, cand, idx, arm)
        if a is None or b is None:
            rows.append({'deck': deck, 'idx': idx, 'file': 'missing'})
            continue
        focus = next(s for s, i in a['ids'].items() if i == deck)
        ea, eb = a['evs'], b['evs']
        i = 0
        while i < min(len(ea), len(eb)) and ea[i] == eb[i]:
            i += 1
        wa, wb = a['winner'] == focus, b['winner'] == focus
        r = {'deck': deck, 'idx': idx, 'outcome': 'both' if wa and wb else 'cand_only' if wb else 'base_only' if wa else 'neither'}
        if i == len(ea) == len(eb):
            r['file'] = 'identical'
            rows.append(r)
            continue
        xa = ea[i] if i < len(ea) else None
        xb = eb[i] if i < len(eb) else None
        own = [x for x in (xa, xb) if x is not None and x['e'] == 'attack' and x.get('seat') == focus]
        if not own:
            r['file'] = 'other'
            r['t'] = (xb or xa).get('t')
            rows.append(r)
            continue
        t = own[0]['t']
        state = {}
        cb = None
        for x in eb[:i]:
            if x['e'] == 'turn':
                state = {s['seat']: s for s in x.get('state') or []}
            elif x['e'] == 'combat' and x.get('seat') == focus and x['t'] == t:
                cb = x
        defs = [d for d in (cb or {}).get('defenders') or [] if d['life'] > 0]
        kill = [d for d in defs if d['through'] >= d['life']]
        if not kill:
            stood = 'nobody'
        elif len(defs) == 1:
            stood = 'last'
        else:
            top = max(danger(d, state) for d in defs)
            stood = 'top' if any(danger(d, state) == top for d in kill) else 'lesser'
        la, dead_a, exp_a, sent_a = after(ea, focus, t)
        lb, dead_b, exp_b, sent_b = after(eb, focus, t)
        r.update({'file': 'attack', 'stood': stood, 't': t, 'opponents': len(defs),
                  'base': {'kill': any(la.get(d['seat']) == t for d in kill), 'dead': dead_a, 'exposed': exp_a, 'sent': sent_a},
                  'cand': {'kill': any(lb.get(d['seat']) == t for d in kill), 'dead': dead_b, 'exposed': exp_b, 'sent': sent_b}})
        rows.append(r)
    return rows


def line(name, g, bn, cn):
    c = collections.Counter(r['outcome'] for r in g if 'outcome' in r)
    s = f"  {name:22} {len(g):5} tables: both {c['both']:4}, only {cn} {c['cand_only']:3}, only {bn} {c['base_only']:3}, neither {c['neither']:4}"
    if c['cand_only'] or c['base_only']:
        s += f"   exact test {exact(c['cand_only'], c['base_only']):.4f}"
    return s


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('root')
    ap.add_argument('variant')
    ap.add_argument('decks', nargs='+')
    ap.add_argument('--base', help='compare DECK@BASE with DECK@VARIANT; without it the base is the shipped playbook (ab-DECK)')
    ap.add_argument('--arm', default='playbook')
    ap.add_argument('--tables', type=int, default=200)
    ap.add_argument('--by-deck', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    bn, cn = (a.base or 'shipped'), a.variant
    rows = []
    for d in a.decks:
        rows += read(a.root, d + ('@' + a.base if a.base else ''), d + '@' + a.variant, d, a.tables, a.arm)
    files = collections.defaultdict(list)
    for r in rows:
        files[r['file'] if r['file'] != 'attack' else 'attack: ' + r['stood']].append(r)
    order = ['identical', 'other', 'attack: last', 'attack: top', 'attack: lesser', 'attack: nobody', 'missing']
    print(f"{len(a.decks)} decks, {len(rows)} tables: {cn} beside {bn}; the two games of a table, filed by the first event that differs")
    for k in order:
        if files.get(k):
            print(line(k, files[k], bn, cn))
    att = [r for r in rows if r['file'] == 'attack']
    print(line('attack, all', att, bn, cn))
    print(line('every table', [r for r in rows if 'outcome' in r], bn, cn))
    print()
    print("From the same position (the turn of the first difference, the seat's own attack): in each game, tables on which an opponent it was sure to kill went out that turn;")
    print("the seat was out before its own next turn; it was left where one opponent alone was sure to kill it before then; attackers sent")
    for k in order:
        g = [r for r in files.get(k, []) if r['file'] == 'attack']
        if not g:
            continue
        f = lambda side: (f"kill {sum(r[side]['kill'] for r in g):4}, out {sum(r[side]['dead'] for r in g):4}, open {sum(r[side]['exposed'] for r in g):4}, "
                          f"attackers {sum(r[side]['sent'] for r in g) / len(g):.1f}")
        print(f"  {k:16} {len(g):5} tables | {cn}: {f('cand')} | {bn}: {f('base')}")
    if att:
        f = lambda side: (f"kill {sum(r[side]['kill'] for r in att):4}, out {sum(r[side]['dead'] for r in att):4}, open {sum(r[side]['exposed'] for r in att):4}, "
                          f"attackers {sum(r[side]['sent'] for r in att) / len(att):.1f}")
        print(f"  {'attack, all':16} {len(att):5} tables | {cn}: {f('cand')} | {bn}: {f('base')}")
    if a.by_deck:
        print()
        for d in a.decks:
            print(line(d + ', attack', [r for r in att if r['deck'] == d], bn, cn))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            summary = {k: dict(collections.Counter(r['outcome'] for r in g if 'outcome' in r), tables=len(g)) for k, g in files.items()}
            summary['attack, all'] = dict(collections.Counter(r['outcome'] for r in att), tables=len(att),
                                          **{f'{side}_{k}': sum(r[side][k] for r in att) for side in ('base', 'cand') for k in ('kill', 'dead', 'exposed', 'sent')})
            for k, g in files.items():
                if k.startswith('attack: '):
                    summary[k].update({f'{side}_{x}': sum(r[side][x] for r in g) for side in ('base', 'cand') for x in ('kill', 'dead', 'exposed', 'sent')})
            json.dump({'kind': 'first-difference', 'base': bn, 'candidate': cn, 'decks': a.decks, 'files': summary, 'tables': rows}, f, indent=0)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
