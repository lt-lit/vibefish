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
