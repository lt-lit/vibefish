# Playtest: death-toll

- List: `Death Toll [DSC] [2024].dck`
- Pilot: playbook `death-toll.json` version 3, Forge's attack (arm `playbook`). Commander: Winter, Cynical Opportunist
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**56 wins in 200 tables: 28.0%** (95% 22% to 35%); an even share is 25%. 2 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 13 of 50, 11 of 50, 19 of 50, 13 of 50.
Games ran 46.4 turns in all. It won on its own turn 12.6 on average. When it lost it was out by its own turn 11.5.
Of its 142 losses it was the first player out in 41, the second in 44, the last opponent standing in 57. What took it out: LifeReachedZero 128, Milled 13, CommanderDamage 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| squirreled-away | 75 | 28 (37%) | 9 (12%) | 7 |
| ahoy-mateys | 62 | 21 (34%) | 17 (27%) | 17 |
| deadly-disguise | 65 | 20 (31%) | 5 (8%) | 4 |
| mutant-menace | 68 | 20 (29%) | 12 (18%) | 14 |
| blight-curse | 76 | 22 (29%) | 16 (21%) | 10 |
| revenant-recon | 66 | 17 (26%) | 18 (27%) | 14 |
| veloci-ramp-tor | 62 | 15 (24%) | 23 (37%) | 18 |
| miracle-worker | 61 | 14 (23%) | 19 (31%) | 11 |
| blood-rites | 65 | 11 (17%) | 23 (35%) | 18 |

## Tempo

