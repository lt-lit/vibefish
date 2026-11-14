<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Blight Curse answer rules: report

**Candidate file:** `playbook/variants/blight-curse-answers.json` (`variant: answers`, `of: playbook/variants/blight-curse-wretch.json`, version 2, 30 cast rules). The attack block and both trigger rules are unchanged. The playbook recorded in the second local run's `run.json` is identical to this file. I recommend sending it to 200 tables, as a playbook-only arm on seed 20261260 joined with ab-run #27's stock arm and `wretch` arm.

### 1. Answer cards in the exam (ab-run #27, 200 tables, candidate arm; stock arm in brackets)
Counts are games drawn / games cast / games where the card was in hand at a loss.

| Card | Candidate | Stock |
|---|---|---|
| Black Sun's Zenith | 53/0/38 | 60/0/43 |
| Fire Covenant | 62/0/42 | 49/0/32 |
| Soul Snuffers | 64/2/37 | 53/7/32 |
| Chain Reaction | 57/14/34 | 62/41/11 |
| Midnight Banshee | 51/18/22 | 50/36/10 |
| Incremental Blight | 51/13/29 | 56/50/5 |
| Skinrender | 55/16/22 | 56/29/18 |
| Village Pillagers | 62/40/26 | 51/40/8 |
| Binding the Old Gods | 42/11/16 | 46/33/8 |
| Liliana, Death Wielder | 52/8/26 | 51/34/12 |
| Instants: Infernal Grasp, Putrefy, Terminate, Assassin's Trophy, Cathartic Pyre | cast in 92–98% of games drawn | same |

On the seat's last own turn of a loss the median board was 2–3 of our creatures against 10–11 for the widest opponent, at 10–15 life.

### 2. Rules added (numbers as in the new file)
- **4–5. Chain Reaction, else Black Sun's Zenith** (X max, at least 3), placed above the commander.
  - When: the widest opponent has 6 or more creatures and more power than we have, and we have 3 creatures or fewer. In the exam logs this held on one of the last three own turns in 113 of 159 losses and 10 of 41 wins.
  - Or: that opponent is wider than us and `threat >= life`.
- **8. Village Pillagers, Soul Snuffers, Midnight Banshee** once an opponent has 4 creatures. These spare most of our side and, with Auntie, cost each opponent a life per creature. They sit below Auntie so she still comes down on turn 4.
- **9. Carnifex Demon's {B} ability** (a counter on every other creature), with Auntie out and an opponent wider than us with 4 or more creatures. Neither pilot ever used it in the exam.
- **10–11. Liliana's −3, else her +2.** Her abilities were starved the same way as the unnamed cards.
- **13. Binding the Old Gods and Incremental Blight**, after the engines. Forge aims the Blight.
- **14. Skinrender** while an opponent has a creature.
- **15. Blowfly Infestation** once an opponent has 3 creatures.
- **22. The threats before the draw spells** while an opponent has more power than we have.
- **24. Eventide's Shadow** only with 40 or more cards in library, 25 or more life and 3 or fewer cards in hand.
- **26.** The base's threat list with five cards added.

**Dropped:** Fire Covenant. Its X is paid in life, which a rule cannot set, and Forge declined it every time it was offered (0 casts in 6 games drawn).

### 3. Local tables (16 games: 8 on seed 20263110, 8 on 20263111)
Counts are games drawn / games cast.
- **Wipes:**
  - Black Sun's Zenith 5/5: one cast killed 15 creatures in a game the seat won; another came at 5 life heads-up and was too late.
  - Chain Reaction 3/1: its one cast killed 17 creatures.
  - Soul Snuffers 8/8, Midnight Banshee 8/6, Village Pillagers 5/4.
- **Removal and threats:**
  - Incremental Blight 8/6, all three targets on opposing creatures every time.
  - Skinrender 9/8, Binding the Old Gods 4/2, Aberrant Return 4/2.
  - Carnifex Demon 8/4; rule 9 activated it twice, both in the second run.
- **Never cast:**
  - Liliana 4/0: she costs seven and the seat never had seven mana with her in hand.
  - Eventide's Shadow 6/0 and Fire Covenant 6/0.
- **Rules that never fired:** 10–11 (Liliana never landed).
- **Rule 9 in the first run:** it first named its ability by a piece of text, and it did not fire in game 1 although the board met its conditions; the cause is unconfirmed. Without the text it fired in the second run.
- **Backfires:** none seen.
- **Wins:** 2 of 8, then 4 of 8. Far too few games to mean anything.
- **Cards still held:** with the rules firing as intended, the seat still lost holding 5.0–5.8 nonland cards.

### 4. What the format cannot express
- **Fire Covenant:** its X is paid in life, and its damage is split across opposing creatures.
- **Answers on other players' turns:** the instants are already cast by Forge then.
- **Sizing Black Sun's Zenith:** it cannot be sized to spare Auntie, since a rule cannot see opposing toughness.
- **Colour:** whether opponents' creatures are black, which decides how one-sided Midnight Banshee is.
- **Vraska's −2:** the target would be Forge's choice, so I did not write it.
- **Eventide's Shadow:** which counters to remove is chosen as it resolves.

### The "cast LESS" list, card by card
- **Incremental Blight:** rule 13, after the engines (6 of 8 cast).
- **Aberrant Return:** added to the threat list, rules 22 and 26 (2 of 4).
- **Liliana, Death Wielder:** added to the threat lists; rules 10–11 use her abilities (0 of 4, unaffordable).
- **Binding the Old Gods:** rule 13, unconditional (2 of 4).
- **Puppeteer Clique:** added to the threat lists (0 of 2 drawn locally).
- **Eventide's Shadow:** the base's hold until 40 cards is kept as right, since it costs a life per counter and the seat is often low. Rule 24 adds a narrow cast (0 of 6).
- **Chain Reaction:** rules 4–5 (1 of 3).
- **Midnight Banshee:** rule 8, plus the threat lists (6 of 8).
- **Ferrafor, Young Yew:** added to the threat lists (1 of 3).
- **Blowfly Infestation:** rule 15 at 3 opposing creatures; the base's hold is kept for goldfish (3 of 4).
- **Dread Tiller, The Scorpion God, Carnifex Demon, Village Pillagers:** already threats; rule 22 now casts them ahead of the draw spells when behind. Pillagers is also in rule 8 and Carnifex has rule 9.
- **Skinrender:** rule 14 (8 of 9).

### Base rules moved or changed
- **Base 1–3, 4, 5:** now rules 1–3, 6, 7. The two wipe rules are inserted after mana and before Auntie, because Auntie would die to them.
- **Base 6 (engines):** now 12, after rules 8–11.
- **Base 7–12:** now 16–21, unchanged.
- **Base 13 (draw spells):** now 23. It now yields to rule 22 whenever an opponent has more power than we have.
- **Base 14:** now 25, unchanged.
- **Base 15 (threats):** now 26, with Liliana, Ferrafor, Aberrant Return, Midnight Banshee and Puppeteer Clique added.
- **Base 16–19:** now 27–30, unchanged.
- **Vraska's +0:** left as it is, since it costs no mana.

Scratch work (scripts, local runs, playtest reports) is in `<scratch>/batch/answers-blight-curse/`.
