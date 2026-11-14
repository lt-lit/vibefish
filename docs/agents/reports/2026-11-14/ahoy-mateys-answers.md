<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Ahoy Mateys: answer rules (`answers`, version 2)

**File:** `playbook/variants/ahoy-mateys-answers.json`. It has `"of": "playbook/variants/ahoy-mateys-crew.json"` and the go-wide attack and triggers of `crew` unchanged. I checked it against the playbook recorded in all 16 local games: the cast rules, triggers and version are identical. **I recommend sending it to 200 tables**, with `crew` played on the same tables as the control.

### 1. Answer cards in the exam (`crew` arm, 200 tables)
Counts are games drawn / games cast / games where it was in hand at a loss. The stock pilot is in brackets as cast/drawn.

| Card | `crew` arm | Stock |
|---|---|---|
| Blasphemous Act | 44 / 11 / 16 | 25/38 |
| Blood Money | 48 / 3 / 23 | 27/42 |
| Evacuation | 44 / 34 / 3 | 34 cast. In both arms it was always cast in our own main phase, mostly at 30 to 40 life against 2 to 5 creatures, and the seat won only 2 of the 34 games where it was cast. |
| Chaos Warp, Lethal Scheme, Prismari Command | cast in about 90% of games drawn | the same |
| Feed the Swarm | 51 / 28 / 19 | 30/35 |
| Hostage Taker | 49 / 18 / 22 | 45/49 |
| Amphin Mutineer | 46 / 11 / 21 | 27/42 |
| Rakdos Charm | 46 / 0 / 30 | never cast (Forge's AI never casts it) |
| Siren Stormtamer | 57 / 52 / 3 | similar |

### 2. Rules added and changed (22 rules now; base rules keep their relative order)
- **Rules 1–2:** Blood Money, then Blasphemous Act, in two cases:
  - an opponent could kill us next turn and has more power than our whole board;
  - an opponent has 5 or more creatures and 10 or more power, and more power than us.
  
  The deck rebuilds after a wipe: Brass is recast from the command zone and returns a Pirate each combat, and Blood Money pays Treasures.
- **Rules 3–4:** Evacuation is held until an opponent could kill us next turn. Then it is cast after combat (main2) if that opponent also has more power than us. This stops Forge from bouncing our own board at 40 life.
- **Rule 9:** Hostage Taker and Feed the Swarm when an opponent has a creature. Forge aims Feed the Swarm, so it is cast only when Forge's own logic agrees.
- **Rule 10:** Coercive Recruiter when an opponent has a creature.
- **Rule 12:** Dire Fleet Ravager while our board's power is at least that of the strongest opponent.
- **Rule 16:** activate Captivating Crew's steal in main1 when an opponent has a creature.
- **Rule 22:** Rakdos Charm in main2. Forge chooses the mode and target.

**Base rules moved or changed:**
- Base rule 4 is split, with no change to its order:
  - its first 7 cards (the lords and engines) are now rule 8;
  - Angrath's Marauders through Breeches are now rule 11;
  - the rest is now rule 14.
- In rule 14:
  - Merchant Raiders and Amphin Mutineer are added at the head;
  - The Grim Captain's Locker moves up to just behind The Indomitable;
  - Captivating Crew moves up to just behind Azure Fleet Admiral;
  - Dire Fleet Daredevil is added among the two-drops.
- Base rule 7 (Distant Melody) is moved up to rule 13, before the creature list, and its threshold drops from 4 Pirates to 3.
- Nothing was tried and dropped.

### 3. Local tables (16 games: seeds 20263140 and 20263141, 8 each)
Counts are games drawn / games cast.
- **Wipes and Evacuation:**
  - Blood Money 5/2. One cast hit 2 of our creatures against 7 of the opponent's.
  - Blasphemous Act 1/1, cast at 5 life.
  - Evacuation 3/2: once at 6 life, once against a 24-creature Goblin board.
  - The trace was on only in the second run, so I can't say whether those casts came from my rules or from Forge's fallback.
- **Stealing and removal:**
  - Hostage Taker 6/6; it took Vincent and Emmara.
  - Coercive Recruiter 3/4; its triggers stole Caesar and Emmara.
  - Captivating Crew's steal fired.
- **Charm and instants:** Rakdos Charm 4/2, rule 22 confirmed by the trace; it used the graveyard mode. Feed the Swarm 2/2, Prismari Command 4/4, Lethal Scheme 3/3, Chaos Warp 3/2.
- **Nothing backfired visibly.** Win count: 4 of 16, too few games to mean anything.

### 4. What the format can't express
- Evacuation as a fog during an opponent's attack. Rules only act in our own main phase; the hold only lets Forge decide.
- Choosing targets for Feed the Swarm, Chaos Warp and Lethal Scheme, and for the triggers of Hostage Taker, Amphin Mutineer, Merchant Raiders and Coercive Recruiter. Forge picks them; Merchant Raiders once tapped a Clue.
- Rakdos Charm's mode.
- "Lowest opponent life" or "we are the one ahead", which Ravager's rule really wants.
- Which Pirate Brass returns: Forge returned Dire Fleet Ravager at 5 life in one game.

### Cards cast less under `crew`
Shown as `crew` cast/drawn → local cast/drawn under `answers`.
- **Dire Fleet Ravager** (12/54 → 5/7): rule 12, conditioned on board power. It was in hand at 4 local losses, which is by design when behind.
- **Blood Money** (3/48 → 2/5) and **Blasphemous Act** (11/44 → 1/1): rules 1–2.
- **Hostage Taker** (18/49 → 6/6): rule 9.
- **Merchant Raiders** (17/38 → 1/1): head of rule 14.
- **Coercive Recruiter** (12/47 → 3/4): rule 10.
- **Distant Melody** (24/50 → 1/3): moved to rule 13 with the threshold lowered to 3 Pirates.
- **Amphin Mutineer** (11/46 → 1/1): head of rule 14. Its exile is "up to one", so Forge can choose no target.
- **Dire Fleet Daredevil** (21/38 → not drawn locally): added among the two-drops in rule 14.
- **Captivating Crew** (28/47 → 3/3): moved up in rule 14, plus the activate rule 16.
- **Feed the Swarm** (28/51 → 2/2): rule 9.
- **Angrath's Marauders** (26/48 → 1/2): left as it was. It is already eighth in the list; at 7 mana the cost is what limits it.
- **The Grim Captain's Locker** (18/41 → 2/3): moved up behind The Indomitable.
- **Zara, Renegade Recruiter** (39/54 → 1/4, in hand at 2 losses): not changed, but it now sits behind more cards. Watch it in the 200 tables.

My scratch work (scan scripts, local runs, playtest reports) is in `<scratch>/batch/answers-ahoy-mateys/`.
