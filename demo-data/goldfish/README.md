# demo-data/goldfish

Paired goldfish comparisons (`runner/hands.py compare A B --out`, kind `goldfish-pair`, DESIGN.md §21): one deck
against three do-nothing opponents, played twice on the same seeds, once by stock Forge AI (`a`) and once under the
deck's playbook (`b`). Each file holds both runs' settings (build, clock, turn cap, the playbook as it was), the
kill-turn summary of each, every game's seed and kill turn (`per_game`), and the paired difference with its 95%
interval. The dashboard does not read these; the numbers are summarised in DESIGN.md.

A kill turn is the deck's own turn on which the last of the three opponents died. Goldfish measures whether the
seat runs its own deck; it says nothing about blocking, removal or being attacked.

`2026-11-10-goblin-storm/`: Goblin Storm, stock against its playbook version 2 (cast rules and the go-wide attack with
`spread`), snapshot 2026-11-10, 100 games a run. `seeds-9001-9100.json` is the block that was not looked at before the
rules were final; `seeds-7001-7100.json` the first check, four of whose games were read to correct the rules;
`seeds-4201-4212.json` the twelve games the rules were written from. Those three were played with the attack aimed at
the lowest life; `seeds-9001-9100-as-shipped.json` is the untouched block again with the attack aimed at the highest
life, the playbook file as it ships (DESIGN.md §21 has why). The stock runs of the last two were played before
the harness version stamp moved to 0.3.0 (they say 0.2.0); nothing that changed since touches a seat without a
playbook.
