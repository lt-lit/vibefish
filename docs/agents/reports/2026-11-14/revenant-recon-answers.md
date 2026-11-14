<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Revenant Recon: answer rules and the cards the engine rules held back

The candidate is ready: `playbook/variants/revenant-recon-answers.json` (variant `answers`, of `revenant-recon-mirko.json`, version 4, attack block unchanged). The cast rules and trigger rules in the file are exactly what the last 8 local tables played: I checked them against each game's `run.json`. Only the notes text changed after that run. **I recommend sending it to 200 tables.**

### 1. Answer cards in the exam (200 tables; my own count from the event logs)
Columns are games drawn / games cast / games where the card was still in hand at a loss. "Drawn" means it was ever in hand, so these counts run a little higher than `playtest.py`'s.

| Card | Stock AI | Candidate (mirko) |
|---|---|---|
| Black Sun's Zenith | 66/0/36 | 60/0/29 |
| Toxic Deluge | 55/0/25 | 58/0/32 |
| Massacre Wurm | 65/22/17 | 62/35/6 |
| Ravenous Chupacabra | 56/43/2 | 60/31/8 |
| Overseer of the Damned | 49/34/6 | 55/21/13 |
| Amphin Mutineer | 59/43/8 | 62/23/18 |
| Shriekmaw | 57/43/5 | 51/33/4 |
| Connive // Concoct | 61/49/4 | 67/35/21 |
| Dream Eater | 49/32/3 | 56/30/12 |
| Counterpoint | 76/29/26 | 74/23/25 |

Price of Fame, Pile On, Ephara's Dispersal and Discovery // Dispersal are cast in 85–95% of the games they are drawn under both pilots.

`playtest.py` reports 0% cast for both split cards. That is wrong: the cast events carry the half's name (Connive, Dispersal), which the tool does not match to the card.

On the last own turn of a loss, the widest opponent had a median of 11 creatures against our 4, with us at 14 life.

### 2. Rules added (final order, 22 cast rules)
- **1–2. Black Sun's Zenith**, X as high as the mana allows, at least 3. It fires in either of two cases:
  - the widest opponent has 6+ creatures, more power than us, and we have 3 or fewer creatures. This held on one of the last three own turns in 91 of 144 losses and 11 of 55 wins;
  - the widest opponent has 6+ creatures and more than we have, and could kill us next turn.
  These sit above everything, because the Zenith wants all the mana.
- **4. Massacre Wurm** when an opponent has 4+ creatures. It is one-sided, so it goes above Mirko.
- **9. Overseer of the Damned, Ravenous Chupacabra, Shriekmaw** when an opponent has a creature. Forge aims their enter triggers. A new trigger rule (number 5) accepts Overseer's optional destroy when an opponent has a creature.
- **10. Amphin Mutineer** when an opponent has a creature and 6+ total power. Its controller gets a 4/3, so it is not worth it on small boards.
- **14. Reanimate, Animate Dead.** They are cast only when Forge's logic agrees, since it picks the target.
- **15. Necromancy, Charnel Serenade** from own turn 6. Neither targets when cast, so the rule casts them as they are; by turn 6 there are usually creatures in the graveyards.
- **16. `{"forge": "unnamed"}`.** Here Forge chooses among the cards no rule names: the clones, Connive // Concoct, Foreboding Steamboat, Dream Eater, the cheap removal, and the rocks and lands with abilities. I put it before the cheap creatures and draw spells because the clones and the split card need Forge's choice anyway.
- **Tried and dropped: Toxic Deluge** on the Zenith's conditions. Its X is paid in life, which a rule cannot set. In a local game it was cast with X = 0: no life paid, nothing died.

**Base rules moved or changed:**
- Base 1–7 are now 3, 5, 6, 7, 8, 11, 12, in the same order.
- Base 8 is split in two. Rule 13 holds the threats (the first nine creatures, plus Eye of Duskmantle after Sphinx and Watcher of Hours last). Rule 17 holds the cheap creatures (Unshakable Tail to Thoughtbound Phantasm), now below the forge rule.
- Base 9 is now 18. Base 10 is now 19, with Deep Analysis added. Base 11–13 are now 20–22.

### 3. The 12 cards cast less under the candidate (cast/drawn at the 16 local tables)
- **Amphin Mutineer:** rule 10. 4/4; it exiled Cloud, Sporemound and Titans' Vanguard.
- **Eye of Duskmantle:** added to the threats rule. 2/5.
- **Charnel Serenade:** rule 15. 3/6, it returned creatures each time.
- **Watcher of Hours:** last in the threats rule; Forge chose its suspend once. 1/3.
- **Vizier of Many Faces:** left to the forge rule. 0/3: Forge declined it every time. Still open.
- **Overseer of the Damned:** rule 9 plus the trigger rule. 4/6, and the destroy hit an opposing creature each time.
- **Phyrexian Metamorph:** left to the forge rule. 3/6.
- **Ravenous Chupacabra:** rule 9. 1/1.
- **Deep Analysis:** added to the draw rule. 1/1.
- **Foreboding Steamboat:** left to the forge rule. 1/3. Its symmetric exile needs a count of our nontoken creatures, which the rules cannot see.
- **Necromancy:** rule 15. 3/5.
- **Dream Eater:** left to Forge (it has flash). 3/4.

### 4. Local tables (16 in all: seeds 20263180 and 20263181, eight each; the second set on the final file)
- **Black Sun's Zenith:** 3/6. It killed 12, 15 and 13 opposing creatures and 1 to 3 of ours each time; two of those games were won.
- **Massacre Wurm:** 3/4. It killed 7 and 16 opposing creatures.
- **Rules that never fired:** none of the new ones. Shriekmaw was never drawn, so its part of rule 9 was not tested.
- **Forge rule:** the trace shows 20 plays taken there: Metamorph, Connive, Dream Eater, Everflowing Chalice, Rogue's Passage, encore, Brainstorm, Ransom Note and Watcher's suspend.
- **Possible cost:** Forge sometimes spends 4 mana on Rogue's Passage at the forge rule, ahead of the cheap creatures.
- **Record:** the seat won 1 of 8, then 5 of 8. Too few games to mean anything.

### 5. What the rule format cannot express
- Toxic Deluge's X, which is paid in life.
- Counterpoint, and the flash windows of Dream Eater and Final-Word Phantom (instant speed on other players' turns).
- Which creature Mirko and the reanimation spells return, and any condition on the creatures in a graveyard.
- Which half of a split card is cast.
- Which of our creatures Foreboding Steamboat exiles.
- Sizing the Zenith to spare Mirko, since a rule cannot see opposing toughness.

My analysis scripts and local runs are in `<scratch>/batch/answers-revenant-recon/`, with the local runs under `results/t1` and `results/t2`.
