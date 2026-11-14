<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Enduring Enchantments: answer rules (candidate `answers`, version 2)

I recommend sending it to the 200 tables. The new rules fire when they should, and the wipes they cast were very one-sided in the local games.

**1. What the league games show** (league-run #3, 200 games, the seat won 64). "Castable turns in losses" counts own turns where the card was in hand with at least its mana value in lands.

| Card | Seen | Cast from hand | In hand at a loss | Castable turns in losses |
|---|---|---|---|---|
| Extinguish All Hope | 68 | 14 | 29 | 104 |
| Culling Ritual | 60 | 13 | 28 | 140 |
| Cacophony Unleashed | 59 | 9 | 22 | 38 |
| Calix, Destiny's Hand | 63 | 21 | 31 | 104 |
| The Eldest Reborn | 57 | 20 | 20 | 87 |
| Grasp of Fate | 54 | 24 | 18 | 83 |
| Battle at the Helvault | 47 | 17 | 16 | 54 |
| Binding the Old Gods | 43 | 20 | 13 | 82 |
| Path / Cast Out / Doomwake Giant | 74 / 46 / 56 | 76 / 43 / 52 | 1 / 1 / 6 | – |

- The shipped library hold (cards held once the library is under 25) was not the reason these cards sat in hand: the library was under 25 on at most 6 of 104 held turns.
- On the turns Extinguish All Hope sat castable in a loss, the seat had 1/3/6 creatures (quartiles), of which 0/1/4 were non-enchantment creatures. The largest opposing board was 4/7/11 creatures.
- Losses were spread across all eleven opponents.

**2. Rules added.** Every shipped rule is kept in its order, the triggers are unchanged, and there is still no attack block.
- **Rule 2:** Extinguish All Hope, else Cacophony Unleashed, when `opp_creatures >= 5` and `opp_creatures > creatures`. Both destroy only non-enchantment creatures, and most of ours are enchantment creatures. In the league this condition held in 26 of the 34 losses where the card was castable, a median of two own turns before the end.
- **Rule 3:** the same two cards when `opp_creatures >= 8` and `opp_power > power`, however wide our board is.
- **Rule 4:** Culling Ritual when `opp_creatures >= 6` and `opp_creatures > creatures`. It is narrower than rule 2 because it also kills our Sol Ring, Signet and two-mana enchantresses.
- **Rule 11:** Grasp of Fate, Binding the Old Gods, The Eldest Reborn, Calix and Battle at the Helvault when `opp_creatures >= 1`. It sits after the enchantress engine and before the other threats.
  - None of these needs a target to cast, so a play rule casts them and Forge still chooses targets when the trigger or chapter resolves.
- Nothing was dropped.

**3. Local tables.** 16 games at tables of bots, seeds 20263080 and 20263081. Seen / cast under the candidate:
- Extinguish All Hope 9/6, Cacophony 6/3, Culling Ritual 7/4.
- Grasp 7/8, Helvault 9/9, Binding 10/9, Eldest Reborn 9/10, Calix 3/3. Some cards were cast more often than seen, probably because they came back.
- Path to Exile 10/10 and Cast Out 7/7 stay with Forge.

What the casts did:
- Extinguish All Hope destroyed 13, 21, 11, 11 and 16 opposing creatures, against 0 to 2 of ours each time.
- Cacophony destroyed 9, 8 and 6 opposing creatures, against 1 of ours (Ondu Spiritdancer) in one cast.
- Culling Ritual cost us 1 to 3 cheap permanents (Sol Ring once; Sythis and Jukai once). It took 10 of Goblin Storm's and Token Triumph's tokens in one game and 18 of Deep Clue Sea's permanents (Clues) in another.
- Forge aimed the removal triggers at commanders and the best threats: Galadriel, Emmara, Caesar, Cloud, Gisa.

Problems seen:
- Battle at the Helvault's "for each player" chapter once exiled our own Arcane Signet.
- Rule 3's casts could not be told apart from rule 2's in the logs.
- Two losses held a castable wipe. In one the seat died to a Chandra emblem in its upkeep at 1 life. In the other the board stayed under the threshold (opponents at 2 to 5 creatures against our 3 to 7).

The seat won 11 of 16 (one draw). That is far too few games to mean anything.

**4. What the rule format cannot express**
- What a wipe would destroy on each side. `creatures` counts our enchantment creatures, which survive Extinguish All Hope and Cacophony, so rule 2 is more cautious than a person would be.
- How many cheap permanents and tokens of mana value 2 or less the opponents have (Culling Ritual's real condition).
- Which permanent Grasp of Fate, Binding the Old Gods, Battle at the Helvault, Calix's −3, Cast Out and Path to Exile hit. That stays Forge's choice, including Battle at the Helvault picking one of our own permanents.
- Cast Out and Path to Exile at instant speed on other players' turns.
- Calix's loyalty choices.

**5. File:** `playbook/variants/enduring-enchantments-answers.json` (the shipped version 1 plus rules 2–4 and 11). The local games are in `<scratch>/batch/answers-enduring-enchantments/results/t1` and `/t2`.
