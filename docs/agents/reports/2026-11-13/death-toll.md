<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Death Toll (Winter, Cynical Opportunist): report**

**1. Audit** (stock, 12 games, seeds 27001–27012)
- Kill turn 11.67 (median 12, range 9–14). About 45% of the mana went unspent (3.0 of 6.6 lands a turn), and 14% of turns cast nothing.
- **Winter is flagged `AI:RemoveDeck:All`, so stock never casts its own commander:** 0 casts in 12 audit games.
- Cards it sat on with the mana for them: Putrefy and Reanimate (11 turns each), Convert to Slime (6), Binding the Old Gods (5), Culling Ritual and Demonic Covenant (3 each).
- Abilities never used: Haywire Mite, Suspicious Bookcase, Scavenging Ooze. Ishkanah was used once in 8 turns.
- Triggers Forge declines: Noxious Gearhulk's (10 times in validation) and Deathreap Ritual's (once or twice).
- Flagged never-cast: Winter and Nyx Weaver.

**2. Candidate:** `playbook/variants/death-toll-winter.json`, version 2
- R1: exile Nyx Weaver for a card once the library is ≤30, which stops its forced upkeep mill (added in v2).
- R2: rocks and ramp first.
- R3: Winter as soon as she is affordable. This is the main gain.
- R4: the self-mill engine while the library is ≥30: Polluted Cistern (its drain fires on every mill), Stitcher's Supplier, Nyx Weaver, Crawling Sensation, Cemetery Tampering.
- R5: the other engines: Demonic Covenant, Titania, Grist, Ob Nixilis, Whip, Deathreap Ritual, Into the Pit.
- R6: Deadbridge Chant only with ≥40 cards left.
- R7: Old Stickfingers at X 5 (at least 3), with ≥30 cards left. In v1 it was X max; v2 caps it.
- R8: activate Whip of Erebos.
- R9: Mulch, Grisly Salvage and Grapple with the Past with ≥25 cards left.
- R10–12 (holds, added in v2): stop Forge casting the same mill cards below those library floors.
- Triggers: accept Deathreap Ritual's draw (library ≥10) and Solemn's.
- Dropped: trigger rules for Winter, Cemetery Tampering, Crawling Sensation and Titania. Forge never asks about them as optional triggers, so they never fired.
- Attack: go_wide, highest life first, min 3 attackers.

**3. Validation** (seeds 27101–27140). **The rules were changed after validation games had been seen.** Version 1 lost 2 of 40 games to the seat milling itself out, so I added R1, the X cap and the holds, and dropped the dead trigger rules. I checked v2 on the tuning seeds first (27021–27040: +2.35 turns, 95% +1.66 to +3.04, faster in 19 of 20), then reran validation. The v2 figure is flattered.

| Arm | Games won | Kill turn | Stock − arm (95%), 38 pairs | Faster / same / slower |
|---|---|---|---|---|
| Stock | 40/40 | 12.03 | | |
| v1 | 38/40 | 10.16 | +1.84 (+1.25 to +2.44) | 31 / 3 / 4 |
| v2 | 38/40 | 10.13 | +1.87 (+1.30 to +2.44) | 31 / 3 / 4 |

- The same two games (25 and 28) still end with the seat milled under v2. The big mills there are not cast from hand. In game 28, Deadbridge Chant ("mill ten") came onto the battlefield without being cast at 30 cards left. Most likely Winter's delirium return or Cemetery Tampering's free hideaway play brought it, and Forge chooses both. Game 25 ran out through Nyx Weaver, Deadbridge, Millipede and Winter's attack mills.
- Pair files are in `<scratch>/batch/death-toll/`: `death-toll-pair.json` (v2) and `death-toll-pair-v1.json` (v1).

**4. Rules fired** (v2 validation, 40 games)
- Rules 1–9 fired: 2, 68, 40, 43, 68, 6, 7, 19 and 18 times. Winter was cast in every game.
- Trigger rules 1 and 2 fired 5 and 11 times.
- The holds (R10–12) have no counter of their own.

**5. What the format can't express**
- Which cards Winter's end-step trigger exiles and which permanent it returns. Forge exiles the whole graveyard, which switches off delirium for Grim Flayer, Gnarlwood Dryad, Demolisher Spawn and Ishkanah and empties it for Old Stickfingers, Formless Genesis and Whip of Erebos.
- Declining the forced or self-chosen mills (Winter's attack mill, upkeep mills, free hideaway plays) when the library is low. There is no "don't attack with Winter" rule.
- Bojuka Bog's target, Reanimate's target, and Dim Oubliette's unlock.

**6. Recommendation:** send it to 200 tables. It gains about 1.9 turns in goldfish, almost entirely from casting a commander stock never casts. Watch two things there: self-milling in longer games (2 of 40 games here), and the attack choice.

**7. Answers for the second pass** (none of them flagged never-cast)
- Putrefy: destroy an artifact or creature.
- Convert to Slime: destroy up to one artifact, one creature and one enchantment; Ooze token with delirium.
- Binding the Old Gods: chapter I destroys a nonland permanent.
- Noxious Gearhulk: may destroy a creature on entering (Forge declines it in goldfish).
- Culling Ritual: destroys every nonland permanent of mana value 2 or less (wipe).
- Deluge of Doom: all creatures −X/−X, X = card types in graveyard (wipe).
- Vile Mutilator: each opponent sacrifices a nontoken enchantment and a nontoken creature.
- Professor Onyx −3: each opponent sacrifices their biggest creature.
- Ob Nixilis −3 and Grist −2: destroy a creature (Grist can also hit a planeswalker).
- Haywire Mite: exile a noncreature artifact or enchantment.
- Inscription of Abundance: a fight mode.
- Arachnogenesis (fog): Spider tokens and combat damage prevention.
- Scavenging Ooze and Bojuka Bog: graveyard hate.

**8. How an owner expects it to play**
An owner casts Winter on turn 3 or 4 and swings with her for the mill. They fill the graveyard to four card types for delirium, drain the table with Polluted Cistern, then reanimate and recur big threats, with Demonic Covenant and Titania closing. The candidate now does the first part, which stock never does. It still can't choose what Winter exiles: a person exiles just enough for four types and keeps delirium and a stocked graveyard, while Forge empties it every turn. It also can't stop milling when the library runs low, which a person who owns this deck watches all game.
