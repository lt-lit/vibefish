<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Token Triumph: answer rules, second attempt (`answers2`)

**1. The answer cards in the 200 league games** (`league-run` #3: the seat won 60 and lost 140)

| Card | Seen | Cast | In hand at a loss |
|---|---|---|---|
| Hour of Reckoning | 35 | 12 (all by Forge) | 13 |
| Citywide Bust | 54 | 17 | 18 |
| Conclave Tribunal | 38 | 28 | 7 |
| Nullmage Shepherd | 56 | 44 cast; its ability used **0** times (Forge never uses it) | 15 |
| Path to Exile / Devouring Light / Aura Mutation / Sylvan Reclamation / Reclamation Sage | 26 / 49 / 24 / 40 / 56 | 25 / 41 / 17 / 27 / 44 | 0 / 8 / 5 / 0 / 10 |

In the games it won while holding Hour of Reckoning, the seat was usually the one ahead, and Forge held the wipe. The losses with a wipe in hand were mostly games where the seat was behind on board: Limit Break with nine nontoken creatures, Elven Council with six, Caesar's board. At those moments our side had 0 to 3 nontoken creatures.

**2. Rules added.** All shipped rules are kept unchanged and in order. There is no attack block, as shipped. Version 5.
- **Rules 1–8, Hour of Reckoning.** Cast before combat when some opponent has more power than our whole board, at least 8 power and at least 4 creatures, and the wipe would cost us at most 3 nontoken creatures. That last part is a ladder: tokens ≥ k with creatures ≤ k+3, for k = 0, 2, … 14. Replayed over the league, it would fire in 12 of 26 games, against 6 to 11 nontoken creatures of theirs.
- **Rule 9, Citywide Bust.** Cast when behind on power with an opponent at 8 or more. It is blocked while we control any of our own toughness-4 creatures, Champion of Lambholt, Collective Blessing or Dictate of Heliod. In the league, turns when we were behind and our side was clean had a toughness-4 opposing creature on 107 of 110 turns; the rule would fire in 32 of 50 games, with a median of 3 creatures hit.
- **Rule 10, Conclave Tribunal.** Cast first in the turn when an opponent has 6 or more power and more than our board. Forge still picks the target.
- **Rule 23, Nullmage Shepherd.** Activated in the second main phase when we have 4 or more untapped creatures that can attack and `life > threat`. Forge picks the target.
- Nothing was tried and dropped. Forge's own casts are not held back, so these rules only add casts when the seat is behind.

**3. Local tables: 16 games, the seat won 4 (too few games to mean anything).**
- **Hour of Reckoning:** in hand in 5 games, cast in 4.
  - By rule twice: on own turn 12 it cost us 0 creatures for 5 of theirs (Galadriel and three elves, plus Rose); on own turn 6 it cost us 2 for 7 of theirs (Zada, Omo, Rampaging Baloths, Goblin Warchief, Goblin Matron, Goblin Dark-Dwellers, Broadside Bombardiers).
  - Once by Forge while we were ahead (4 of ours for 11), and once countered by Swan Song.
  - Held in one loss: the seat was ahead on power, with four nontoken creatures (three of them mana creatures) until it died.
- **Citywide Bust:** drawn once and not cast; Champion of Lambholt blocked it, and the game was won. **This rule has never fired in a game**; I only know it parses.
- **Conclave Tribunal:** cast 4 of 4, twice by the new rule before the turn's other plays (Pashalik Mons; Galadriel).
- **Nullmage Shepherd:** 3 activations in 2 games, on Song of Eärendil, Bastion of Remembrance and Talisman of Conviction. Forge picked the targets, and one is a mana rock.
- Nothing backfired. One run, seed 20263090, hit the 2-hour background limit while waiting for a game slot; its first 4 games are counted, and the rest of it was not restarted.

**4. What the rule format cannot say**
- **Opponents' nontoken creature count.** Hour doesn't touch token boards, but `opp_creatures` counts tokens.
- **Toughness**, ours or theirs. Bust is guarded by card names only, and anthems from counters (Felidar, Rishkar, Commander's Insignia) can slip past that guard.
- **Subtraction.** Hence the ladder.
- **Targets.** Forge picks them for Tribunal, Nullmage and Sylvan Reclamation (which hits Sol Ring and Signets).
- **Off-turn play.** Devouring Light, Rootborn Defenses and Dauntless Escort (responding to a wipe) need instant-speed play on other players' turns.
- **Who is winning.** `opp_power` is the strongest single board, not the leader.

**5. File and recommendation**
The file is `playbook/variants/token-triumph-answers2.json`. I checked that its `cast` block matches the playbook recorded in the local runs. I recommend sending it to 200 tables as `token-triumph@answers2`, with stock and shipped arms on the same tables. The thing to watch is the Citywide Bust rule, which has not fired locally.
