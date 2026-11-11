# playbook/variants/

Candidate playbooks and drafts, one file each, played with `runner/ab.py --data` or as `deck@name` in the `ab-run` queue
(`playbook/README.md`, `variants/`). What each one is, and what came of it (DESIGN.md §22 has the numbers and the runs;
`demo-data/ab/` the rollups). A shipped playbook lives in `playbook/precons/<deck>.json`; the file here is the candidate
it came from, kept as the record of what was measured.

| File | Status | What was measured |
|---|---|---|
| `counter-intelligence-draft.json` | draft, next in line | goldfish +0.44 turns over stock; idle tap abilities listed in DESIGN §22 and docs/upstream.md |
| `goblin-storm-draft.json` | draft | goldfish 11.40 turns, the same as stock; shipped rules 2.0 turns faster |
| `goblin-storm-pressure2.json` | measured, not shipped | run #5 tables: 28 wins |
| `goblin-storm-pressure3.json` | measured, not shipped | run #5 tables: 32 wins (shipped v2 40, stock 18) |
| `goblin-storm-table.json` | measured, not shipped | run #5 tables: 28 wins; the lost-board rules cost four wins |
| `goblin-storm-zadahold.json` | measured, not shipped | run #5 tables: 39 wins; the Zada hold is worth seven on top of pressure |
| `goblin-storm-zadawide.json` | SHIPPED as goblin-storm version 3 | run #5 tables: 48 wins (v2 40, stock 18); a lean over v2, exact test 0.27. Confirmed on tables of its own (run #17): 48 against stock's 18 again |
| `hail-caesar-caesar.json` | goldfish and duels | trigger with a token, pressure: 10.82 turns; 33 of 60 duels (stock 22) |
| `hail-caesar-caesar-any.json` | measured, not shipped | trigger always, pressure: run #6 tables 45 wins (stock 34) |
| `hail-caesar-caesar-tok-wide.json` | SHIPPED as hail-caesar version 3 | run #6 tables 51 wins (stock 34); confirmed in a second run of new games, 42 against 27 |
| `hail-caesar-caesar-wide.json` | measured, not shipped | trigger always, go-wide: 44 wins |
| `hail-caesar-cast.json` | goldfish only | cast rules, pressure, no trigger rule: 11.45 turns (stock 12.47) |
| `hail-caesar-cast-wide.json` | measured, not shipped | no trigger rule, go-wide: 41 wins |
| `hail-caesar-draft.json` | draft | goldfish +0.23 turns over stock (nothing) |
| `quick-draw-draft.json` | draft | goldfish +0.97 turns over stock |
| `quick-draw-spells.json` | measured, not shipped | goldfish 11.72 against 13.72; 200 tables 38 wins against stock 31 (exact test 0.42); 17 of 60 duels against 14 |
| `science-draft.json` | draft | goldfish 0.23 turns slower than stock |
| `science-lab.json` | measured, not shipped | goldfish +0.35 turns; 200 tables 15 wins against stock 14 |
| `tinker-time-draft.json` | draft | goldfish +0.53 turns over stock; nothing more found without opponents |
| `token-triumph-cast.json` | SHIPPED as token-triumph version 3 | run #6 tables: 67 wins (stock 43). Confirmed on tables of its own (run #17): 56 against stock's 35 |
| `token-triumph-cast2.json` | measured, not shipped | 66 wins against the shipped 67: nothing |
| `token-triumph-castafter.json` | measured, not shipped | 58 wins |
| `token-triumph-castpressure.json` | measured, not shipped | 60 wins |
| `token-triumph-draft.json` | draft | goldfish +0.05 turns over stock (nothing) |
| `tricky-terrain-draft.json` | draft | goldfish +1.2 turns over stock (27 games) |
| `tricky-terrain-lands.json` | measured, not shipped | the shipped rules under pressure: 37 wins of 200 (stock 30, go-wide 48) |
| `tricky-terrain-lands-wide.json` | SHIPPED as tricky-terrain (first playbook) | 200 new tables: 48 wins (stock 30); its curated key cards add nothing (50) |

Keep this table current when a candidate is added, measured or shipped: it is what stops the next session
measuring a dead end twice.
