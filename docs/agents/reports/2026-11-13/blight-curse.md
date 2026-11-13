<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Blight Curse (Auntie Ool, Cursewretch): report**

**1. The audit** (12 stock goldfish games, seeds 21002-21013). Stock won 11 of 12, with a mean kill turn of 15.6 (median 14). It left 50% of its mana unspent. On 54% of turns it ended holding a card the spare mana would have paid for, and on 32% of turns it cast nothing.
- **Cards it sat on:** mostly answers with no target in goldfish: Infernal Grasp, Putrefy, Fire Covenant, Persist, Black Sun's Zenith, Chain Reaction, Assassin's Trophy, Skinrender. Beyond those:
  - Channeler Initiate: kept on 33 of the 54 turns it was in hand.
  - Cathartic Reunion.
  - Painful Truths and Harmonize: held from turn 1 to the end of a game while the seat was stuck on four lands.
- **Abilities it never used:** Grim Poppet, Carnifex Demon, Ferrafor, Wickersmith's Tools (sacrifice), Nesting Grounds, Ifnir Deadlands, Wickerbough Elder and Devoted Druid. It used Vraska's +0 once in 33 turns and The Scorpion God 3 times in 30.
- **Triggers declined:** only Hapatra's combat trigger, correctly (in goldfish it can only aim at our own creatures).
- **Never cast:** Fire Covenant and Black Sun's Zenith are flagged `AI:RemoveDeck:All`. Devoted Druid carries the same flag but was cast here.

**2. The candidate:** `playbook/variants/blight-curse-wretch.json`. The rules are numbered as in the file.
1. **Hold Blowfly Infestation until an opponent has two creatures.** In goldfish its mandatory trigger aims at our own Snakes, and with Hapatra and Auntie that loops until Forge calls the game a draw or the seat runs out of cards.
2. **Hold Eventide's Shadow until 40 cards are left.** It drew 18 cards at once.
3. **Cast mana first.** Devoted Druid is cast as a plain mana creature.
4. **Channeler Initiate only onto an empty board,** so the three counters land on itself. Otherwise Forge put them on Auntie, Devoted Druid or Dread Tiller.
5. **Auntie at once.**
6. **The engines:** Hapatra, Lasting Tarfire, Sinister Gnarlbark, Grave Venerations, Chimil, Vraska, Evolution Sage, Oft-Nabbed Goat and Puca's Covenant.
7. **Flourishing Defenses only with 40 or more cards left and no Midnight Banshee in play.** Trigger rule 1 also declines its Elf below 30 cards: in tuning, Banshee plus Flourishing plus Auntie decked the seat.
8. **Vraska's +0 every turn.**
9. to 12. **Free counters on our own "sponges":** Grim Poppet's counters on Oft-Nabbed Goat, Tree of Perdition and Gnarlbark (once a turn), and Ferrafor's doubling on the Goat. Each counter draws a card through Auntie and triggers Tarfire.
13. and 14. **Draw spells with 30 or more cards left;** Cathartic Reunion only with 4 or more cards in hand.
15. **Threats, most expensive first.**
16. to 18. **The Scorpion God's counter on the same sponges.**
19. **Cash in Wickersmith's Tools from turn 10,** in the second main phase. The rules cannot read its charge counters.

Trigger rule 2 always accepts Dread Tiller, Puca's Covenant, The Reaper and Necroskitter. The attack is the batch default `go_wide`.

Dropped: letting Forge pick Channeler Initiate's target with creatures already on board.

**3. Validation** (seeds 21102-21141, 40 games per arm; the rules were not changed after I saw these games):

| | Won | Kill turn mean / median | Mana unspent |
|---|---|---|---|
| Stock | 36/40 (3 loop draws, 1 milled) | 13.53 / 13 | 34% |
| Playbook | 39/40 (1 milled, ended at the turn cap) | 12.56 / 13 | 22% |

On the 35 seeds both arms won, the playbook is **1.06 turns faster (95% +0.45 to +1.67)**: faster in 21, the same in 10, slower in 4. The pair file is `<scratch>/batch/blight-curse/blight-curse-pair.json`.

**4. Which rules fired** (validation): rule 3: 114, 4: 5, 5: 40, 6: 139, 7: 12, 8: 70, 9: 9, 10: 16, 11: 1, 12: 3, 13: 94, 14: 17, 15: 224, 16 to 18: 8/8/2, 19: 8. The holds vetoed Forge 8 times. Trigger rules: 4 declines and 171 accepts. Every rule fired at least once.

**5. What the rule format cannot express:**
- **A cap on Auntie's draws.** They are mandatory. The playbook arm still decked once, after Flourishing Defenses was cast free off Chimil's discover and Midnight Banshee was brought back by Aberrant Return. Neither path goes through a cast rule.
- **Aiming a creature's enters trigger:** Channeler Initiate, Skinrender, Contagion Clasp, Dread Tiller.
- **Reading charge counters** on Wickersmith's Tools.
- **Choosing what proliferate adds to,** and what Eventide's Shadow removes.
- **Aiming Hapatra's combat trigger.**

**6. Recommendation:** send it to 200 tables. The gain is about one turn with an interval clear of zero, and it comes from the deck's own engine: more draw, the sponges, Vraska, the commander on time. The holds also remove goldfish loops that are not this deck's play. At the tables, the Blowfly hold releases as soon as opponents have creatures.

**7. The deck's answers:**
- **Black Sun's Zenith:** X -1/-1 counters on every creature (never cast by Forge's AI).
- **Chain Reaction:** damage to every creature, equal to the number of creatures.
- **Soul Snuffers:** a -1/-1 counter on every creature.
- **Midnight Banshee:** a counter on every nonblack creature each upkeep.
- **Carnifex Demon:** activated ability, a counter on every other creature.
- **Village Pillagers:** 1 damage to each opponent's creature.
- **Assassin's Trophy:** any permanent an opponent controls.
- **Infernal Grasp, Terminate:** a creature.
- **Putrefy:** an artifact or creature.
- **Cathartic Pyre:** 3 damage to a creature or planeswalker.
- **Fire Covenant:** X damage split among creatures (never cast by Forge's AI).
- **Incremental Blight:** three creatures, with 1, 2 and 3 counters.
- **Skinrender:** 3 counters on a creature.
- **Binding the Old Gods:** a nonland permanent.
- **Vraska -2:** turns a creature into a Treasure.
- **Liliana -3:** destroys a creature that has a -1/-1 counter.
- **Wickerbough Elder:** an artifact or enchantment.
- **Glissa Sunslayer:** an enchantment, or removes counters.
- **Ifnir Deadlands:** 2 counters on an opponent's creature.
- **Grim Poppet and The Scorpion God:** a counter each on any creature.
- **Kulrath Knight:** creatures with counters cannot attack or block.

There are no counterspells and no fogs.

**8. How a person plays it.** Auntie comes down on turn 3 or 4. From then on every -1/-1 counter is either a card for you or a point of life off an opponent. Your own throwaway creatures (Goat, Tree, Channeler, Gnarlbark) soak up counters to draw cards. Wither creatures, Hapatra, Tarfire and the death triggers grind the table down until Grave Titan, the fliers, or a Tree swap end it. An owner also plays on other players' turns, and that is where this candidate falls short. It plays its own main phase better than stock, but its counters still go on its own creatures because goldfish has nothing else to hit. Aiming at the opponent who matters, timing the removal, and sizing Black Sun's Zenith are all still Forge's. It can also draw itself out of cards when the counter engines snowball.
