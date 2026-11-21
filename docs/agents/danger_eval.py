#!/usr/bin/env python3
"""danger_eval.py RUN_DIR... [--arm ARM]: is there a better judgement of who goes on to win than life + 2 x nonland permanents?
A session helper (DESIGN.md section 34; needs numpy).

From the `turn` events of finished games (harness 0.4.0 or later for a seat's creatures and their power): for every turn with
three or four players alive, each seat's life, nonland permanents, lands, cards in hand, creatures, their power, the damage it
has dealt and taken so far and whether its commander is out of the command zone. It prints, by the round of the game, how
often the one seat that is highest on a score is the game's eventual winner: single counts, hand-made sums, and a conditional
logit over the seats alive fitted on the odd games, everything scored on the even games. `leader.py` is the same question on
older logs with fewer counts.
"""
import argparse, glob, gzip, json, os, sys
import numpy as np

FE = ('life', 'nl', 'lands', 'hand', 'creatures', 'power', 'dealt', 'cmd_out', 'gy', 'taken')
NAMES = ('game', 't', 'round', 'alive', 'seat', 'active') + FE + ('won',)


def states(run_dirs, arm):
    rows = []
    gi = 0
    for root in run_dirs:
        for rj in sorted(glob.glob(os.path.join(root, '**', 'run.json'), recursive=True)):
            if arm and f'{os.sep}arm-{arm}{os.sep}' not in rj:
                continue
            run = json.load(open(rj))
            for g in run['games']:
                if not g.get('events'):
                    continue
                evf = os.path.join(os.path.dirname(rj), 'games', os.path.basename(g['events']))
                if not os.path.exists(evf):
                    evf += '.gz'
                    if not os.path.exists(evf):
                        continue
                winner = next((p['seat'] for p in g['players'] if p.get('won')), None)
                if winner is None:
                    continue
                gi += 1
                dealt = {}; taken = {}
                op = gzip.open if evf.endswith('.gz') else open
                with op(evf, 'rt', encoding='utf-8') as f:
                    for line in f:
                        if '"e":"damage"' in line:
                            e = json.loads(line)
                            if e.get('source_seat') is not None and e['source_seat'] != e['seat']:
                                dealt[e['source_seat']] = dealt.get(e['source_seat'], 0) + e['amount']
                                taken[e['seat']] = taken.get(e['seat'], 0) + e['amount']
                        elif '"e":"turn"' in line:
                            e = json.loads(line)
                            st = [s for s in e['state'] if s['alive']]
                            if len(st) < 3:
                                continue
                            for s in st:
                                rows.append((gi, e['t'], e['own_turn'], len(st), s['seat'], e['seat'] == s['seat'],
                                             s['life'], s['bf'] - s['lands'], s['lands'], len(s['hand']), s.get('creatures', 0), s.get('power', 0),
                                             dealt.get(s['seat'], 0), 0 if s.get('cmd') else 1, s.get('gy', 0), taken.get(s['seat'], 0),
                                             s['seat'] == winner))
    return np.array(rows, dtype=np.float64)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('run_dirs', nargs='+')
ap.add_argument('--arm', default='playbook')
args = ap.parse_args()
a = states(args.run_dirs, args.arm)
names = list(NAMES)
col = {n: a[:, i] for i, n in enumerate(names)}
game = col['game'].astype(int); t = col['t'].astype(int)
key = game * 1000 + t                      # one group per turn event
order = np.argsort(key, kind='stable')
a = a[order]; col = {n: a[:, i] for i, n in enumerate(names)}
game = col['game'].astype(int); t = col['t'].astype(int); key = game * 1000 + t
uniq, start = np.unique(key, return_index=True)
size = np.diff(np.append(start, len(key)))
grp = np.repeat(np.arange(len(uniq)), size)
won = col['won']
has_winner = np.add.reduceat(won, start) > 0        # the winner is among the alive seats (always true unless a draw)
rnd = col['round'][start]
ggame = game[start]
bucket = np.where(rnd <= 3, 0, np.where(rnd <= 6, 1, np.where(rnd <= 9, 2, 3)))
BN = ('r1-3', 'r4-6', 'r7-9', 'r10+')

