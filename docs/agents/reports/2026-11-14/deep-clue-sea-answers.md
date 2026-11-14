<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Answer rules for Deep Clue Sea (`deep-clue-sea`)**

**1. The answer cards in the 200 games of `league-run` #3** (the seat won 74). "Cast" counts spell casts only; trigger activations are left out.

| Card | Seen | Cast | In hand at a loss |
|---|---|---|---|
| Farewell | 63 | 6 | 11 |
| Fumigate | 72 | 5 | 10 |
| Organic Extinction | 63 | 4 | 9 |
| Aerial Extortionist | 60 | 17 | 8 |
| Confirm Suspicions | 58 | 12 | 9 |
| Swords to Plowshares | 54 | 53 | 1 |
| Disorder in the Court | 51 | 50 | 0 |
| Junk Winder / Koma | 55 / 49 | 41 / 33 | 2 / 0 |

Each wipe sat in hand for about 380 of the seat's own turns. Most losses came from a wide token board: Zombie, Goblin, Soldier, Shark and Plant tokens dealt 40 to 96 of the damage. I rebuilt creature counts from the zone events and looked at our own turns with a wipe in hand and five or more lands:
- With the widest opponent at 8 to 12 creatures and more creatures than us, the seat died within two turn cycles 30 to 37% of the time. At 13 or more it was 36 of 96 turns. At 4 to 7 creatures it was about 24%.
- When the seat had at least as many creatures as the widest opponent (8 or more), it died that soon in 1 of 31 turns.
- At life 20 or less with an opponent on 6 or more creatures, 54 of 92 turns ended in death within two cycles.

**2. Rules added** (version 2; every shipped rule kept in order; no attack block, as shipped)
- Rules 1-3, Organic Extinction (spares artifact creatures, and the Clues help pay for it): cast when an opponent has 8 or more creatures and more than us, or when `threat >= life`, or when our life is 20 or less, an opponent has 6 creatures and `opp_power > power`.
- Rules 4-6, Fumigate: the same three. The count rule is off while Tangletrove Kelp is out; the threat rule also needs `opp_power > power`.
- Rule 7, Farewell: an opponent has 10 or more creatures, more creatures and more power than us, and neither Mechanized Production nor Kelp is out.
- Rule 8, Farewell: `threat >= life` with more opposing power. A first version also blocked this while Mechanized Production was out. One local seat then held Farewell at 18 life, with six Clues out, and died that cycle to nine 4/4 flying Angels, so I removed the block.
- Aerial Extortionist moved above the Morska rule, cast when `opp_power >= 8`. Locally it sat in hand at 8 to 13 lands while every turn's mana went to recasting Morska at a growing commander tax.
- The wipes sit above the engine rules, so the wipe comes before the turn's creatures.

**3. Local tables of bots** (16 games, seeds 20263010-20263012; the seat won 7, too few games to mean anything)
- Fumigate: seen 7, cast 5. Organic Extinction: seen 7, cast 3; improvise paid for it at 5 to 7 lands. Farewell: seen 5, cast 1; in two of the other games the seat never reached six lands. Aerial Extortionist: seen 5, cast 5.
- Each wipe took 10 to 27 opposing permanents for 0 to 8 of ours.
- The one Farewell cast took 20 of theirs and 19 of ours, 16 of them our Clues.
- Nothing backfired that I could see. The logs don't record which rule fired, because `playbook_stats` add up every playbook seat at the table. The rules where `threat >= life` was the deciding condition may never have fired.
- The first batch was stopped at its 2-hour limit after 4 games, mostly time spent queued for a slot. Those 4 finished games are included; the unfinished fifth was deleted.

**4. What the rule format cannot express**
- Farewell's modes: Forge picks them, and it exiles our Clues and artifacts along with everything else.
- Who Aerial Extortionist exiles: Forge picks the target. Every league cast took an opponent's permanent.
- Confirm Suspicions: a counterspell, played only in response, which the rules never see.
- Swords to Plowshares and Disorder in the Court are cast on other players' turns too, so the rules don't reach them; Forge already casts them almost every game.
- What a wipe would destroy on each side: I used creature counts as a stand-in.
- A cap on what we spend recasting Morska. That comes from the shipped rule order and is not changed here.

**5. File and recommendation:** `playbook/variants/deep-clue-sea-answers.json`. I recommend sending it to 200 tables as a playbook-only arm next to the shipped playbook and stock (seed 20261300).
