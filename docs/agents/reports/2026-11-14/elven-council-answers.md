<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Elven Council: answer rules (candidate `answers`, version 2)

The rules fire when they should and do what they were written to do. My seat won only 2 of the 24 local tables, which is far too few games to read anything into, but it is lower than the league rate (18%) would predict, so the 200 tables should settle it.

**1. The answer cards in the league games** (league-run #3, 200 games with this seat, 36 wins)

| Card | Seen | Cast | In hand at a loss | Notes |
|---|---|---|---|---|
| Beast Within | 60 | 0 | 41 | Forge never casts it (`AI:RemoveDeck:All`) |
| Mystic Confluence | 50 | 0 | 34 | Same flag |
| Devastation Tide | 66 | 33 | 21 | Forge cast it at any position, even at 40 life with six permanents a side; the seat won 7 of those 33 games |
| Raise the Palisade | 56 | 40 | 14 | Forge picks Elf, so it is nearly one-sided for us |
| Galadhrim Ambush | 61 | 23 | 21 | Cast during combat on other players' turns |
| Heroic Intervention | 60 | 37 | 25 | Instant, a response |
| Lignify / Windswift Slice / Trap the Trespassers / Reclamation Sage | 59–66 | 54–61 | 0–13 | Already cast well; left to Forge |

**2. Rules added** (all 14 shipped rules are kept, in their order; no attack block, as shipped)
- **Rules 1–3, Devastation Tide**, on Tricky Terrain's wipe conditions. It fires when an opponent has 7 or more creatures and more power than we have, plus one of:
  - we have 5 creatures or fewer;
  - that opponent is wider than us and could kill us next turn;
  - only one opponent is left.
- **Rule 4, Raise the Palisade** in the first main phase when an opponent has 4 or more creatures, we have 2 or more Elves and 2 or fewer Insects (so Forge still chooses Elf). Casting it before combat clears blockers, and what comes back is summoning-sick.
- **Rule 5, the same card when `threat >= 10`.** This covers decks with a few large creatures: one local game was lost to Eldrazi Incursion with the card held for 8 turns because that opponent never had 4 creatures.
- **Rule 8, Beast Within when `threat >= 7`.** Forge picks the target (a permanent of mana value 4 or more).
- **Dropped: Mystic Confluence** as a first-main play. Both casts resolved with no effect at all (no card drawn, nothing returned), so five mana went for nothing.
- No hold on Devastation Tide. A hold might block Forge's cheap miracle cast, so Forge's own casts stay.

**3. Local tables** (24 games, seeds 20263030–32)
- **Beast Within:** seen 8, cast 6. It destroyed Cloud (a commander), Gray Merchant, Rampaging Baloths, Twins of Discord, Anikthea and Elspeth. The one loss with it in hand was a game stuck on 3 lands.
- **Raise the Palisade:** seen 6, cast 4, one of those countered. The casts that resolved returned 8, 8 and 10 opposing permanents (tokens die) and none of ours. Rule 5 never fired.
- **Devastation Tide, by the rules:** 4 casts. Three were good: 6 of ours returned against 34 of theirs, 10 against 38, and 5 against 35. The fourth was the last-opponent rule, which returned 10 of ours (4 of them Insect tokens, which die) against 8 of theirs, and the seat lost that game.
- **Devastation Tide, by Forge:** 2 casts, one of them a waste (2 opposing permanents on turn 10).
- Mystic Confluence was in hand at 6 losses once dropped.

**4. What the rule format cannot express**
- Mystic Confluence: its modes are chosen as it resolves, and its real use is on an opponent's turn.
- Galadhrim Ambush (combat on other players' turns), Heroic Intervention and Swan Song (responses).
- Any check that Forge chose Elf for Palisade; the conditions only make it likely.
- A comparison of two metrics, such as Elves against all creatures (only a number is allowed on the right).
- What a symmetric wipe would cost each side; the conditions only proxy for it.
- A cap on Forge's own Devastation Tide casts that would still keep the miracle.

**5. Recommendation:** `playbook/variants/elven-council-answers.json`. Yes, send it to 200 tables.
