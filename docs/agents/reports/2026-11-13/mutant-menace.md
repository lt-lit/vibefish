<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Mutant Menace (The Wise Mothman): report

The candidate is about 1.2 turns faster than stock in goldfish on the validation seeds, and the interval does not include zero. I did not change any rule after seeing the validation games.

**1. The audit: 12 stock games, seeds 23001 to 23012**
- **Kill turn:** 11.33 (median 11, range 10 to 14). 12 of 12 won.
- **Unspent mana:** 1.5 of 5.7 lands' worth a turn (27%). 26% of turns ended holding a card the leftover mana would have paid for, and 13% of turns cast nothing.
- **Commander timing:** Mothman was cast on own turn 4 to 11 (4, 5, 10, 5, 5, 7, 5, 4, 4, 9, 11, 4).
- **Cards sat on with the mana up:** Winding Constrictor (7 turns), Contagion Clasp (6), Hardened Scales (6), Hancock (5), Contaminated Drink (4), Young Deathclaws (4). Part of this is colour screw: the deck is three colours with many taplands and colourless lands.
- **Drawn and never cast:** Bloatfly Swarm (0 of 5), Struggle for Project Purity (0 of 5), Feral Ghoul (0 of 4), Raul (0 of 3), Contaminated Drink (0 of 3), Guardian Project (0 of 2).
- **Under-cast ramp:** Cultivate 1 of 5, Talisman of Dominance 1 of 5.
- **Abilities never used:** Jason Bright's sacrifice ability (24 turns on the battlefield), Nesting Grounds (20), Cathedral Acolyte (12), Raul's mill tap.
- **Trigger Forge declines:** Tato Farmer's optional "get two rad counters".
- **Flags:** Biomass Mutation is the only card flagged never-cast (`RemoveDeck:All`). Hardened Scales, Winding Constrictor and Inspiring Call are flagged `RemoveDeck:Random`.
- **How games end:** by combat damage, with a few commander-damage kills. Rad counters on the do-nothing opponents only mill their lands, so they cost them no life. Rad milling did deck two opponents in the stock validation run and one in the playbook run.

**2. The candidate: `playbook/variants/mutant-menace-mothman.json`**
1. Ramp first: Sol Ring, Signet, the three Talismans, Rampant Growth, Farseek, Cultivate. Stock under-casts them.
2. The Wise Mothman as soon as it can be cast.
3. The counter doublers before the creatures they multiply: Hardened Scales, Winding Constrictor, Branching Evolution, Corpsejack Menace.
4. The engine creatures and enchantments: Raul, Hancock, Guardian Project, Inexorable Tide, Marcus, Scorchbeast, Mirelurk Queen.
5. Tap Raul in the first main phase (only while the library has 30 cards or more), so our own nonland mills trigger Mothman, Mirelurk Queen and Scorchbeast before combat.
6. Every other creature, most expensive first. This is what gets Bloatfly Swarm and Feral Ghoul cast.
7. Vault 87 and Struggle for Project Purity while the library has 45 cards or more. Both draw.
8. Biomass Mutation in the first main phase, X at least 6, with three or more attackers.
9. Contaminated Drink, X at least 3, with 4 or fewer cards in hand and 35 or more in the library.
10. Harmonize while the library has 25 cards or more.
11. Strength Bobblehead's counter ability after combat.
12. Contagion Clasp's proliferate after combat.

Triggers: always take Scorchbeast's tokens and Radroach's return. Take Tato Farmer's rad counters only while Mothman or Scorchbeast is out, with 50 or more cards in the library and 20 or more life.

Attack: the default go-wide block from the brief.

The tuning round added rules 7, 9 (loosened), 12 and the Tato trigger rules; together they changed nothing (0.00 turns against tune-1). I kept them because they make the deck cast its cards.

**3. Validation: seeds 23101 to 23140, rules frozen beforehand**

| | Wins | Kill turn mean (median) | Range |
|---|---|---|---|
| Stock | 39 of 40 (1 not finished) | 11.54 (11) | 8 to 19 |
| Playbook | 40 of 40 | 10.43 (10) | 7 to 14 |

- **Paired on the 39 seeds both arms won:** stock minus playbook = +1.18 turns (95% interval +0.54 to +1.81). The playbook was faster in 26, the same in 5, slower in 8.
- **Unspent mana:** 23% under the playbook against 34% for stock.
- The rules recorded in `run.json` match the frozen file. The pair is in `<scratch>/batch/mutant-menace/mutant-menace-pair.json`.

**4. Which rules fired (validation, 40 games)**
- Cast rules: r1 96, r2 41, r3 34, r4 69, r5 (Raul) 56, r6 195, r7 11, r8 (Biomass) 2, r9 4, r10 5.
- Triggers: Scorchbeast accepted 9 times, Tato Farmer 31.
- Never fired: r11 (Bobblehead) and r12 (Clasp proliferate), and the Radroach trigger, which cannot occur in goldfish.

**5. What the rule format cannot express**
- **Targets for our own pump effects:** Cathedral Acolyte's "creature that entered this turn", Bobblehead's counters and the equip targets for Power Fist and Nuka-Nuke Launcher can't be named dynamically.
- **Contagion Clasp:** a rule can't aim its -1/-1 counter at an opponent's creature, so it stays in hand at an empty table.
- **Choices as an effect resolves:** Struggle's mode (Brotherhood or Enclave), the proliferate choices, and Mothman's targets for its counters stay Forge's.
- **Missing conditions:**
  - rad counters on players, which would let a rule time Tato Farmer or Contaminated Drink properly;
  - how many of our creatures carry counters, for Inspiring Call;
  - creature cards milled this turn, for The Master's tap.
- **Jason Bright:** a sacrifice-for-value line, which needs a choice of what to sacrifice.

**6. Recommendation:** send it to the 200 tables. The engine and the commander get played (+1.2 turns, interval clear of zero, and one stock stall gone). How much of that carries to tables of bots is the open question.

**7. The deck's answers, for the second pass**
None of these is flagged never-cast.
- **Putrefy:** destroys an artifact or creature.
- **Atomize:** destroys a nonland permanent, then proliferates.
- **Casualties of War:** destroys one artifact, creature, enchantment, land and planeswalker.
- **Nuclear Fallout:** X wipe; every creature gets -2X/-2X and every player gets X rad counters.
- **Find // Finality:** Finality is a -4/-4 sweep after two +1/+1 counters on one of ours; Find returns creatures from the graveyard.
- **Alpha Deathclaw:** destroys a target permanent when it enters and again when it becomes monstrous.
- **Rampaging Yao Guai:** destroys artifacts and enchantments with total mana value X or less.
- **Vault 87, chapter I:** steals a non-Mutant creature.
- **Contagion Clasp:** puts a -1/-1 counter on a creature when it enters.
- **Mutational Advantage:** protection, not a fog. Our permanents with counters gain hexproof and indestructible, damage to them is prevented, then proliferate.
- **Counterspells:** none in the list.

**8. How an owner expects it to play**
Ramp into Mothman early, then mill: Raul and rad counters mill our own deck, and every nonland card milled grows the team through Mothman. The counter doublers turn proliferate (Inexorable Tide, Frank Horrigan, Radstorm) into huge boards. Rad counters on opponents both mill them and cost them life. The candidate now gets Mothman, the doublers, Raul and the engine pieces down on time. It still leaves to Forge the proliferate decisions, all targeting, Jason Bright, the equipment and Struggle's mode. In goldfish the rad plan cannot show, because the opponents mill only lands. Its real worth, and the answers, can only be judged at tables.
