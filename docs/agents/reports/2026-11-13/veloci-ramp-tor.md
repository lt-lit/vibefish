<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Veloci-Ramp-Tor (Pantlaza, Sun-Favored): report

**1. The audit** (12 stock goldfish games, seeds 22001+)
- Stock already plays this deck well. It killed in 11.25 turns on average (10 to 13) and left 28% of its mana unspent. Nearly all of that unspent mana sat on answers that had nothing to hit: Generous Gift, Path to Exile, Fiery Confluence, Chandra's Ignition, Savage Stomp. A turn with nothing cast was rare (8%).
- What stock left undone:
  - **Pantlaza was late.** It came down on own turns 4 to 10 (median 6 to 7) and was never cast in 2 of the 12 games.
  - **Ramp and engines were late.** Sol Ring went down on turn 7 (median) and Lifecrafter's Bestiary sat in hand for up to 8 turns.
  - **Cards it never cast:** Rishkar's Expertise, Apex Altisaur and Bronzebeak Foragers. Forge won't cast the last two when their enter trigger has nothing to aim at.
- **Abilities never used:** Kessig Wolf Run, Rogue's Passage, Otepec Huntmaster's haste, Wayta's fight, Shifting Ceratops, Atzocan Seer, Thrashing Brontodon. Thundering Spineback's token was made once in 14 turns.
- **Triggers declined:** Lifecrafter's Bestiary only when it had no mana to pay, and Itzquinth when there was no target.
- **Flagged never-cast:** only Marauding Raptor (`AI:RemoveDeck:All`).

**2. The candidate:** `playbook/variants/veloci-ramp-tor-stampede.json`
1. Hold Mosswort Bridge's ability until we have 10 power and 8 lands. Forge activated it every upkeep with Bronzebeak Foragers hidden under it, then declined to cast the Foragers. That spent a green mana each turn and stranded a hand of green cards: one game took 14 turns.
2. Ramp and rocks first.
3. Pantlaza as soon as it is affordable.
4. The engines: Otepec Huntmaster, Lifecrafter's Bestiary, Rhythm of the Wild, Descendants' Path.
5. Rishkar's Expertise when total power is at least 4 and the library has at least 30 cards.
6. Every Dinosaur and creature, most expensive first, so Pantlaza's one discover a turn is the biggest. This includes Apex Altisaur and Bronzebeak Foragers as bodies. Marauding Raptor is left out on purpose because it deals 2 to each creature that enters and kills our mana creatures. Itzquinth is left to Forge.
7. Thundering Spineback's token in main phase 2, with spare mana.

Attack is the brief's go_wide block. Tried and dropped: an accept rule for Bestiary's pay-G draw. Forge already pays it whenever it has the mana, and the games came out identical. On the audit seeds the rules were +0.75 turns without rule 1 and +1.08 with it.

**3. Validation** (seeds 22101+, 40 games each arm, all 40 won in both)
- Stock killed in 11.35 turns on average, the playbook in 10.03.
- Paired difference: **+1.32 turns faster (95% +0.97 to +1.68)**. The playbook was faster in 32 games, the same in 6, slower in 2.
- No rule was changed after I saw the validation games. Because of the container restart, val-stock was run before the restart and val-playbook after it, on the same unchanged file.
- Pantlaza was cast in 40 of 40 games on own turn 5.15 on average, against 37 of 40 games on turn 6.78 under stock.
- Unspent mana fell from 28% to 17%.
- Pair file: `<scratch>/batch/veloci-ramp-tor/veloci-ramp-tor-pair.json`

**4. Which rules fired** (`playbook_stats` over the 40 validation games)
- rule 1 (Mosswort hold): 34 vetoes
- rule 2 (ramp): 105
- rule 3 (Pantlaza): 40
- rule 4 (engines): 37
- rule 5 (Rishkar's): 11
- rule 6 (creatures): 272
- rule 7 (Spineback token): 2
- 1 cast failed. Every rule fired.
- Card by card, against stock: Apex Altisaur cast in 10 of 12 games drawn (stock 0 of 9), Bronzebeak Foragers 10 of 11 (stock 0 of 11), Rishkar's Expertise 10 of 10 (stock 0 of 13).
- One side effect: Itzquinth was cast in 6 of 10 games against stock's 9 of 9, because the cheap cards now wait behind the expensive ones.

**5. What the rule format cannot express**
- Kessig Wolf Run and Otepec Huntmaster's haste both want "the biggest creature that can attack" or "the Dinosaur cast this turn" as their target. A rule can only name a fixed permanent.
- Itzquinth, Savage Stomp and Wayta's fight need an opponent's creature as a target.
- I can't see what Mosswort Bridge has hidden, so the hold is a proxy. Forge activating it and then declining to cast the card is a Forge oddity.
- There is no way to pick Rhythm of the Wild's riot choice (haste or counter) or Etali's free casts.

**6. Recommendation:** send it to 200 tables. The gain is well clear of noise and comes from the plain things: the commander about a turn and a half earlier, the engines on curve, and three cards stock never cast now cast. Stock was already strong with this deck, so the gain at the tables may be small. Which attack the deck keeps should be decided there.

**7. The deck's answers, for the second pass** (none of them is flagged never-cast)
- Path to Exile: exiles a target creature.
- Generous Gift: destroys any target permanent (its controller gets a 3/3).
- Fiery Confluence: three picks among 1 damage to each creature, 2 damage to each opponent, destroy an artifact.
- Chandra's Ignition: our creature deals its power to every other creature and each opponent (a one-sided wipe if it is big).
- Wakening Sun's Avatar: destroys all non-Dinosaur creatures when cast from hand. This includes our mana creatures, Otepec Huntmaster and Wayta.
- Raging Swordtooth: 1 damage to each other creature when it enters.
- Savage Stomp: a +1/+1 counter, then fight.
- Apex Altisaur: fights when it enters and again whenever it is damaged.
- Itzquinth: pay 2 for a Dinosaur to deal damage equal to its power.
- Wayta: a fight ability.
- Bronzebeak Foragers: exiles up to one nonland permanent per opponent.
- Thrashing Brontodon: sacrifice it to destroy an artifact or enchantment.
- Scion of Calamity: destroys an artifact or enchantment on combat damage.
- Zacama: 3 damage to a creature, or destroy an artifact or enchantment.
- Deathgorge Scavenger: graveyard hate.
- Akroma's Will: protection or indestructible, also a finisher.
- No counterspells and no fogs.

**8. How a person plays it, and where the bot falls short**
An owner ramps on turns 2 and 3, lands Pantlaza on turn 4 or 5, and then plays one big Dinosaur a turn so each discover chains into a free spell. Haste from Rhythm of the Wild and Xenagos lets the fat attack at once, and Kessig Wolf Run or Akroma's Will closes the game. The candidate now does the ramp, the commander and the Dinosaur a turn. It still leaves the haste and pump abilities unused, never sequences a cheap Dinosaur before Pantlaza to discover twice, and holds its removal until Forge sees a target, which only real tables will test.
