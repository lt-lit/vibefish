<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Wretched Ranks: answer rules (candidate `answers`, version 2)

**1. The answer cards in the league games** (league-run #3, the seat's 200 games: it won 37, lost 162 and was first out in 68). "Drawn" counts a game if the card was in hand on a turn or cast that game. "Held" means it was in hand on the seat's last turn of a loss. "Idle" counts the seat's own turns where the card was in hand, the seat had at least its mana value in lands, and the card was not cast that turn.

| Card | Kind | Drawn | Cast | Held at loss | Idle turns |
|---|---|---|---|---|---|
| Necrotic Hex | everyone sacrifices 6; we get 6 Zombies | 57 | 12 | 35 | 124 |
| Mutilate | −X/−X to all creatures, ours too | 48 | 7 | 31 | 193 |
| Noxious Ghoul | −1/−1 to every non-Zombie, each time a Zombie enters | 41 | 7 | 29 | 190 |
| Syphon Flesh | each opponent sacrifices one; we get a token each | 44 | 16 | 23 | 134 |
| Fleshbag Marauder | everyone sacrifices one | 51 | 26 | 19 | 174 |
| Go for the Throat / Withering Torment / Consuming Corruption / Tendrils / Consumed by Greed | targeted removal | 37–51 | 33–50 | 1–4 each | – |

Forge already casts the targeted removal in nearly every game it is drawn. The sweepers and edicts are the gap. The seat dies to combat: 7,607 of the 8,030 damage it took in its last four game turns, with a median of 4 attackers at it per attack (9 at the 75th percentile).

**2. Rules added** (they go after the rocks, Gisa and Gisa's activation, so Gisa makes her tokens before a sacrifice effect; and before the lords and creatures):
- Noxious Ghoul when an opponent has 3+ creatures. It is the deck's one-sided sweeper, and it goes first so the Zombies cast after it that turn trigger it again.
- Syphon Flesh when an opponent has 1+ creatures. It only hits opponents.
- Necrotic Hex when an opponent has 3+ creatures. Close to one-sided for a token deck, since we alone get six Zombies back.
- Mutilate only when behind: 5+ lands, an opponent with 3+ creatures, and that opponent's power above our whole board's.
- Fleshbag Marauder when an opponent has 1+ creatures. Forge gives up a token or the Marauder itself.

The twelve shipped rules and the triggers are unchanged and in order. There is no attack block, as shipped. Nothing was tried and dropped.

**3. Local tables** (16 tables of bots, seeds 20263060 and 20263061):
- **Syphon Flesh:** drawn 4, cast 4. 11 opposing creatures sacrificed, 13 tokens made.
- **Fleshbag Marauder:** drawn 4, cast 4.
- **Necrotic Hex:** drawn 2, cast 2. 18 opposing creatures and 7 of ours died; we got 12 tokens.
- **Noxious Ghoul:** drawn 3, cast 3. It killed only 3 opposing creatures in all. Its −1/−1 kills X/1s unless more Zombies follow that turn.
- **Mutilate:** drawn 2, cast 1, at 8 life: 8 of theirs died, 1 of ours. In the other game it stayed in hand for five turns while the seat was ahead, and that game was a win.
- **Targeted removal:** cast 14 times in all, as before.

None of these five cards was in hand at a loss. Every rule fired; nothing backfired. The seat won 3 of 16, which is too few games to mean anything.

**4. What the format cannot express**
- The targeted removal can't be aimed. Forge picks the target: often the widest board, not the leader or the creature about to kill us.
- No instant-speed use. Removal can't be held for an attacker on another player's turn.
- No count of how many opponents have creatures, which is the true value of Syphon Flesh.
- No forecast of Noxious Ghoul's stacked triggers. A later Army of the Damned or Necrotic Hex gives −13/−13 or −6/−6 to our own non-Zombies too: Gisa, Kalitas, Grave Titan, Ayara. Nothing can sequence around that.
- No toughness of opposing creatures, so the rules can't tell whether a −1/−1 kills anything.
- Mutilate's X counts Swamps; `lands` stands in for it.
- No choice of what we sacrifice to Necrotic Hex or Fleshbag Marauder; Forge decides.
- Bojuka Bog's target is Forge's.

**5. The file and the recommendation**
The candidate is `playbook/variants/wretched-ranks-answers.json`. I recommend sending it to 200 tables: stock, shipped and answers, on seed 20263060 or later. My scratch work is in `<scratch>/batch/answers-wretched-ranks/`.
