<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Miracle Worker: answer rules and the starved cards (`miracle-worker-answers`, version 3)

The candidate is `playbook/variants/miracle-worker-answers.json`. It is built on `veil` version 2 and written from the 120 tables of exam #30 that were in. Local runs: t1 was 8 tables on seed 20263200 with an earlier draft; t2 was 8 tables on seed 20263201 with the final file. t2's `run.json` records the same `cast` object as the file (checked), so the file handed in is the file last played. The attack and triggers blocks are unchanged.

### 1. Answer cards in the exam (playbook arm; stock arm in brackets)
| Card | Drawn | Cast | In hand at a loss |
|---|---|---|---|
| Time Wipe | 25 (28) | 1 (8) | 17 (11) |
| Terminus | 20 (32) | 13 (24) | 4 (6) |
| The Eldest Reborn | 21 (28) | 14 (28) | 5 (0) |
| Timely Ward | 32 (33) | 9 (10), miracle only; flagged never-cast for Forge's AI | 10 (12) |
| Swords / Utter End / Cast Out / Return to Dust | 33 / 21 / 25 / 25 | 97% / 90% / 84% / 88% (about the same under stock) | 1 / 1 / 0 / 3 |
| Inkshield | 38 (31) | 18 (17) | 10 (9) |
| Sphere of Safety | 32 (25) | 25 (20) | 6 (3) |
| Doomwake Giant / Dream Eater | 32 / 26 | 28 / 20 | 3 / 5 |

**Why the candidate trails stock (37 against 42 wins):**
- **Starved cards.** On the turns the starved cards sat in hand with the lands to pay for them, the card cast instead was most often a recast of Aminatou. That happened on 8 of the turns Augury waited, 14 of Redress Fate's, 11 of Eldest Reborn's and 14 of Time Wipe's.
- **More attacks at the seat.** It drew 30% of the table's attackers against stock's 23%, took 39.8 combat damage a game against 30.1, and was first out in 34 of 80 losses against 25 of 76.
- **Aminatou attacks and dies more.** She attacked 257 times against 132 and left the battlefield 135 times against 91; 41 of those exits came on turns she attacked, against 14. She was cast 1.99 times a game against 1.23.

The attacks point to the go-wide attack. I left it alone as instructed.

### 2. Rules added
- **Rule 2:** Time Wipe or Terminus from hand when `threat >= life` and `opp_power > power`.
- **Rule 3:** the same in main2 with `threat >= life` and `opp_creatures >= 2`, whatever the power. Added after local game t1/g1: the seat died at 7 life holding Time Wipe with five lands, while its own power was the larger and its creatures had attacked.
- **Rule 4:** the same when an opponent has a board that kills in two swings: `opp_power >= 20`, more power than ours, four creatures or more.
- **Rule 5:** Aminatou's Augury while `library >= 20`, placed above Aminatou's recast.
- **Rule 7:** Timely Ward with `target` Aminatou, to make her indestructible.
- **Rule 9:** The Eldest Reborn when `opp_creatures >= 1`.
- **Rule 13:** `{"forge":"unnamed"}`, after the engine, Entreat and The Master of Keys and before the bodies list. Forge then chooses among the unnamed cards, which covers Redress Fate (no condition can judge the graveyard), the spot removal, the instants, Monologue Tax, Mirrormade and Auramancer. It also reaches the Rooms' door unlocks, which the base noted no activate rule could. In the trace it cast Utter End, Swords, Cast Out, Redress Fate, the Secret Arcade / Dusty Parlor and Cramped Vents / Access Maze unlocks, Portent, Brainstorm, Auramancer, Mirrormade and Brainstone, plus fetch-land activations.
- **Dropped:** a rule moving Sphere of Safety up. It was never played; I took it out before the first run because it is not starved (25 of 32 cast against stock's 20 of 25).

### Base rules changed
- **Aminatou** moved from 2nd to 6th, below the three wipe rules and Augury. Nothing else moved; the base's 10 rules keep their relative order.
- **Mind Flayer, the Shadow** added to the end of the bodies list. Neither pilot cast it in any of the 38 games it was drawn.
- **Sphere of Safety** is still in its original place.
- Nothing was removed.

### The "cast LESS" list (local 16 tables: drawn / cast)
- **Aminatou's Augury:** rule 5; 3 / 1. Held at 2 losses, in short games.
- **Redress Fate:** left to the forge rule; 3 / 2.
- **The Eldest Reborn:** rule 9; 2 / 2.
- **Time Wipe:** rules 2 to 4; 3 / 1. The one cast was rule 4 in t2/g4: it destroyed 10 of Quick Draw's creatures and 4 of Limit Break's against 2 of ours, and the seat won that game. The two holds were t1/g1 (before rule 3 existed) and t1/g4 (four lands, so it could not be paid for).
- **Otherworldly Gaze:** forge rule; 3 / 3.

### 3. Local tables
- **Wins:** 1 of 8 with the draft, 2 of 8 with the final file. These are too few games to mean anything.
- **Other answers (drawn / cast):** Utter End 6 / 6, Swords 3 / 3, Cast Out 2 / 2, Return to Dust 2 / 2, Timely Ward 2 / 2 (both on Aminatou), Arcane Denial 3 / 3, Inkshield 4 / 1, Sphere 5 / 2, Doomwake 4 / 3, Mind Flayer 4 / 0.
- **Terminus** was drawn once in t2 and not cast; rules 2 and 3 have not fired yet.
- Aminatou was still cast 23 times in 16 games.
- Nothing backfired that I could see. Two losses were one-turn kills from Enduring Enchantments, at turn 4 and turn 6.

### 4. What the format cannot say
- The miracle decision itself, including a miracle Terminus while we are ahead.
- Inkshield as a fog, and Arcane Denial, on other players' turns.
- Instants at end of turn.
- Which creature Time Wipe returns to hand.
- A count of the graveyard's enchantments and artifacts for Redress Fate.
- Keeping the commander out of go-wide attacks: there is no key to exclude a creature.

### 5. Recommendation
Send it to the 200 tables, ideally as two arms: the go-wide one and a forge-attack sibling. Most of the deficit looks like the attack drawing heat and sending Aminatou into combat.

Scratch files are in `<scratch>/batch/answers-miracle-worker` (`results/t1`, `results/t2`, `playtest-t1.json`, `playtest-t2.json`, `bin/`).
