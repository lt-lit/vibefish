<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Quick Draw: answer rules (candidate `answers`, version 2)

**1. Answer cards in the league games** (`league-run` #3: 200 games of the seat, 57 won)

| Card | Seen | Cast in | In hand at a loss | Notes |
|---|---|---|---|---|
| Volcanic Torrent (one-sided damage wipe, X = spells cast this turn) | 80 | 37 | 25 | the losses were held with this |
| Curse of the Swine (`AI:RemoveDeck:All`) | 82 | 0 | 36 | Forge never casts it |
| Baral's Expertise | 85 | 59 | 16 | |
| Propaganda | 88 | 77 | 1 | sat in hand a median of 2 own turns first |
| Pongify / Chaos Warp | 89 / 83 | 82 / 77 | 5 / 5 | Forge already plays them |
| Vandalblast | 80 | 73 | 10 | |
| Arcane Denial | 74 | 46 | 11 | counterspell |

**2. Rules added.** The 7 shipped rules are unchanged and in their order (now rules 6–12). There are no triggers and no attack block, as shipped.
- R1: Torrent when an opponent has 4+ creatures and 2+ spells have gone this turn. Cascade adds a spell, so X is at least 4.
- R2: Torrent at once when an opponent has 8+ creatures. Against the pool's token boards even X=2 clears them.
- R13 (last): Torrent when an opponent has 4+ creatures, using the mana the engine rules leave.
- R3: Curse of the Swine when `threat >= 12` and `opp_creatures <= 6`. Forge picks X and the targets.
- R4: Baral's Expertise when `threat >= life`, as an emergency.
- R5: Propaganda when an opponent has 3+ creatures, moved ahead of the engine.
- Tried and narrowed: R3 was first just `threat >= 12`. Against 17 creatures Forge chose X=18: 1/1 tokens (which would become 2/2 Boars) plus Kappa Cannoneer. The Cannoneer's ward then countered the whole spell. The cap of six creatures keeps Curse for boards of a few large creatures.

**3. Local tables.** 16 tables of bots, seeds 20263050 and 20263051. The first 8 used the earlier R3; the second 8 are exactly the candidate file.
- **Volcanic Torrent:** seen in 4 games, cast from hand 5 times. It killed 10 tokens; a planeswalker and 3 Boars; 12 creatures (storm 16); Cid and 8 Soldiers. Nothing backfired.
  - In the storm-16 game the seat was decked (milled out) the same turn. That came from its own draw engine, not the Torrent.
- **Curse of the Swine:** seen in 6 games, cast in 2 (it had never been cast before). One cast was countered by ward (old R3). The other exiled 3 creatures. It sat in hand for 6 turns in one game because the conditions did not hold.
- **Propaganda:** cast 7 times, usually the turn an opponent reached 3 creatures.
- **Baral's Expertise:** cast 5 times. I can't tell R4's casts apart from Forge's own, because `playbook_stats` collide across playbook seats.
- **Pongify, Chaos Warp, Vandalblast:** cast by Forge as before.
- **Wins:** 5 of 16 (3 + 2). That is too few games to mean anything.

**4. What the rule format can't express**
- Arcane Denial: a counterspell needs a spell on the stack, usually on another player's turn.
- Pongify and Chaos Warp: no instant-speed casting, and no way to aim at a chosen opposing permanent. They stay Forge's, which already casts them in about 9 games of 10.
- Vandalblast's overload: `play` rules skip alternative costs, so only the single-target mode is cast.
- Curse of the Swine: no control over its X or targets. That means no "exclude tokens" and no "avoid ward".
- Volcanic Torrent: no way to wait for the end of a spell chain other than `storm >= N`. There's also no "board after the wipe" or "lowest opponent life" condition.

**5. File:** `playbook/variants/quick-draw-answers.json` (`"variant": "answers"`, version 2; the notes list each rule's source). I recommend sending it to 200 tables. The rules fire when intended, and the deck's two biggest held-at-loss answers (Torrent and Curse) now get cast. R3's guard is the softest part: it rests on 2 local casts.

Scratch work (scripts, league summary, results) is in `<scratch>/batch/answers-quick-draw`.
