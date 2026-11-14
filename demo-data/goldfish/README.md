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
`wretched-ranks-seeds-11101-11140.json` (`wretched-ranks-gisa.json`: 9.85 against 10.63 on the 38 seeds both arms won);
`sultai-arisen-seeds-14101-14140.json` (`sultai-arisen-graves.json`: 12.15 against 12.65, not sent to the tables);
`limit-break-seeds-12101-12140.json` (`limit-break-cloud.json`: 11.07 against 11.03, nothing), `limit-break-fix-seeds-12101-12140.json` and
`limit-break-fix-seeds-12201-12240.json` (the same file after the controller stopped re-equipping what Cloud already wears: 10.65 against 11.03 on the same seeds, 10.28 against 10.85 on fresh ones);
`enduring-enchantments-seeds-16101-16140.json` (`enduring-enchantments-nyx.json`: 10.95 against 12.82 on the 32 seeds both arms won);
`eldrazi-incursion-seeds-15101-15140.json` (`eldrazi-incursion-ulalek.json`: 10.42 against 11.85 on the 38 seeds both arms finished).

`2026-11-13/`: the owner's table (DESIGN §30), ten precons, validation pairs on 40 seeds the rules had not seen (`runner/hands.py compare`; the playbook each run recorded was checked rule for rule against the candidate file; the paired gain is over the seeds both arms finished):
`blight-curse-seeds-21101-21140.json` (`playbook/variants/blight-curse-wretch.json`: 12.56 turns against stock's 13.53, +1.06 on 35 seeds, 95% +0.45 to +1.67; 39 games of 40 finished against 36);
`veloci-ramp-tor-seeds-22101-22140.json` (`veloci-ramp-tor-stampede.json`: 10.03 against 11.35, +1.32, +0.97 to +1.68);
`mutant-menace-seeds-23101-23140.json` (`mutant-menace-mothman.json`: 10.43 against 11.54, +1.18 on 39 seeds, +0.54 to +1.81);
`squirreled-away-seeds-24101-24140.json` (`squirreled-away-acorns.json`: 10.03 against 11.38, +1.35, +0.98 to +1.72);
`revenant-recon-seeds-25101-25140.json` (`revenant-recon-mirko.json`: 12.18 against 13.08, +0.90 on 39 seeds, +0.54 to +1.26);
`blood-rites-seeds-26101-26140.json` (`blood-rites-demons.json`: 10.97 against 12.07, +1.10, +0.75 to +1.45);
`death-toll-seeds-27101-27140.json` (`death-toll-winter.json`, version 2: 10.13 against 12.03, +1.87 on 38 seeds, +1.30 to +2.44; these rules were changed after the validation games of the first set had been seen, so this pair is not unseen) and
`death-toll-first-rules-seeds-27101-27140.json` (the first set of rules: 10.16 against 12.03, +1.84 on 38 seeds, +1.25 to +2.44);
`miracle-worker-seeds-28101-28140.json` (`miracle-worker-veil.json`: 12.36 against 13.97, +1.62 on 37 seeds, +1.16 to +2.09; Forge hung to the 900 s clock on one seed in both arms and on two more under stock);
`ahoy-mateys-seeds-29101-29140.json` (`ahoy-mateys-crew.json`: 9.05 against 10.12, +1.07, +0.74 to +1.41);
`deadly-disguise-seeds-30101-30140.json` (`deadly-disguise-veil.json`: 11.13 against 11.95, +0.82 on 38 seeds, +0.45 to +1.18).
Seed blocks used by this batch: 21001 to 30140 (in each thousand the audit from x001, tuning from x021, validation x101 to x140).

`2026-11-14/`: the second pass of the owner's first four decks (DESIGN §30) on the validation seeds of their engine-only candidates, to see whether the added rules cost the engine its speed (A is the engine-only candidate's validation run of 2026-11-13, B the second-pass candidate on the same seeds; these seeds are not unseen for the base, and in goldfish the answer rules have nothing to fire at):
`blight-curse-answers-on-wretch-seeds-21101-21140.json` (12.49 turns against 12.56: 0.08 faster, 95% -0.20 to +0.35);
`mutant-menace-answers-on-mothman-seeds-23101-23140.json` (10.45 against 10.43: 0.03 slower, -0.32 to +0.27);
`squirreled-away-answers-on-acorns-seeds-24101-24140.json` (10.22 against 10.03: 0.20 slower, -0.49 to +0.09);
`ahoy-mateys-answers-on-crew-seeds-29101-29140.json` (8.82 against 9.05: 0.23 faster, +0.08 to +0.37).
