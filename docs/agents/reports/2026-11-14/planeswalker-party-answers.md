<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Answer rules for Planeswalker Party: candidate written and checked at 16 local tables**

**1. The answer cards in the league games** (`league-run` #3: this seat played 200 games and won 29; opponents sent 15.4 attackers a game at its walkers)

| Card | Drawn | Cast | In hand at a loss |
|---|---|---|---|
| Urza's Ruinous Blast | 47 | 6 | 31 |
| Guff Rewrites History | 46 | 0 | 33 |
| Promise of Loyalty | 74 | 24 | 39 |
| Nevinyrral's Disk | 53 | 19 (11 activations) | 24 |
| Blasphemous Act | 61 | 38 | 10 |
| Norn's Annex | 55 | 29 | 22 |
| Wall of Denial | 49 | 21 | 26 |
| Silent Arbiter | 47 | 14 | 17 |
| Onakke Oathkeeper | 57 | 39 | 15 |
| Semester's End | 50 | 21 | 27 |
| Path to Exile / Swords to Plowshares | 57 / 64 | 55 / 60 | 1 / 3 |

- Two loyalty abilities were never used. Chandra, Awakened Inferno's -3: Forge took her +2 all 145 times. Elspeth's -3: 0 uses, against 113 of her +1.
- Every planeswalker in this deck is legendary and none is a creature on our turn, so all its wipes are close to one-sided. They cost us tokens and mana rocks.

**2. Rules added** (version 2; the shipped rules, triggers and attack are kept, in order)
- **At the top, before the turn's other plays:**
  - Ruinous Blast when an opponent has 4+ creatures and more power than us, or can attack us for 12+ and has more power.
  - Blasphemous Act and the Disk's activation on the first of those boards.
  - Chandra's -3 when an opponent has 4+ creatures and more creatures than us.
  - Elspeth's -3 when one opponent can attack for 12+ with 3 or fewer creatures (so at least one has power 4+) and has more power.
  - Promise of Loyalty on the same board as Blast when we have 2 or fewer creatures.
  - The thresholds are the ones Hail, Caesar uses (4 creatures, a threat of 12). They were not tuned on these games.
- **After the mana rocks, the attack deterrents:**
  - Onakke Oathkeeper at once.
  - Norn's Annex and the Disk when an opponent has 3+ creatures.
  - Silent Arbiter on the Blast board.
- **One shipped rule changed:** the last creature list now also includes Wall of Denial, Fog Bank, Norn's Annex and the Disk.
- **Dropped:** Gideon's +2 (an opponent's creatures must attack Gideon). It never fired in 8 games with Gideon out. It targets an opponent, so Forge's own logic has to agree, and that logic for this delayed trigger declines (the card is `AI:RemoveDeck:All`, and its script notes the missing AI).

**3. Local tables** (seeds 20263040 and 20263041, 16 games, read from the event logs)
- Every new rule fired as intended at least once, except the Disk's play rule. Its activation fired once.
- Under the candidate:
  - Ruinous Blast: drawn 3 times, cast 3 times. It removed 44 opponent permanents against 7 of ours, then 26 against 5.
  - Blasphemous Act: drawn 7, cast 6.
  - Promise of Loyalty: drawn 8, cast 6.
  - Norn's Annex: 5 of 5 cast. Silent Arbiter: 5 of 6. Onakke Oathkeeper: 3 of 3.
  - Chandra's -3 killed 9 opponent creatures against 2 of ours.
  - Elspeth's -3 fired twice; the second also killed our own Jaya's Phoenix.
- What could be a backfire: Promise of Loyalty once cost us 9 permanents against 18 of theirs.
- Wins: 3 of 16. That is too few games to mean anything.

**4. What the rule format cannot express**
- **Guff Rewrites History:** it needs a target from every player, and Forge never agrees to cast it.
- **Semester's End:** it is an instant that saves the walkers, so it is wanted on an opponent's turn.
- **Gideon's +2:** it needs an aimed opponent.
- **Walker counts:** no condition can count planeswalkers or read loyalty. That is needed to time protection and minus abilities.
- **Who to aim at:** removal cannot be aimed at the opponent who is attacking our walkers.

**5. Recommendation**
- The file is `playbook/variants/planeswalker-party-answers.json`. Its cast rules are identical to the ones played in the second batch.
- I recommend sending it to 200 tables: stock, the shipped version and this candidate on tables of their own.
