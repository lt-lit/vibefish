<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Limit Break answer rules: candidate `playbook/variants/limit-break-answers.json` (version 2)**

**1. The answer cards in the league games** (`league-run` #3, 200 games for this seat, 35 wins and 165 losses)

| Card | Seen | Cast | In hand on the last own turn of a loss |
|---|---|---|---|
| Vanquish the Horde (destroys every creature) | 55 | 29 | 18 |
| Austere Command | 45 | 14 | 22 |
| Ultimate Magic: Meteor (7 damage to every creature) | 42 | 0 | 5 |
| Decimate | 55 | 21 | 26 |
| Summon: Kujata | 50 | 22 | 22 |
| Yuffie, Materia Hunter (steals an artifact) | 32 | 0 | 21 |
| Dispatch | 50 | 0 | 32 |
| Clever Concealment | 43 | 0 | 30 |
| Chaos Warp / Cloud's Limit Break / Vandalblast / Holy | 51/50/55/43 | 47/50/44/25 | 3/2/8/6 |

- Meteor was never cast because Forge foretells it (49 times hand to exile) and then never casts it from exile.
- The seat loses to wide boards. On its last own turn of a loss it had 3 creatures (median) against 11 for the widest opponent.
- An opponent had 5 or more creatures, and more than the seat, in 144 of the 165 losses and in 7 of the 35 wins.

**2. The rules added** (every shipped rule is unchanged and in its order; no attack block, as shipped)
- **Rule 3:** Vanquish the Horde, else a hard cast of Meteor from hand, when an opponent has 5 or more creatures and both more power and more creatures than we have. The wipe also kills our creatures, but the equipment stays and Cloud comes back from the command zone. The rule sits above Cloud's rule, so he is recast after the wipe.
- **Rule 4:** the same two cards when an opponent could kill us next turn (`threat >= life`) and has more power than we have.
- **Rule 5:** Forge may not cast those two itself. In the league, 8 of its 43 Vanquish and Austere casts came when the opponents' boards were not that big.
- **Rule 2:** Ultimate Magic: Holy (our permanents indestructible) just before a wipe, with 9 mana and at least 2 creatures of ours.
- **Rules 11 to 13:** Decimate is tried before the creatures; Summon: Kujata is cast when an opponent has 2 creatures; Yuffie, Materia Hunter is cast whenever possible.
- **Dropped, Austere Command:** cast by a play rule it resolves with no mode chosen and destroys nothing. In one local game it did that against 13 opposing creatures. Forge's own casts of it did destroy things in the league (5 to 35 opposing permanents each), so it stays Forge's.
- **Dropped, Dispatch:** Forge's logic never agreed to cast it, though it sat in hand for many turns.

**3. The local tables** (24 games, seeds 20263020 to 20263022, opponents drawn from `bots-v2` under their playbooks)
- **Vanquish:** cast once (7 opposing creatures against 1 of ours). Held once in a game where the seat had the widest board, and that game was won.
- **Meteor:** cast twice. Once it destroyed 7 opposing creatures for 2 of ours and a Treasure; once 13 opposing permanents for Cloud alone.
- **Kujata:** cast 4 times, killing 2 creatures each time.
- **Yuffie:** cast 11 times, taking an Arcane Signet, a Mind Stone, a Talisman and Nevinyrral's Disk, among others.
- **Decimate:** cast 4 times. **Chaos Warp and Cloud's Limit Break:** still cast by Forge as before.
- **Holy (rule 2) never fired:** Forge foretells Holy soon after it is drawn, and a rule cannot cast a foretold card.
- Nothing backfired.
- The seat won 3 of 24. That is too few games to mean anything.

**4. What the rule format cannot express**
- Casting a foretold card from exile. This is why Holy is dead, and why Meteor works only while it is still in hand.
- Stopping Forge from foretelling. A hold blocks spells only, and foretelling is a different kind of action.
- Choosing the modes of a modal spell. Austere Command and Cloud's Limit Break can only be left to Forge.
- Aiming at an opponent's creature when Forge's logic will not. This blocks Dispatch, and Secret Rendezvous as found before.
- Instant-speed responses. Clever Concealment and Holy belong on other players' turns, against a wipe or removal.
- A count of opponents' artifacts, which Vandalblast's overload (destroy each of them) and Yuffie would want. The overload is an alternative cost, which a rule cannot choose.

**5. Recommendation:** send it to 200 tables of its own, with stock, the shipped version and this file as arms. Meteor and Vanquish now go off on the boards the seat lost to, and Yuffie and Kujata come down where Forge left them in hand. The thresholds come from the league logs (creature counts rebuilt from the `zone` events; power and threat estimates are Forge's own) and have not been tuned. My scripts and the local results are in `<scratch>/batch/answers-limit-break/`.
