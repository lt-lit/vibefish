<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

## Revenant Recon (Mirko, Obsessive Theorist): candidate report

**Summary:** stock Forge AI already plays this deck fairly well. The candidate is 0.90 turns faster in goldfish on unseen seeds (95% +0.54 to +1.26). The gain comes from three things: Mirko cast at once, the surveil engine cards used, and Copy Catchers' and Mirko's "you may" triggers taken.

**1. Audit (12 stock goldfish games, seeds 25002–25013)**
- **Kill turn:** 12.75 (median 12.5, range 10–16).
- **Mana:** 52% unspent (3.2 of 6.1 lands a turn). 56% of turns ended holding a card the spare mana could pay for, and 21% of turns cast nothing.
- **Held most:** mostly answers with nothing to answer: Black Sun's Zenith 17/23, Toxic Deluge 16/25, Price of Fame 11/18, Counterpoint 9/17. Also the reanimation spells (Animate Dead 8/10, Necromancy 8/20) and cheap creatures (Dimir Spybug 7/14, Final-Word Phantom 7/12, Sinister Starfish 7/11, Syr Konrad 7/13), plus Dream Eater 7/14.
- **Mirko:** cast on own turn 6–7 in four games and never in one.
- **Abilities never or rarely used:** Sinister Starfish's surveil on 1 of its 15 turns. Never: Port of Karfell (8 turns), Lazav (9), Enhanced Surveillance (26), Rogue's Passage (21).
- **Optional triggers Forge declined** (from the playbook trace): Copy Catchers' paid copy (395 declines), Overseer of the Damned (2), Foreboding Steamboat (2).
- **Flagged never-cast:** Black Sun's Zenith, Toxic Deluge, Mission Briefing.

**2. Candidate:** `playbook/variants/revenant-recon-mirko.json` (version 3). Attack is the brief's default go-wide (min 3, reserve 3, spread).
1. Mana rocks first.
2. Mirko at once: his end-step reanimation needs him out and growing.
3. Surveil engine early: Whispering Snitch, Sinister Starfish, Case of the Shifting Visage, Dimir Spybug, Enhanced Surveillance.
4. Phyrexian Arena while library ≥ 30.
5. Tap Sinister Starfish every turn (it grows Mirko and fills the graveyard).
6. Mission Briefing (never cast by Forge).
7. Rise of the Dark Realms whenever affordable.
8. Creatures, most expensive first.
9. Disinformation Campaign after the creatures.
10. Cheap card draw while library ≥ 25.
11. Doom Whisperer's surveil while life ≥ 20.
12. Tocasia's Dig Site in main 2.
13. Port of Karfell in main 2 with 8 lands.

Triggers: always accept Mirko's return; Master of Death at life ≥ 10; Marvo's free cast; Copy Catchers' {1}{U} copy when mana ≥ 4 and library ≥ 25.

- Tuning: version 1 was +1.67 turns on the audit seeds (95% +1.06 to +2.27; 10 faster, 2 same).
- Dropped: Disinformation Campaign inside the engine rule (version 2). It recast on every surveil, 42 times in 12 games, and made two games a turn slower.

**3. Validation (seeds 25102–25141, 40 games each arm)**

| | Wins | Kill turn mean (median) | Mana unspent |
|---|---|---|---|
| Stock | 39/40 | 13.08 (13) | 42% |
| Playbook | 39/40 | 12.18 (12) | 38% |

- **Paired difference** over 39 seeds: +0.90 turns (95% +0.54 to +1.26). Faster in 27, same in 8, slower in 4.
- **Unfinished game:** seed 25122 hit the turn cap in both arms.
- The rules were not changed after the validation games were seen. The playbook arm ran on the variant file itself.

**4. Rules that fired (`playbook_stats`, 40 validation games)**
- Cast rules: 1: 90, 2: 54, 3: 51, 4: 6, 5: 49, 6: 14, 7: 8, 8: 148, 9: 42, 10: 34, 11: 34, 12: 34, 13: 3.
- Triggers: Mirko 46, Master of Death 2, Copy Catchers 47. Marvo's trigger rule never fired. Every cast rule fired at least once.

**5. What the rule format cannot express**
- Surveil choices: what goes to the graveyard decides what Mirko and the reanimation spells can bring back, and Forge picks it.
- Which creature Mirko returns; reanimation targets; any condition on creature cards in the graveyard.
- Lazav's X copy.
- Everflowing Chalice's multikicker.
- Instant-speed play: Starfish at an opponent's end step, Final-Word Phantom's flash window, Counterpoint, Dream Eater's flash.
- A cap on chains of Copy Catchers copies beyond the mana condition.
- The choices Foreboding Steamboat asks for.

**6. Recommendation:** send it to 200 tables, played with both attacks. The goldfish gain is real but modest, and stock already runs the engine passably. The deck's table strength is its answers, which this pass leaves to Forge, so expect a small lead or none until the second pass.

**7. The deck's answers, for the second pass (no rules written)**
- Black Sun's Zenith: X −1/−1 counters on every creature. **Never cast by Forge.**
- Toxic Deluge: all creatures −X/−X. **Never cast by Forge.**
- Massacre Wurm: opponents' creatures −2/−2, and each one that dies costs its controller 2 life.
- Price of Fame: destroy a creature (cheaper on a legendary one), surveil 2.
- Pile On: destroy a creature or planeswalker (convoke), surveil 2.
- Ravenous Chupacabra: destroy an opponent's creature.
- Shriekmaw: destroy a nonartifact, nonblack creature (can be evoked).
- Overseer of the Damned: may destroy a creature when it enters.
- Amphin Mutineer: exile a creature; its controller gets a 4/3.
- Connive // Concoct: Connive steals a creature with power 2 or less.
- Discovery // Dispersal: Dispersal makes each opponent bounce their highest-value nonland permanent and discard a card.
- Ephara's Dispersal: bounce a creature, surveil 2.
- Dream Eater: bounce an opponent's nonland permanent.
- Counterpoint: counter a spell.
- Foreboding Steamboat: each player exiles two of their own creatures, the seat included.
- Bojuka Bog: exiles a graveyard.
- Fogs: none.

**8. How an owner expects it to play:** Mirko comes down on turn 3. Surveil every turn to grow him and stock the graveyard, then bring a bigger creature back each end step while Whispering Snitch and Syr Konrad drain the table. Removal, the two wipes and Counterpoint are held for real threats and used at instant speed, often on opponents' turns.

The candidate gets Mirko out and runs the surveil and copy engines. It cannot choose what to surveil away or what Mirko and the reanimation spells return, and it never acts on another player's turn. It still leaves every answer to Forge, which casts neither wipe at all.

Files are in <scratch>/batch/revenant-recon:
- revenant-recon-pair.json
- results/
