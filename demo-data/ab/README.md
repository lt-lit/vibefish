# demo-data/ab

Paired A/B results for per-deck AI data (`runner/ab.py rollup`, DESIGN.md §19), one file per deck and run. The dashboard
does not read these yet; the numbers are summarised in DESIGN.md. Each file holds the arms' win rates with Wilson
intervals, the paired differences, and every game's seats, seed, winner and length.

`2026-11-10-ab-v1b/` is the v1 arms again on 100 new tables per deck (seed 20261110, `ab-run` #2), and
`2026-11-10-ab-v1-pooled/` pools each deck's two seeds into one 200-table measurement (`runner/ab.py pool`, kind `ab-pool`:
games keyed by run seed and table, the same statistics).

`2026-11-10-ab-v2/` is the CI playbook measurement (`ab-run` #3, DESIGN.md §20: arms stock, playbook, playbookdata on Token Triumph,
Goblin Storm and Hail, Caesar, seed 20261110).

`2026-11-10-ab-mcmax/` is the CI check of desktop-strength Monte Carlo (`ab-run` #4, DESIGN.md §19: Tricky Terrain, arms stock, mcmax,
mcmaxdata, seed 20261120), the first run started by `runner/queue/ab-run.json`.

Dated `*-local/` directories hold 40- to 100-table checks played on a session's machine rather than in Actions, named by
deck and the arms they ran; the same format, smaller.

`2026-11-10-local/goblin-storm-playbook-v2-*.json` are Goblin Storm's playbook version 2 (cast rules, DESIGN.md §21) on the
same 40 tables with the attack aimed at the lowest life, the highest life and the biggest board; the three share one
stock arm, and each file's `note` and `attack_target` say which it is. The playbook file ships with the highest life.

`2026-11-10-ab-v3/` is the CI measurement of Goblin Storm's playbook version 2 (`ab-run` #5, DESIGN.md §21: cast rules and the
go-wide attack aimed at the highest life; arms stock and playbook, 200 tables, seed 20261140, snapshot 2026-11-10): 40 wins
against 18, the first difference in this directory whose interval excludes zero.

`2026-11-11-ab-v4/` is the leader-first attack alone on the two other go-wide decks (`ab-run` #6, DESIGN.md §22: Token Triumph and
Hail, Caesar under playbooks that hold an attack policy and nothing else, go-wide aimed at the highest life with the split; arms
stock and playbook, 200 tables each, seed 20261141, snapshot 2026-11-10): Token Triumph 39 wins against stock's 43, Hail, Caesar 32
against 34. Whom the seat attacks does not move either deck by itself. The stock arms are the baseline that the cast-rule
variants of both decks are paired with (same seed, playbook arm only).

`2026-11-11-ab-v5/goblin-storm.json` joins four candidates for Goblin Storm (`ab-run` #7, playbook arm only) with run #5's stock and
version-2 arms on the same 200 tables (`runner/ab.py join`, kind `ab-join`, DESIGN.md §22): the pressure attack wins 32 (damage per
loss 3) and 28 (2) where the shipped go-wide attack wins 40; two rules for a lost board on top of pressure, 28; Zada held until she
can be aimed at, on top of pressure, 39. Every candidate beats stock's 18; none beats the shipped file.

`2026-11-11-local/` are checks on the session's machine, each a join of arms that share one stock arm: Goblin Storm at 40 tables
under five attack settings and in 60 duels, Token Triumph's three cast-rule candidates in 60 duels, Hail, Caesar's two trigger-rule
candidates in 60 duels (`runner/ab.py --opponents 1`).

`2026-11-11-ab-v6/token-triumph.json` joins Token Triumph's three cast-rule candidates (`ab-run` #8, playbook arm only) with run #6's
stock and attack-only arms on the same 200 tables: the cast rules under the go-wide attack win 67 where stock wins 43 (+12.0 points,
47 discordant pairs against 23, exact test 0.006), under the pressure attack 60, with everything but the anthems cast after
combat 58. The first became the deck's shipped playbook (version 3).

