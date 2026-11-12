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

`2026-11-11/`: the three other first bots, stock against the candidate playbook each went to the tables with (DESIGN.md
§22), snapshot 2026-11-10, 40 games a run: Hail, Caesar (`playbook/variants/hail-caesar-caesar-any.json`: cast rules, pressure
attack, Caesar's attack trigger accepted every time; 10.10 turns against 12.47), Token Triumph
(`token-triumph-cast.json`; 9.05 against 10.38), Tricky Terrain (`tricky-terrain-lands.json`, version 3; 10.64 against 13.39, with
seven stock games and one playbook game not finished: the turn cap, and for one stock game the clock).
Quick Draw (`quick-draw-spells.json`; 11.72 turns against 13.72) was added the same day, the fifth deck with a candidate.
`hail-caesar-shipped-seeds-6001-6040.json` is Hail, Caesar's playbook as it shipped (version 3: the trigger only with a token, go-wide): 11.07 turns against 12.47.
`goblin-storm-v3-seeds-9001-9100.json` and `tricky-terrain-shipped-seeds-8001-8040.json` are the two playbooks as they shipped on 2026-11-11 (Goblin Storm version 3 with the Zada hold: 9.20 turns against 11.40 on the block of 100 seeds; Tricky Terrain under go-wide: 10.97 against 13.39).

The batch of 2026-11-11 (DESIGN.md §24), four decks written at once, each validated on 40 seeds its rules had not seen:
`counter-intelligence-seeds-2101-2140.json` (`playbook/variants/counter-intelligence-charge.json`: 11.62 turns against 13.45) and
`counter-intelligence-draft-seeds-2101-2140.json` (the mechanical draft on the same seeds: 13.40, nothing);
`deep-clue-sea-seeds-3201-3240.json` (`deep-clue-sea-sleuth.json`: 9.70 against 12.57; stock casts Farewell on its own board in 12 of the 40);
`food-and-fellowship-seeds-2401-2440.json` (`food-and-fellowship-eat.json`: 10.30 against 11.38);
`planeswalker-party-seeds-2701-2740.json` (`planeswalker-party-guff.json`: 10.65 against 13.07) and
`planeswalker-party-forge-attack-seeds-2701-2740.json` (the same rules with Forge's own attack: 11.32). In these files the
playbook's `file` is the name of the copy that was played; the rules are those of the variant named here (checked rule for rule).
Goldfish flatters a planeswalker deck in particular: nobody attacks its planeswalkers.
Seed blocks used by this batch: 2001 to 2140, 2301 to 2440, 2601 to 2740, 3101 to 3240 (audit, tuning, validation).

`2026-11-12/`: the batch of 2026-11-12, validation pairs on 40 seeds the rules had not seen (`runner/hands.py compare`):
`elven-council-seeds-13101-13140.json` (`playbook/variants/elven-council-grove.json`: 10.47 turns against 13.07);
`wretched-ranks-seeds-11101-11140.json` (`wretched-ranks-gisa.json`: 9.85 against 10.63 on the 38 seeds both arms won).
