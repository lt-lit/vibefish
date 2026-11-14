<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Blood Rites (`blood-rites`): answer rules and rules for the starved cards

**File:** `playbook/variants/blood-rites-answers.json` (variant `answers`, of `blood-rites-demons.json`, version 2; the `attack` block and triggers are unchanged). The playbook recorded in the last local run's `run.json` matches the file exactly. **I recommend sending it to 200 tables.**

### 1. Answer cards in ab-run #29 (200 tables). Counts are drawn / cast / in hand at a loss
| Card | Stock AI | Candidate `demons` |
|---|---|---|
| Damn (Forge always aims it at one creature, never overloads it) | 33 / 29 / 6 | 37 / 12 / 16 |
| Austere Command | 45 / 32 / 6 | 37 / 6 / 21 |
| Olivia's Wrath (one-sided: every creature in this deck is a Vampire) | 43 / 33 / 6 | 45 / 15 / 14 |
| Patron of the Vein | 47 / 43 / 1 | 45 / 22 / 18 |
| Butcher of Malakir | 56 / 35 / 12 | 52 / 23 / 18 |
| Swords / Utter End / Return to Dust (instants: Forge casts them on other players' turns) | 35/35/0, 55/52/1, 54/46/5 | 42/39/2, 50/48/2, 48/42/9 |
| New Blood | 50 / 0 / 30 | 41 / 0 / 20 |

Stock's casts were mostly good play:
- **Damn:** all 29 aimed at real threats (Avenger, Hornet Queen, Krenko, Caesar).
- **Austere Command:** on average about 13 opposing permanents destroyed for 2 of ours; the seat won 18 of those 32 games.
- **Olivia's Wrath:** killed 1 to 115 opposing permanents and none of ours; the seat won 19 of 33.

### 2. Rules (numbers are positions in the file)
- **3. Olivia's Wrath** when `type:Vampire >= 3` and `opp_creatures >= 3`. It is a one-sided wipe, so it goes high.
- **4. `forge` rule** when `opp_power > power` and `opp_creatures >= 3`. When the seat is behind, Forge picks among the unnamed cards here. This is how Austere Command gets cast, since a play rule cannot choose its modes.
- **5. Patron of the Vein** when `opp_creatures >= 1`. Forge aims its enter-the-battlefield kill.
- **6. Damn.** Forge's logic aims it at one creature.
- 7 is the base's engine rule, unchanged.
- **8. Sorin, Lord of Innistrad, Heirloom Blade, Swiftfoot Boots.**
- **9. `forge` rule with no condition**, before Champion of Dusk and the creature list. Austere Command, the instants and the activations no rule names get Forge's judgement before the filler and the mana sinks.
- **12. Patron of the Vein** again, with no condition, after the creatures.
- **17. Rogue's Passage**, activated in the first main phase only, last. I added this after the first run: rule 4 spent 4 mana on it twice ahead of the engine's casts.

**Base rules moved or changed:**
- Butcher of Malakir moved to the front of the creature list (it was starved behind 12 cheaper creatures).
- Nighthawk Scavenger moved ahead of Bloodtracker.
- The base's rules 3 to 9 shifted down by the insertions; their content is unchanged.

Nothing was tried and dropped.

### 3. Local tables (seeds 20263190 ×8, then 20263191 ×4 with the final file; 12 tables, trace on)
- **Olivia's Wrath:** 2 drawn, 2 cast. Killed 9 and 3 opposing permanents, none of ours.
- **Austere Command:** 5 drawn, 2 cast, both through rule 4. Results: 32 opposing for 7 of ours, then 13 for 3. Of the other three: one was drawn on the seat's last turn with only 4 lands, and two were held for six turns in a game the seat won at life 52 to 160, which is right.
- **Patron of the Vein:** 2 drawn, 1 cast. Its enter-the-battlefield trigger killed Anikthea. The other copy was in hand at a loss.
- **Damn:** drawn once, on the turn the seat won, so it is untested locally.
- **Others:** Sorin 2 drawn / 2 cast; Heirloom Blade 4/3; Swiftfoot Boots 5/5; Butcher 2/1; Nighthawk 6/6; Swords 3/3; Utter End 1/1; Return to Dust 3/3; New Blood 3/0.
- **What the `forge` rules cast:**
  - Rule 4: Austere Command ×2, Return to Dust, Sorin's −2, Swiftfoot Boots equip ×6, Blade of the Bloodchief, Bartolomé's sacrifice ability, Rogue's Passage ×2 (fixed by rule 17).
  - Rule 9: Wayfarer's Bauble, Sorin, Blade of the Bloodchief, Bartolomé.
- **Never fired:** nothing that was in hand. The engine rules kept firing.
- **Wins:** 6 of 12 (3/8, then 3/4). That is too few games to mean anything.

### 4. What the rule format cannot express
- **New Blood:** Forge's logic declined it in all 91 games it was drawn across both arms, and a play rule defers to that logic. It needs an opponent's creature as a target.
- **Pact of the Serpent:** flagged `AI:RemoveDeck:All` and aimed at a player, so a rule cannot cast it.
- **Damn overloaded:** an alternative cost, which play rules skip.
- **Austere Command's modes:** reachable only through the `forge` rule.
- **Missing conditions:** "we are behind" can only be said as total power, and the format cannot count what a wipe would destroy on each side.

### "Cast LESS" list: what I did with each card
- **Damn:** rule 6, high in the order.
- **Austere Command:** left to Forge through `forge` rules 4 and 9.
- **Olivia's Wrath:** rule 3.
- **Patron of the Vein:** rules 5 and 12.
- **Heirloom Blade:** rule 8. The base's equip rule is kept.
- **Sorin, Lord of Innistrad:** rule 8. Its loyalty abilities are left to Forge.
- **Swiftfoot Boots:** rule 8. Equipping is left to Forge.
- **Nighthawk Scavenger:** moved earlier in the creature list.
- **Butcher of Malakir:** moved to the front of the creature list.

The base's Viscera Seer scry hold stays. None of the "cast more" cards lost a rule: the engine rule sits below only conditional answers and three cheap cards.

Scratch files are in `<scratch>/batch/answers-blood-rites/`: runs `results/t1` and `results/t2`, `t1.json`, `t2.json`, and `casts.py`.