- A mulligan in 23% of games. Lands at the start of its own turns 4, 6, 8: 3.08, 4.94, 6.66; cards in hand: 5.62, 4.73, 3.68. Short of four lands at the start of turn 5 in 20% of games.
- Commander first cast on its own turn 4 (median; quartiles 4 to 5), never cast in 2% of games, 2.21 casts a game.
- 14.7 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 5%.
- Damage dealt 35.0 a game (5.8 of it by the commander), taken 39.0.
- When it lost it held 2.32 nonland cards, 2.05 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (61 cards); the deck won 28.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Arachnogenesis | 3 | 47 | 38% | 11.5 | 38% | 25% | +14 | 16 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Grapple with the Past | 2 | 42 | 93% | 8 | 45% | 23% | +22 | 3 |
| Inscription of Abundance | 2 | 29 | 97% | 7.5 | 45% | 25% | +20 | 0 |
| Polluted Cistern // Dim Oubliette | 7 | 51 | 94% | 5.5 | 43% | 23% | +20 | 2 |
| Demolisher Spawn | 7 | 45 | 76% | 8.5 | 42% | 24% | +18 | 3 |
| Professor Onyx | 6 | 40 | 82% | 9 | 40% | 25% | +15 | 3 |
| Mind Stone | 2 | 41 | 98% | 3.0 | 39% | 25% | +14 | 1 |
| Arachnogenesis | 3 | 47 | 38% | 11.5 | 38% | 25% | +14 | 16 |
| Wrenn and Seven | 5 | 48 | 77% | 10 | 38% | 25% | +12 | 9 |
| Grim Flayer | 2 | 46 | 87% | 7.0 | 37% | 25% | +12 | 4 |
| Deathreap Ritual | 4 | 33 | 85% | 8.5 | 36% | 26% | +10 | 3 |
| Hornet Queen | 7 | 51 | 80% | 9 | 35% | 26% | +10 | 4 |
| Grist, the Hunger Tide | 3 | 40 | 98% | 6 | 35% | 26% | +9 | 1 |
| Obsessive Skinner | 2 | 43 | 91% | 7 | 35% | 26% | +9 | 2 |
| Cemetery Tampering | 3 | 46 | 98% | 6 | 35% | 26% | +9 | 3 |
| Sol Ring | 1 | 50 | 98% | 6 | 34% | 26% | +8 | 1 |
| Stitcher's Supplier | 1 | 39 | 92% | 5.5 | 33% | 27% | +7 | 2 |
| Moldgraf Millipede | 5 | 52 | 52% | 10 | 33% | 26% | +6 | 15 |
| Deathcap Cultivator | 2 | 50 | 100% | 4.5 | 32% | 27% | +5 | 1 |
| Noxious Gearhulk | 6 | 50 | 88% | 8.0 | 32% | 27% | +5 | 5 |
| Crawling Sensation | 3 | 47 | 81% | 6.0 | 32% | 27% | +5 | 6 |
| Haywire Mite | 1 | 47 | 87% | 4 | 32% | 27% | +5 | 3 |
| Nyx Weaver | 3 | 52 | 88% | 6.0 | 31% | 27% | +4 | 2 |
| Reanimate | 1 | 52 | 100% | 7.5 | 31% | 27% | +4 | 5 |
| Carrion Grub | 4 | 49 | 69% | 8.0 | 31% | 27% | +3 | 11 |
| Sakura-Tribe Elder | 2 | 53 | 91% | 7.0 | 30% | 27% | +3 | 4 |
| Arcane Signet | 2 | 50 | 100% | 7.0 | 30% | 27% | +3 | 1 |
| Ursine Monstrosity | 3 | 47 | 66% | 8 | 30% | 28% | +2 | 13 |
| Burnished Hart | 3 | 34 | 82% | 7.0 | 29% | 28% | +2 | 6 |
| Skola Grovedancer | 2 | 41 | 83% | 6.5 | 29% | 28% | +2 | 5 |
| Harrow | 3 | 48 | 96% | 5.5 | 29% | 28% | +2 | 1 |
| Ishkanah, Grafwidow | 5 | 55 | 82% | 9 | 29% | 28% | +1 | 6 |
| Deluge of Doom | 3 | 31 | 81% | 11 | 29% | 28% | +1 | 10 |
| Moldgraf Monstrosity | 7 | 59 | 66% | 9 | 29% | 28% | +1 | 15 |
| Talisman of Resilience | 2 | 66 | 98% | 4 | 29% | 28% | +1 | 0 |
| Demonic Covenant | 6 | 42 | 67% | 8.0 | 29% | 28% | +1 | 7 |
| Whip of Erebos | 4 | 42 | 86% | 7.0 | 29% | 28% | +1 | 4 |
| Golgari Signet | 2 | 46 | 98% | 4 | 28% | 28% | +0 | 0 |
| Whispersilk Cloak | 3 | 39 | 69% | 8 | 28% | 28% | +0 | 7 |
| Rendmaw, Creaking Nest | 5 | 51 | 72% | 9 | 28% | 28% | -1 | 13 |
| Convert to Slime | 5 | 55 | 82% | 8 | 27% | 28% | -1 | 8 |
| Titania, Nature's Force | 6 | 52 | 86% | 8 | 27% | 28% | -1 | 6 |
| Commander's Sphere | 3 | 41 | 100% | 5 | 27% | 28% | -1 | 1 |
| Mulch | 2 | 41 | 95% | 7 | 27% | 28% | -1 | 2 |
| Grisly Salvage | 2 | 50 | 94% | 7 | 26% | 29% | -3 | 2 |
| Old Stickfingers | 2 | 58 | 78% | 8 | 26% | 29% | -3 | 7 |
| Formless Genesis | 3 | 43 | 67% | 9 | 26% | 29% | -3 | 11 |
| Into the Pit | 3 | 51 | 96% | 7 | 26% | 29% | -3 | 1 |
| Vile Mutilator | 7 | 44 | 64% | 9.0 | 25% | 29% | -4 | 11 |
| Giant Adephage | 7 | 49 | 69% | 9.5 | 24% | 29% | -5 | 14 |
| Suspicious Bookcase | 2 | 53 | 83% | 7.0 | 24% | 29% | -5 | 9 |
| Putrefy | 3 | 41 | 98% | 5.0 | 24% | 29% | -4 | 1 |
| Rampant Growth | 2 | 41 | 98% | 4.0 | 24% | 29% | -4 | 0 |
| Harmonize | 4 | 42 | 71% | 9.0 | 24% | 29% | -5 | 10 |
| Culling Ritual | 4 | 55 | 86% | 9 | 24% | 30% | -6 | 8 |
| Night's Whisper | 2 | 48 | 96% | 8.5 | 23% | 30% | -7 | 5 |
| Deadbridge Chant | 6 | 36 | 58% | 8 | 22% | 29% | -7 | 11 |
| Ob Nixilis Reignited | 5 | 46 | 91% | 8.0 | 22% | 30% | -8 | 1 |
| Solemn Simulacrum | 4 | 49 | 59% | 9 | 20% | 30% | -10 | 14 |
| Binding the Old Gods | 4 | 40 | 95% | 7.0 | 18% | 31% | -13 | 1 |
| Gnarlwood Dryad | 1 | 53 | 92% | 6 | 17% | 32% | -15 | 3 |
| Scavenging Ooze | 2 | 53 | 83% | 7.5 | 15% | 33% | -18 | 7 |
