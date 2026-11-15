# Playtest: mutant-menace

- List: `Mutant Menace [PIP] [2024].dck`
- Pilot: playbook `mutant-menace.json` version 2, Forge's attack (arm `playbook`). Commander: The Wise Mothman
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**40 wins in 200 tables: 20.0%** (95% 15% to 26%); an even share is 25%. 2 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 13 of 50, 12 of 50, 8 of 50, 7 of 50.
Games ran 42.0 turns in all. It won on its own turn 11.1 on average. When it lost it was out by its own turn 10.2.
Of its 158 losses it was the first player out in 51, the second in 50, the last opponent standing in 57. What took it out: LifeReachedZero 157, CommanderDamage 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| deadly-disguise | 65 | 16 (25%) | 5 (8%) | 5 |
| blight-curse | 76 | 17 (22%) | 19 (25%) | 9 |
| squirreled-away | 75 | 16 (21%) | 9 (12%) | 7 |
| veloci-ramp-tor | 62 | 13 (21%) | 22 (36%) | 22 |
| ahoy-mateys | 62 | 12 (19%) | 23 (37%) | 18 |
| blood-rites | 65 | 12 (18%) | 23 (35%) | 20 |
| death-toll | 61 | 11 (18%) | 20 (33%) | 14 |
| miracle-worker | 68 | 12 (18%) | 17 (25%) | 16 |
| revenant-recon | 66 | 11 (17%) | 20 (30%) | 21 |

## Tempo

