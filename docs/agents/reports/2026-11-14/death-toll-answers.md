<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Death Toll answers candidate: report**

My candidate is `playbook/variants/death-toll-answers.json` (variant `answers`, of `death-toll-winter.json`, version 3). Its cast rules are byte-identical to the `cast` object recorded in the run.json of my last local run. Only `notes` was edited during that run, and no rule changed after it.

**1. Answer cards in the exam (200 tables)**
Figures are for the candidate arm, from the playtest report; stock is in brackets.

| Card | Drawn | Cast | In hand at a loss |
|---|---|---|---|
| Deluge of Doom (all creatures −X/−X) | 54 | 0 (stock 0/57) | 31 (41) |
| Culling Ritual (destroys MV ≤2 permanents, so every token) | 40 | 27 | 7 |
| Putrefy | 44 | 44 | 1 |
| Convert to Slime | 27 | 19 (33/36) | 8 |
| Binding the Old Gods | 47 | 24 (42/52) | 14 |
| Noxious Gearhulk | 52 | 25 (48/58) | 16 |
| Vile Mutilator | 45 | 9 (31/48) | 16 |
| Professor Onyx | 39 | 18 (22/29) | 15 |
| Ob Nixilis / Grist | 47 / 53 | 44 / 52 | 3 / 1 |
| Arachnogenesis (fog) | 49 | 21 (27/44) | 16 |

- **Losses:** the seat died at about 25 life on its last turn to one opponent's swing (76 damage on average).
- **Milled:** 12 of its 139 losses, against 3 of 161 for stock.
- **Gearhulk's enters trigger:** Forge took it on 75 of 76 casts, always on an opponent's creature, so it needs no trigger rule.
- **Deluge's X is the problem:** Winter's end-step trigger exiles the whole graveyard. At the start of our turn X was 0–1 on 59% of the turns Deluge was in hand. Before the end step, after Winter's attack mill, it was 4+ on 156 of 179 turns.

**2. Rules added and changed (27 rules)**
- **R2 and R5, Culling Ritual:** cast when an opponent has 6+ creatures and more than we do, or when a lethal threat stands (`threat >= life`).
- **R3, Deluge in main 2:** when an opponent has 6+ creatures and more creatures and power than we do. Main 2 is where X is high. In the losses the biggest opposing board had 15 nonland permanents (median) against our 6; in the wins it was 8 against 6.
- **R4, Deluge emergency:** in either main phase when `threat >= life`, `opp_power > power` and an opponent has 3+ creatures.
- **R9, removal:** Binding, Putrefy and Convert to Slime, after the mill engine. Forge picks the targets.
- **R13–15, threats and edicts:** Gearhulk (when an opponent has a creature), Vile Mutilator (when we have a token to sacrifice and an opponent has a creature), then Hornet Queen, Demolisher Spawn, Giant Adephage, Moldgraf Monstrosity, Onyx, Wrenn and Seven, Ishkanah and Rendmaw, biggest first.
- **R19, `{"forge":"unnamed"}`:** placed after the base's mill spells. It lets Forge choose among Reanimate, Formless Genesis, Inscription, Sakura-Tribe Elder, the two-drops and the planeswalker abilities before the mid creatures and draw spells.
- **R20–22:** Millipede, Carrion Grub and Ursine Monstrosity with library ≥ 30 (held below that by R26); Grim Flayer and Burnished Hart; Harmonize and Night's Whisper with library ≥ 15.
- **Changed base rule:** I split Demonic Covenant out of base rule 5 into R10 (library ≥ 20) and hold it below 20 (R27). It mills two cards every end step, and the base lost 12 games to an empty library.
- **Everything else of the base is kept in its order.** The threats now come before Stickfingers, the Whip activation and the mill spells, which only matters once there are 5+ lands. Nothing was tried and dropped.

**"Cast LESS" list, card by card**
- **Own rule, a threat or edict (R13–15):** Hornet Queen, Wrenn and Seven, Gearhulk, Ishkanah, Onyx, Rendmaw, Demolisher Spawn, Giant Adephage, Vile Mutilator.
- **Removal (R9):** Binding the Old Gods, Convert to Slime.
- **Library-gated (R20):** Millipede, Carrion Grub, Ursine Monstrosity. The new hold explains part of their lower share; I think that is right, because they mill.
- **R21:** Grim Flayer, Burnished Hart.
- **R22 (library ≥ 15):** Harmonize, Night's Whisper.
- **Left to Forge through R19:** Formless Genesis. Its X is lands in a graveyard Winter keeps emptying, so a plain rule could make a 0/0.
- **Left to Forge:** Arachnogenesis. It is an instant fog, and rules act only in our own main phase.

**3. Local tables (seed 20263160, 8 games)**
The seat won 7 of 8, which is far too few games to mean anything. Per card, drawn → cast:

| Cards | Drawn → cast |
|---|---|
| Deluge of Doom, Culling Ritual, Putrefy, Convert to Slime | 3→2, 2→1, 1→1, 3→1 |
| Binding, Gearhulk, Mutilator, Onyx | 1→1, 2→2, 1→1, 1→0 |
| Hornet Queen, Wrenn and Seven, Ishkanah, Rendmaw | 1→0, 2→2, 3→2, 2→1 |
| Demolisher Spawn, Giant Adephage, Millipede, Carrion Grub | 1→1, 4→3, 2→0, 3→1 |
| Ursine Monstrosity, Harmonize, Night's Whisper, Formless Genesis | 2→0, 2→2, 2→2, 4→2 |
| Burnished Hart, Grim Flayer, Arachnogenesis | 2→1, 1→1, 3→1 |

What the answers did:
- **Deluge, cast twice:**
  - Once on turn 8 while stuck on 2 lands: 26 opposing permanents died for 1 of ours, and the seat won.
  - Once in main 2 at 53 life, opponents at 7 and 9: 16 opposing permanents died for 8 of ours, Winter, Hornet Queen and Adephage among them. The seat won, but that cast was costly. A condition on graveyard types would fix it, and the format has none.
- **Culling Ritual:** 7 opposing permanents, none of ours.
- **Vile Mutilator:** 4 opposing creatures; its sacrifice cost was Whip of Erebos.
- **Hornet Queen and Onyx in game 4:** waited behind the base's engines (Titania, Whip, Grist, Deadbridge).

I could not use the trace: the `-Dvibefish.trace` lines did not appear in `play.log`. From the events, the unnamed cards cast on our own turns were Reanimate, Formless Genesis, Whispersilk Cloak, Bookcase, Gnarlwood Dryad, Grovedancer, Ooze, Inscription, Haywire Mite, Obsessive Skinner and Sakura-Tribe Elder. Library fell to 12 and 4 in two games; there was no milled loss.

**4. What the format cannot say**
- Graveyard card types, which are Deluge's X and delirium.
- Which cards Winter exiles; it empties the graveyard.
- Keeping mana open for Arachnogenesis on opponents' turns.
- Declining the "may mill" upkeep effects (Crawling Sensation, Cemetery Tampering) and Winter's attack mill.
- Commander tax as a condition: Winter's recasts took the mana on 256 of the 1,248 turns where a starved card was affordable.

**5. Recommendation**
Send it to 200 tables, as the candidate arm beside the `winter` arm on seed 20261280. Watch two things: Deluge in main 2 hitting our own board, and milled losses.
