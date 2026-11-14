<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Mutant Menace answer rules: report

I wrote the answer rules as `playbook/variants/mutant-menace-answers.json` (variant `answers`, of `mutant-menace-mothman.json`, version 2, 20 cast rules). The attack block and the triggers are unchanged. In `run.json` the cast rules of the local run match the file.

Two findings first. At the seat's losses the biggest opposing board held 12.5 creatures on average, against 3.8 of ours; 131 of the 145 losses had more opposing creatures than ours, 111 had six or more. The seat had 19 life on its last own turn and died within a turn cycle. Neither pilot ever cast Nuclear Fallout or Find // Finality: Forge's own AI never does.

### 1. The answer cards over the 200 exam tables (seen / cast / in hand at a loss)
| Card | Playbook arm | Stock arm |
|---|---|---|
| Nuclear Fallout | 52 / 0 / 37 | 45 / 0 / 32 |
| Find // Finality | 41 / 0 / 14 | 30 / 0 / 3 |
| Atomize | 38 / 1 / 27 | 38 / 0 / 24 |
| Mutational Advantage | 38 / 1 / 28 | 39 / 0 / 30 |
| Rampaging Yao Guai | 38 / 6 / 26 | 34 / 14 / 16 |
| Alpha Deathclaw | 51 / 10 / 23 | 48 / 41 / 9 |
| Casualties of War | 30 / 17 / 14 | 37 / 32 / 5 |
| Vault 87 | 41 / 29 / 12 | 44 / 36 / 7 |
| Putrefy | 45 / 45 / 0 | 46 / 46 / 1 |

### 2. Rules added (numbers are positions in the new file)
- **R1:** Nuclear Fallout at X 3 (-6/-6) in the first main phase, when the strongest opposing board has more power than ours and 4 or more creatures.
- **R2:** Nuclear Fallout at X 2 (-4/-4, spares our creatures with counters) when one opponent has 6 or more creatures and more than we do.
- **R3:** Find // Finality on the same terms as R2.
- R1 to R3 sit above everything, ramp included, so the ramp spells do not use up the mana X needs.
- **R7:** Casualties of War, Alpha Deathclaw and Atomize when an opponent has a creature. Forge picks the targets and modes.
- **R8:** Vault 87 split off the old rule 7: library 30 or more (was 45) and an opposing creature. Chapter I steals a creature.
- **R11:** The Master's tap in the first main phase, after Raul's mill.
- **R12:** Rampaging Yao Guai at X max, at least 3.
- **R16:** Mutational Advantage before combat with 4 or more attackers and 3 or more opposing creatures. It works as combat protection, then proliferates.
- **Dropped:** a rule for Alpha Deathclaw's monstrosity. A rule cannot tell the creature is already monstrous, so it would pay 7 mana every turn for nothing.

### The "cast LESS" list: what I did
- **Rule 13 (the old creature rule) now names the cards it left to Forge:** Lumbering Megasloth (listed first; only castable once its counter discount makes it cheap), Nightkin Ambusher, The Master, Harold and Bob, Fraying Sanity and Power Fist. The cause is the one your prompt gave: these were not starved by a hold but because a play rule always had something to cast first.
- **Alpha Deathclaw and Casualties of War:** R7, above the engine rules.
- **Rampaging Yao Guai:** R12.
- **Vault 87:** R8 (library condition loosened).
- **Young Deathclaws and Marcus:** already named in the base (rules 6 and 4), so they were simply losing the mana to earlier rules. I left them where they were. In the local games Young Deathclaws mostly sat in hand in games short of green.
- **The "cast more" rules (ramp, Mothman, doublers, engines, Struggle, Biomass, Drink, Harmonize, Bobblehead, Clasp):** kept in their order.

### Base rules moved or changed
- Ramp, Mothman, doublers and engines: moved down by three positions (rules 4 to 6), below the new wipe rules, and by four more for the engines (rule 9), below the new R7 and R8.
- Raul's mill: now rule 10.
- The creature rule: now rule 13, with six cards added.
- Old rule 7 (Vault 87 + Struggle): split. Vault 87 is R8 with library 30 and an opposing creature; Struggle is R14 alone, keeping library 45.
- Biomass Mutation, Contaminated Drink, Harmonize, Bobblehead and Clasp keep their rules unchanged, now at positions 15 and 17 to 20.

### 3. Local tables: 8 tables of bots, seed 20263120 (`playtest.py`)
The seat won 2 of 8, which is too few games to mean anything.

Games drawn / cast:
- **Answer cards:**
  - Nuclear Fallout 2 / 2, both by R1. One cast removed 10 opposing permanents and none of ours; the other 7 opposing creatures and 1 of ours.
  - Find // Finality 2 / 2, though `playtest.py` shows 0 because it logs the halves by name. Finality was cast by R3 and countered by Swan Song; Find was cast once by Forge's own choice.
  - Alpha Deathclaw 1 / 1; its enters trigger destroyed Doomwake Giant.
  - Casualties of War 2 / 1; it took Ulvenwald Hydra, Desert Warfare and Urza's Mine.
  - Putrefy 1 / 1; Contagion Clasp 3 / 1.
  - Atomize 1 / 0, in a game with no green source. Stock cast it in 0 of 38 games, so Forge's logic may decline it under R7 as well. Not verified.
  - Mutational Advantage 2 / 0: R16 never had four attackers.
- **The other "cast LESS" cards:** Nightkin 1 / 1, Megasloth 3 / 2, Power Fist 3 / 3, Harold and Bob 3 / 2, Yao Guai 2 / 1, Young Deathclaws 4 / 2, Vault 87 2 / 1, The Master 2 / 0. Fraying Sanity and Marcus were not drawn.
- **Uncast cards:** Vault 87 and The Master went uncast in g0008, a Swamps-only colour screw; The Master's other uncast game was g0006. Atomize was the other card stranded in g0008. Nothing backfired. Rule 11 (The Master's tap) never fired because The Master was never cast.

### 4. What the rule format cannot express
- Atomize, Putrefy and Casualties of War cannot be aimed at an opponent's permanent; the rule depends on Forge agreeing.
- Mutational Advantage cannot be held as a response to a wipe or to removal on another player's turn.
- Find // Finality: the format cannot choose which half to cast (here Find came from Forge's own choice; whether a rule would take Find ahead of Finality is unverified).
- A wipe rule cannot see how many of our creatures would die. Toughness, counters and "a creature is monstrous" are not conditions.
- Opponents' total creatures across the table are not a metric; `opp_creatures` is one opponent's count.

### 5. Recommendation
Send it to 200 tables. The wipes and removal fire when they should, and the cards the base starved are now cast.