def top1(score, mask_groups):
    # strict top seat per group; ties left out
    mx = np.maximum.reduceat(score, start)
    is_top = score == mx[grp]
    ntop = np.add.reduceat(is_top.astype(float), start)
    hit = np.add.reduceat((is_top * won), start)
    ok = (ntop == 1) & mask_groups
    return hit[ok].sum(), ok.sum()

def report(label, score, mask):
    out = []
    for b in range(4):
        h, n = top1(score, mask & (bucket == b))
        out.append(f'{100*h/max(1,n):5.1f}%')
    h, n = top1(score, mask)
    print(f'  {label:44} ' + '  '.join(out) + f'   all {100*h/max(1,n):5.1f}%  (n {int(n)})')

test = (ggame % 2 == 0)
train = ~test
print('games', len(np.unique(game)), 'turn states', len(uniq), ' chance', f'{(1/size[has_winner]).mean()*100:.1f}%')
print('top seat goes on to win, test half (even games):', '  '.join(BN))
F = {n: col[n] for n in ('life', 'nl', 'lands', 'hand', 'creatures', 'power', 'dealt', 'cmd_out', 'gy', 'taken')}
cands = {
 'life': F['life'], 'nl': F['nl'], 'power': F['power'], 'creatures': F['creatures'], 'hand': F['hand'], 'lands': F['lands'], 'dealt': F['dealt'],
 'life+2*nl': F['life'] + 2*F['nl'],
 'life+3*nl': F['life'] + 3*F['nl'],
 'life+power': F['life'] + F['power'],
 'life+2*nl+power': F['life'] + 2*F['nl'] + F['power'],
 'life+nl+power': F['life'] + F['nl'] + F['power'],
 'life+2*nl+hand': F['life'] + 2*F['nl'] + F['hand'],
 'life+2*nl+2*hand': F['life'] + 2*F['nl'] + 2*F['hand'],
 'life+2*nl+lands': F['life'] + 2*F['nl'] + F['lands'],
 'life+2*nl+2*lands': F['life'] + 2*F['nl'] + 2*F['lands'],
 'life+2*nl+power+hand': F['life'] + 2*F['nl'] + F['power'] + F['hand'],
 'life+2*nl+power+2*lands': F['life'] + 2*F['nl'] + F['power'] + 2*F['lands'],
 'life+2*creatures+power': F['life'] + 2*F['creatures'] + F['power'],
 'life+2*nl+dealt/2': F['life'] + 2*F['nl'] + 0.5*F['dealt'],
}
gt = test
for k, v in cands.items():
    report(k, v, gt & has_winner)

# conditional logit: P(seat wins) = softmax over alive seats of w.x ; fitted per round bucket and overall
X = np.stack([F[n] for n in ('life', 'nl', 'lands', 'hand', 'creatures', 'power', 'dealt', 'cmd_out')], axis=1)
mu = X.mean(0); sd = X.std(0) + 1e-9
Z = (X - mu) / sd
def fit(mask_g, iters=400, lr=0.5, l2=1e-3):
    w = np.zeros(Z.shape[1])
    rows = mask_g[grp]
    for _ in range(iters):
        s = Z @ w
        s = s - np.maximum.reduceat(s, start)[grp]
        e = np.exp(s)
        p = e / np.add.reduceat(e, start)[grp]
        g = ((p - won)[:, None] * Z)[rows].sum(0) / mask_g.sum() + l2 * w
        w -= lr * g
    return w
w_all = fit(train & has_winner)
print('fitted on the odd games (weights per raw unit, life = 1):')
raw = w_all / sd
print('   ' + ', '.join(f'{n} {raw[i]/raw[0]:+.2f}' for i, n in enumerate(('life', 'nl', 'lands', 'hand', 'creatures', 'power', 'dealt', 'cmd_out'))))
report('fitted (all rounds)', Z @ w_all, gt & has_winner)
for b in range(4):
    wb = fit(train & has_winner & (bucket == b))
    rb = wb / sd
    h, n = top1(Z @ wb, gt & has_winner & (bucket == b))
    print(f'  fitted on {BN[b]:6}: top goes on to win {100*h/max(1,n):5.1f}% (n {int(n)}); weights: ' + ', '.join(f'{nm} {rb[i]/abs(rb[0]):+.2f}' for i, nm in enumerate(('life', 'nl', 'lands', 'hand', 'creatures', 'power', 'dealt', 'cmd_out'))))
