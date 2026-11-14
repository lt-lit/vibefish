<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Deadly Disguise: answers candidate and repair of the base (`answers`, version 2)

**File:** `playbook/variants/deadly-disguise-answers.json`. Its rules, triggers and attack are identical to the file my last local run played (I checked them against that run's `run.json`). The only thing that changed afterwards is the `notes` text, which the harness does not read.

**What veil got wrong, from the 200 exam tables.** Veil's rule 6 cast every morph and disguise card face up whenever it could afford to. Face-down casts fell from 4.0 a game under stock to 1.8. Den Protector, Hidden Dragonslayer, Ainok Survivalist, Printlifter Ooze, Nervous Gardener, Master of Pearls, Broodhatch and Deathmist Raptor went down face up 27 to 39 times each, where stock put them down face down 30 to 47 times. That throws away their turn-up triggers, including two removal effects. Stock's 27 wins averaged 5.6 face-down casts and its losses 3.8. On top of that, veil's rules that fire every turn (rule 6 and the mana sinks) starved every card no rule named.

### 1. Answer cards in the exam (seen / cast / in hand at a loss)
| Card | stock | veil |
|---|---|---|
| Austere Command | 45/18/18 | 48/5/31 |
| Dusk // Dawn | 37/19/8 | 42/5/21 |
| Fell the Mighty | 46/38/6 | 50/9/30 |
| Decimate | 58/37/14 | 55/11/30 |
| Showstopping Surprise | 48/15/26 | 49/8/30 |
| Chaos Warp | 45/39/0 | 51/41/5 |
| Path to Exile | 56/50/1 | 56/52/1 |
| Unexplained Absence | 55/38/9 | 63/38/12 |

### 2. Changes (rule numbers are in the new file)
- **Removed veil rule 6.** All morph and disguise cards now go to Forge, which decides face down or face up. The rule format cannot cast a card face down.
- **Rule 8 `{"forge":"unnamed"}`.** It sits after ramp (4), Kaust (5), the engines (6) and the Projektor tap (7), and before the payoffs (9), Boltbender (10) and the sinks (11 to 14). Forge's own logic then picks the moment and targets for the removal and casts the morphs face down. The engines are each cast once, and Duskana wants face-down creatures on the battlefield first.
- **Panoptic Projektor's tap** (veil rule 4) now comes before the forge rule, so its cost reduction is there when Forge casts face down.
- **Neheb** is out of the payoff rule and left to Forge.
- **Rules 1–2, Austere Command:** cast when an opponent has 7 or more creatures, more power than us, and we have 4 creatures or fewer; or when an opponent has more power than us and could kill us next turn (`threat >= life`).
- **Rule 3, Dusk:** cast when an opponent has more power than us, `threat >= life`, and 6 creatures or fewer.
- **Rule 10, Boltbender:** cast only when `mana <= 3`. At that point the face-up spell is unaffordable, so the rule casts it face down.
- Every other veil rule, the triggers and the attack are unchanged and keep their order.
- **Tried and dropped:** the forge rule placed above the engines. In run 1 Projektor sat in hand for four turns while Forge spent the mana on face-down creatures.

### 3. Local tables (16 games, 0 wins: far too few to mean anything)
- **Face-down casts:** 5.9 a game in run 1 (forge rule above the engines) and 3.5 a game in run 2 (the final order). The exam had stock at 4.0 and veil at 1.8.
- **Rules firing:** Austere Command was cast twice by rule 1. One cast was countered by Swan Song. The other chose the artifacts and mana value 4 or more modes and destroyed 11 opposing permanents and none of ours. Rule 3 (Dusk) never fired. Boltbender went down face down twice, both times by rule 10.

**Cast-LESS cards, drawn / cast** (run 1; run 2, the final file):
| Card | Run 1 | Run 2 | What I did |
|---|---|---|---|
| Fell the Mighty | 1/0 | 1/0 | Left to the forge rule. A named rule cannot force a cast: Forge must agree to its target. |
| Neheb | 1/1 | not drawn | Taken out of the payoff rule, left to Forge. |
| Decimate | 1/1 | 1/1 | Forge rule. |
| Jeska's Will | 2/1 | 4/2 | Forge rule. |
| Austere Command | 2/2 | 1/0 | Rules 1–2. |
| Return of the Wildspeaker | 1/1 | 2/2 | Forge rule. |
| Ohran Frostfang | 3/1 | 1/0 | Still in the payoff rule, now after the forge rule. |
| Showstopping Surprise | 3/2 | 1/1 | Forge rule. |

**Backfire risk:** Dusk was drawn in 4 run-2 losses and never cast. In one of them the seat died at 2 life holding Dusk and Fell the Mighty against 7 creatures. Rule 3's cap of 6 creatures failed and Forge declined Fell the Mighty. That cap is the first thing to drop if Dusk keeps sitting in hand at the 200 tables. I did not change it, because I had used the 16-game cap and could not play the extra games a rule change requires.

### 4. What the rule format cannot express
- Casting a card face down, apart from the mana trick used for Boltbender.
- Turning a card face up (a static action) or using Kaust in combat.
- Choosing Austere Command's modes. Forge's AI picks them because the rule casts it without asking Forge.
- Any condition on opposing creatures' power or toughness, which Dusk and Fell the Mighty need. The logs do not show creature power either, so I could not set the thresholds from evidence.
- Instant-speed use of Showstopping Surprise.

### 5. Recommendation
Send it to the 200 tables against stock, with veil on the same tables (seed 20261280). The main bet is the restored face-down play and the removal, not the answer rules.

**Not touched, flagged for the 200 tables:** Mirror Entity's rule (X = all mana, minimum 3, first main phase) never fired in my 16 games and fired about 25 times in veil's 200, so I left it.

Scratch work is in `<scratch>/batch/answers-deadly-disguise/`: the runs are in `results/t1` and `results/t2`, the playtest reports are `t1-playtest.*` and `t2-playtest.*`, and the scripts are in `bin/`.
