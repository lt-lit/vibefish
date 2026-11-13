<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Squirreled Away (`squirreled-away`): report

**1. Audit (12 stock goldfish games, seeds 24001-24012).** All 12 games were won, with a mean kill turn of 11.75 (median 12). Stock left 27% of its mana unspent (1.5 of 5.7 lands a turn). On 19% of turns it ended holding a card it could have paid for, and on 7% it cast nothing. Stock already runs this deck reasonably well.
- **Commander:** Hazel came out on own turn 5.2 on average.
- **Cards it sat on:** Plaguecrafter, Maelstrom Pulse, Tear Asunder, Cache Grab and Academy Manufactor. It never cast Hazel's Brewmaster (0 of 4 games), Shamanic Revelation (0 of 3), Scurry of Squirrels or Rootcast Apprenticeship (1 of 4).
- **Wasted plays:** it cast End-Raze Forerunners after combat, which wastes its +2/+2.
- **Abilities used rarely or never:** Squirrel Nest's land was never tapped for a Squirrel. Idol of Oblivion drew 3 times in 21 turns on the battlefield, Skullclamp was equipped 3 times in 20, Maskwood Nexus used once in 9, Chitterspitter 5 times in 16. Insatiable Frugivore, Swarmyard and Haywire Mite were never used.
- **Feeding Woe Strider:** stock sacrificed tokens to Woe Strider for scry on other players' turns.
- **Triggers declined:** Chitterspitter's upkeep sacrifice and Skyfisher Spider's.
- **Never cast by Forge:** only Decree of Pain is flagged `AI:RemoveDeck:All`. Second Harvest and Scurry of Squirrels are flagged `Random`.

**2. The candidate:** `playbook/variants/squirreled-away-acorns.json` (version 2). Rules in file order:
1. Play Sol Ring and the three Signets/Talisman first.
2. Play Hazel at once.
3. Play End-Raze Forerunners only in main phase 1 with 4 or more attackers.
4. Hold End-Raze otherwise.
5. Deploy the token engine and payoffs in a fixed order: Chatterfang, the Squirrel lords, Chitterspitter, Toski, Odd Acorn Gang, Beastmaster Ascension, the drain and draw pieces, then the rest. Hazel's Brewmaster is included because stock never cast it.
6. Second Harvest at 4 or more tokens.
7. Shamanic Revelation at 5 or more creatures and a library of 30 or more.
8–9. Gourmand's Talent Level 2 and Level 3.
10. Equip Skullclamp onto a Squirrel Token, up to 3 times a turn, while no lord keeps the tokens alive and the library is 30 or more.
11. Idol of Oblivion draws whenever it can (library 20 or more).
12–13. Chatterstorm at storm 2 or more, otherwise in main phase 2.
14–16. In main phase 2: Chitterspitter, Maskwood Nexus, and the land enchanted by Squirrel Nest. The rule lists every land name in the deck.
17. Idol again in main phase 2.
18–21. Hold Woe Strider's scry unless Zulaport, Bastion, Nadier's Nightblade or Poison-Tip Archer is out.
- **Triggers:** always take Beastmaster Ascension's quest counter; take Chitterspitter's upkeep sacrifice with 3 or more tokens.
- **Attack:** go_wide per the brief.
- **Tuning:** tune-1 (v1) was +1.33 turns over stock on the audit seeds. Tune-2 added Brewmaster and the Woe Strider holds (+1.50; +0.17 over v1). Nothing was dropped.

**3. Validation (seeds 24101-24140, 40 games each arm).**

| | finished | kill turn mean (median) | unspent mana |
|---|---|---|---|
| stock | 40/40 | 11.38 (11) | 30% |
| acorns | 40/40 | 10.03 (10) | 22% |

- The playbook is **1.35 turns faster** on 40 paired seeds (95% +0.98 to +1.72). It was faster in 33, the same in 4 and slower in 3.
- Hazel came out on turn 4.1 against stock's 4.8.
- The rules were not changed after the validation games were seen.
- Pair file: `<scratch>/batch/squirreled-away/squirreled-away-pair.json`.

**4. Rules that fired (validation, 40 games).**
- **Cast rules:** r1 41, r2 40, r3 5, r5 324, r7 6, r8 7, r9 1, r10 39, r11 37, r12 4, r13 7, r14 7, r15 10. The holds turned down 6 of Forge's choices.
- **Triggers:** 261 accepted (Beastmaster 249, Chitterspitter 12).
- **Never fired in validation:** r6 (Second Harvest; Forge casts it first as an instant), r16 (the Squirrel Nest land; it fired 10 times in tune-1, so with a tapped land it never gets the chance) and r17 (Idol in main phase 2, already covered by r11).
- **Possible cost:** under the End-Raze hold it was cast in 5 of 12 games, against 12 of 13 under stock, and it sat in hand at the end of 5 games.

**5. What the rule format cannot express.**
- Rootcast Apprenticeship: three modes with targets, so a rule cannot cast it.
- Tapping the Squirrel Nest land or Chitterspitter at an opponent's end step, which is the correct timing.
- Choosing which token Hazel copies.
- Chatterfang's sacrifice-X-Squirrels: as removal it needs an opponent's creature as target.
- Hazel's mana ability (tap X tokens) is Forge's to use or not.

**6. Recommendation:** send it to 200 tables. The gain is +1.35 turns, clear of noise, from real engine use rather than invented rules. Game times stayed at 4-12 s and no loops appeared.

**7. The deck's answers, for the second pass** (no counterspells, no fogs):
- Putrefy: artifact or creature, cannot be regenerated.
- Maelstrom Pulse: nonland permanent plus everything with the same name.
- Tear Asunder: artifact or enchantment; kicked, any nonland permanent (exile).
- Windgrace's Judgment: one nonland permanent per opponent.
- Casualties of War: one artifact, creature, enchantment, land and planeswalker.
- Saw in Half: creature.
- Decree of Pain: wipe that draws per creature, or cycled for -2/-2 to all. **Flagged never-cast.**
- Swarmyard Massacre: one-sided -X/-X to non-Squirrels.
- Plaguecrafter: edict for every player.
- Chittering Witch: sacrifice a creature for -2/-2.
- Skyfisher Spider: on entering, sacrifice a creature to destroy a nonland permanent.
- Haywire Mite: noncreature artifact or enchantment.
- Garruk -3: destroy a creature.
- Binding the Old Gods, chapter I: destroy a nonland permanent.
- Chatterfang: +X/-X.
- Bojuka Bog and Hazel's Brewmaster: graveyard exile.

**8. How an owner expects it to play.** Hazel comes down on turn 3-4 off a rock. The board goes wide with Squirrel makers and Chatterfang doubling the tokens. Hazel's end-step copies, Second Harvest and Chatterstorm snowball the board, while sacrifice outlets with Zulaport, Bastion and Nadier's drain the table and Skullclamp, Idol and Toski refill the hand. The candidate now gets Hazel, the engine pieces and the card-draw artifacts working. It still taps tokens and lands in its own main phase instead of at end of turn, never casts Rootcast, and does not choose a sacrifice-drain finish over attacking. Its End-Raze hold may keep the card in hand too long.
