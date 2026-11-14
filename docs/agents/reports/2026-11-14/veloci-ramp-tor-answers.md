<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Veloci-Ramp-Tor: answer rules and the cards the engine rules starved

The candidate is written: `playbook/variants/veloci-ramp-tor-answers.json` (version 2, `of` stampede, attack block unchanged). My local tables went over the limit on the final file. The final file played only 2 tables, not the 4 your prompt asks for, because 4 more would have taken me past the cap of 16. In all I played 16 tables (8 + 6 + 2). The final file is byte-identical to the file of those last 2 tables, and its cast object matches the one recorded in their `run.json`.

### 1. The answer cards in the exam (200 tables, `ctx.py` on the merged run; seen / cast from hand / in hand at a loss)
| Card | Stampede | Stock |
|---|---|---|
| Fiery Confluence | 84 / 12 / 35 | 67 / 31 / 18 |
| Wakening Sun's Avatar | 56 / 9 / 20 | 49 / 35 / 5 |
| Chandra's Ignition | 54 / 11 / 18 | 62 / 38 / 9 |
| Raging Swordtooth | 64 / 25 / 19 | 51 / 42 / 4 |
| Savage Stomp | 49 / 20 / 9 | 52 / 38 / 6 |
| Return of the Wildspeaker | 64 / 31 / 15 | 61 / 46 / 7 |
| Path to Exile / Generous Gift | 52/47/2, 54/47/3 | about the same |

- What killed the seat was mostly tokens: Soldier, Goblin, Insect and Bird tokens are the top sources.
- On the turns these answers sat in hand, the largest single opponent had about 7 to 8 creatures.

### 2. Rules (final numbering)
1–3. Unchanged from the base.
4. **New.** Topiary Stomper, Wayward Swordtooth and Atzocan Seer are played as ramp while we have 5 lands or fewer and Pantlaza is not out. After that they stay in the creature list, dearest first.
5. **Changed.** The base engines plus Wayta, Trainer Prodigy (3-mana haste 1/5 that doubles enrage triggers).
6. **New.** Wakening Sun's Avatar when one opponent has 3 or more creatures.
7. **New.** Chandra's Ignition when one opponent has 3 or more creatures. Forge picks the target and decides whether to cast.
8. **New.** Raging Swordtooth when one opponent has 5 or more creatures.
9. **New.** `{"forge":"unnamed"}`. Fiery Confluence and Savage Stomp are cast here now, along with Path, Gift, Zacama's abilities and the fetch lands. I placed it after the answers and before the draw spell and creatures so that Forge's removal gets a turn before the mana goes to threats.
10. Rishkar's Expertise, unchanged from the base.
11. **New.** Return of the Wildspeaker with 8 or more power and 5 or fewer cards in hand.
12. **Changed.** The base creature list, with the Avatar (after Zetalpa), Raging Swordtooth (after Xenagos) and Itzquinth (before Dinosaur Egg) added.
13. Unchanged from the base.

**Tried and dropped after the first 14 tables:**
- **A Confluence rule** (one opponent with 5 or more creatures, plus a finisher at `opp_life <= 6`). A rule casts the charm without asking Forge, and 3 of its 6 casts killed nothing.
- **A Savage Stomp rule.** Every rule cast failed: 4 tries in one game, and the card stayed in hand.

### 3. Local tables
- **Answer casts:**
  - Avatar: 4 of 4 drawn. Its wipes took 22 and 13 opposing creatures for 1 of ours each.
  - Ignition: 1 of 2. That cast took 23 opposing creatures for 2 of ours.
  - Swordtooth: 5 of 5.
  - Confluence: 8 of 9 (2 of 2 through the forge rule under the final file).
  - Savage Stomp from hand: 0 of 2, both under the dropped rule. The forge-rule route for Stomp is **untested**: it was not drawn on the final tables.
  - Path 4 of 4, Gift 1 of 2, Return of the Wildspeaker 4 of 4.
- **The forge rule** cast Generous Gift, Fiery Confluence, Akroma's Will, Zacama's abilities, Mosswort Bridge once its hold had lifted, and fetch lands. Nothing it did looked harmful.
- **Wins:** 4 of 16 tables. That is far too few games to mean anything.

### "Cast LESS" list (drawn / cast, over all 16 tables) and what I did
- **Wakening Sun's Avatar** 4/4, **Raging Swordtooth** 5/5, **Chandra's Ignition** 1/2: answer rules, plus a place in the creature list.
- **Wayta** 5/5: moved into the engines rule.
- **Itzquinth** 6/6: added to the creature list.
- **Fiery Confluence** 8/9, **Savage Stomp** 0/2: left to the forge rule.
- **Atzocan Seer** 4/4, **Topiary Stomper** 4/4, **Wayward Swordtooth** 6/9: the early ramp rule.
- **Return of the Wildspeaker** 4/4: its own rule.
- **Deathgorge Scavenger** 2/2, **Xenagos** 3/6, **Curious Altisaur** 4/4, **Shifting Ceratops** 1/2, **Quartzwood Crasher** 2/3, **Earthshaker Dreadmaw** 5/6: no change. They were already in the creature list and lose out on mana to dearer cards. I judge that to be the base's design, not a missing rule.

The "cast more" engine cards held up: Rishkar's 6/6, Bestiary 9/9.

### 4. What the rule format cannot express
- An opponent's creature as a target: Stomp, Wayta's fight, Itzquinth's trigger.
- Opponents' creature toughness: a 1-damage sweep is only worth it against X/1s.
- The lowest opponent life, so no Confluence finisher.
- Instant-speed timing for Akroma's Will and Return of the Wildspeaker.
- A rule-cast charm skips Forge's judgement of whether the modes are worth casting.

### 5. Recommendation
Send it to 200 tables, as a playbook-only arm beside stampede's arms on seed 20261280. One caveat: whether Savage Stomp gets cast through the forge rule has not been seen.

Files are in `<scratch>/batch/answers-veloci-ramp-tor/`:
- the local runs: `results/t1`, `t2`, `t3`
- the playtest reports: `t1-playtest.json`, `t2-playtest.json`, `t3-playtest.json`
- the context script: `ctx.py`
