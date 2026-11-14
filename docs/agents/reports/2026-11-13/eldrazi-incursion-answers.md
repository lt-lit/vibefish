<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Eldrazi Incursion answer rules: report**

I added rules for three sweepers: All Is Dust, Selective Obliteration and Kozilek's Return. In 16 local tables they fired when they should and did not backfire. I recommend sending the file to 200 tables.

**1. The answer cards in the league games** (league-run #3; the seat played 200 games and won 50)

| Card | Seen | Cast | In hand at a loss |
|---|---|---|---|
| All Is Dust (sweeper that hits only coloured permanents) | 51 | 16 | 18 |
| Selective Obliteration (`AI:RemoveDeck:All`, so Forge never casts it) | 56 | 2 | 30 |
| Kozilek's Return | 57 | 29 | 13 |
| Eldrazi Confluence | 53 | 16 | 15 |
| Imprisoned in the Moon | 58 | 24 | 8 |
| Crib Swap | 50 | 38 | 8 |
| Ugin, the Ineffable | 62 | 43 | 10 |
| Warping Wail | 58 | 51 | 1 |

- **All Is Dust is effectively one-sided for this deck.** Nearly every permanent is colourless or devoid, Ulalek included. Our only coloured permanents are Garruk's Uprising, Awakening Zone and Imprisoned in the Moon.
- **When it was cast, it worked.** It took 5 to 14 opposing creatures and 0 to 2 of ours, and the seat won 13 of the 16 games where it was cast.
- **Losses where it sat in hand** had 7 to 10 lands against opposing boards of 8 to 40 creatures (g00253, g00114, g00419, g00464, g00345, g00147).

**2. Rules added**
These are rules 1 to 5, placed above the shipped rules. The shipped triggers and its 12 cast rules are unchanged and in their order. There is no attack block, as shipped. Version 2.
- **Rule 1:** All Is Dust when `opp_creatures >= 4`. This is a one-sided wipe, and 4 is the threshold Hail, Caesar uses for Ruinous Ultimatum.
- **Rule 2:** All Is Dust when `threat >= 12`, for one big creature such as Marit Lage or an equipped commander.
- **Rule 3:** Selective Obliteration when `opp_creatures >= 5`. A single-colour opponent can keep its whole board, so it waits for a bigger one. It sits below All Is Dust so the full wipe goes first when both can be cast.
- **Rule 4:** Selective Obliteration when `threat >= 15`.
- **Rule 5:** Kozilek's Return when `opp_creatures >= 5`. Forge holds it in about half its games; the cost is our Scion and Spawn tokens.

Nothing was tried and dropped.

**3. Local tables** (16 tables, seeds 20263070 to 20263072, every opponent under its playbook)
- **All Is Dust:** seen in 2 games where 7 mana came, cast in both, both won. One cast, copied by Ulalek, cleared the Limit Break, Wretched Ranks and Enduring boards, followed by a lethal swing. The other took 20 Token Triumph permanents and 2 of ours.
- **Selective Obliteration:** seen in 5 games, cast in 4.
  - The casts exiled 9 Wretched Ranks creatures plus 3 Enduring creatures in one game, and 8 Goblin Storm creatures in another. Single-colour decks still lost their boards.
  - The uncast one was correctly held below the threshold, in a game that was won.
- **Kozilek's Return:** cast in 2 of 2. One killed 7 opposing creatures and none of ours.
- **Unfired and backfired:** every new rule fired at least once. None of the three cards was in hand at any of the 6 losses, and nothing backfired.
- **Win count:** 9 wins, 6 losses and 1 draw. That is too few games to mean anything.
- **The draw** ran into the 30-minute clock on a Skittering Invasion chain of 127 copies. That is version 1's known copy-chain defect, not these rules.

**4. What the format cannot express**
- **Targets on the other side:** Crib Swap, Imprisoned in the Moon, Eldrazi Confluence, Warping Wail, Ugin's −3, Endbringer's abilities and Drowner of Hope's tap all need them. Forge picks those targets and already casts or uses most of these cards.
- **Instant-speed answers:** Ulamog's Nullifier is a flash counterspell and Kozilek's Return is an instant. The rules only act in our own main phase.
- **No colour count:** a condition cannot count opponents' coloured permanents, so All Is Dust cannot be fired by a board of enchantments or planeswalkers alone.
- **Selective Obliteration's colour choice:** each player picks a colour as the spell resolves, and that choice stays Forge's.
- **No cap on a copy chain:** this is the version 1 defect.

**5. File:** `playbook/variants/eldrazi-incursion-answers.json`. Its notes record what each rule was written from and the local check. Scratch scripts and results are in `<scratch>/batch/answers-eldrazi-incursion`.