- A mulligan in 20% of games. Lands at the start of its own turns 4, 6, 8: 3.15, 4.79, 6.16; cards in hand: 5.67, 5.07, 4.52. Short of four lands at the start of turn 5 in 18% of games.
- Commander first cast on its own turn 4.0 (median; quartiles 4 to 5), never cast in 2% of games, 2.43 casts a game.
- 11.8 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 6%.
- Damage dealt 35.0 a game (16.8 of it by the commander), taken 38.0.
- When it lost it held 3.77 nonland cards, 3.39 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 20.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Atomize | 4 | 36 | 0% |  | 19% | 20% | -1 | 23 |
| Biomass Mutation | 2 | 44 | 11% | 11 | 18% | 20% | -2 | 33 |
| Mutational Advantage | 3 | 40 | 12% | 10 | 22% | 19% | +3 | 26 |
| Harmonize | 4 | 43 | 35% | 11 | 26% | 18% | +7 | 19 |
| Struggle for Project Purity | 4 | 32 | 38% | 6.5 | 22% | 20% | +2 | 17 |
| Agent Frank Horrigan | 7 | 42 | 45% | 10 | 19% | 20% | -1 | 19 |
| Vault 12: The Necropolis | 6 | 52 | 48% | 9 | 27% | 18% | +9 | 17 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Talisman of Resilience | 2 | 43 | 100% | 4 | 37% | 15% | +22 | 1 |
| Arcane Signet | 2 | 40 | 98% | 6 | 35% | 16% | +19 | 1 |
| Winding Constrictor | 2 | 46 | 94% | 7 | 35% | 16% | +19 | 3 |
| Rampaging Yao Guai | 3 | 41 | 54% | 9.0 | 32% | 17% | +15 | 14 |
| Watchful Radstag | 3 | 35 | 63% | 7.0 | 31% | 18% | +14 | 7 |
| Strong, the Brutish Thespian | 6 | 32 | 56% | 10.0 | 31% | 18% | +13 | 13 |
| Piper Wright, Publick Reporter | 2 | 42 | 76% | 5.5 | 31% | 17% | +14 | 4 |
| Branching Evolution | 3 | 47 | 94% | 6.0 | 28% | 18% | +10 | 3 |
| Bloatfly Swarm | 4 | 40 | 80% | 7.0 | 28% | 18% | +9 | 7 |
| Inspiring Call | 3 | 51 | 88% | 7 | 28% | 17% | +10 | 6 |
| Feral Ghoul | 3 | 55 | 82% | 7 | 27% | 17% | +10 | 11 |
| Infesting Radroach | 3 | 55 | 66% | 7.0 | 27% | 17% | +10 | 25 |
| Lumbering Megasloth | 12 | 37 | 68% | 8 | 27% | 18% | +9 | 9 |
| Glowing One | 3 | 52 | 71% | 7 | 27% | 18% | +9 | 12 |
| Vault 12: The Necropolis | 6 | 52 | 48% | 9 | 27% | 18% | +9 | 17 |
| Alpha Deathclaw | 6 | 41 | 76% | 9 | 27% | 18% | +9 | 9 |
| Farseek | 2 | 42 | 100% | 6.0 | 26% | 18% | +8 | 1 |
| Harmonize | 4 | 43 | 35% | 11 | 26% | 18% | +7 | 19 |
| Cathedral Acolyte | 2 | 47 | 81% | 6.5 | 26% | 18% | +7 | 11 |
| Casualties of War | 6 | 44 | 61% | 7 | 25% | 19% | +6 | 15 |
| Contagion Clasp | 2 | 28 | 68% | 7 | 25% | 19% | +6 | 9 |
| Lily Bowen, Raging Grandma | 4 | 44 | 59% | 8.0 | 25% | 19% | +6 | 12 |
| Sol Ring | 1 | 52 | 100% | 3.5 | 25% | 18% | +7 | 0 |
| Talisman of Curiosity | 2 | 52 | 98% | 3 | 25% | 18% | +7 | 0 |
| Nightkin Ambusher | 4 | 45 | 84% | 7.5 | 24% | 19% | +6 | 8 |
| Nuka-Nuke Launcher | 2 | 41 | 80% | 5 | 24% | 19% | +5 | 4 |
| Tato Farmer | 3 | 37 | 60% | 8.0 | 24% | 19% | +5 | 9 |
| Radstorm | 4 | 34 | 56% | 9 | 24% | 19% | +4 | 15 |
| Marcus, Mutant Mayor | 5 | 35 | 86% | 8.0 | 23% | 19% | +4 | 3 |
| Fraying Sanity | 3 | 40 | 57% | 7 | 22% | 19% | +3 | 14 |
| Mutational Advantage | 3 | 40 | 12% | 10 | 22% | 19% | +3 | 26 |
| Putrefy | 3 | 40 | 90% | 5.0 | 22% | 19% | +3 | 2 |
| Mirelurk Queen | 5 | 49 | 67% | 8 | 22% | 19% | +3 | 14 |
| The Master, Transcendent | 4 | 50 | 74% | 8 | 22% | 19% | +3 | 19 |
| Struggle for Project Purity | 4 | 32 | 38% | 6.5 | 22% | 20% | +2 | 17 |
| Tireless Tracker | 3 | 51 | 69% | 6 | 22% | 20% | +2 | 15 |
| Rampant Growth | 2 | 33 | 100% | 5 | 21% | 20% | +1 | 1 |
| Corpsejack Menace | 4 | 45 | 84% | 7.0 | 20% | 20% | +0 | 6 |
| Young Deathclaws | 4 | 35 | 71% | 9 | 20% | 20% | +0 | 6 |
| Vault 87: Forced Evolution | 5 | 46 | 76% | 8 | 20% | 20% | -1 | 6 |
| Cultivate | 3 | 41 | 100% | 5 | 20% | 20% | -1 | 0 |
| Atomize | 4 | 36 | 0% |  | 19% | 20% | -1 | 23 |
| Hardened Scales | 1 | 36 | 97% | 6 | 19% | 20% | -1 | 2 |
| Agent Frank Horrigan | 7 | 42 | 45% | 10 | 19% | 20% | -1 | 19 |
| Biomass Mutation | 2 | 44 | 11% | 11 | 18% | 20% | -2 | 33 |
| Power Fist | 2 | 39 | 56% | 7.0 | 18% | 20% | -3 | 11 |
| Contaminated Drink | 2 | 45 | 58% | 8.0 | 18% | 21% | -3 | 17 |
| Harold and Bob, First Numens | 3 | 45 | 76% | 8.0 | 18% | 21% | -3 | 9 |
| Inexorable Tide | 5 | 51 | 84% | 8 | 18% | 21% | -3 | 7 |
| Talisman of Dominance | 2 | 40 | 98% | 4 | 18% | 21% | -3 | 1 |
| Guardian Project | 4 | 44 | 84% | 7 | 16% | 21% | -5 | 5 |
| Raul, Trouble Shooter | 3 | 44 | 89% | 6 | 16% | 21% | -5 | 6 |
| Nuclear Fallout | 2 | 38 | 79% | 8.0 | 16% | 21% | -5 | 7 |
| Vexing Radgull | 2 | 46 | 87% | 5.5 | 15% | 21% | -6 | 7 |
| Hancock, Ghoulish Mayor | 3 | 48 | 85% | 6 | 15% | 22% | -7 | 4 |
| Recon Craft Theta | 4 | 43 | 60% | 8.0 | 14% | 22% | -8 | 15 |
| Strength Bobblehead | 3 | 38 | 60% | 7 | 13% | 22% | -8 | 14 |
| Jason Bright, Glowing Prophet | 3 | 46 | 70% | 7.0 | 13% | 22% | -9 | 10 |
| Screeching Scorchbeast | 6 | 39 | 59% | 8 | 10% | 22% | -12 | 20 |
| Find // Finality | 8 | 41 | 54% | 8.5 | 10% | 23% | -13 | 12 |
