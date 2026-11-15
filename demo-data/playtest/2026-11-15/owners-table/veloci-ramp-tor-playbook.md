# Playtest: veloci-ramp-tor

- List: `Veloci-Ramp-Tor [LCC] [2023].dck`
- Pilot: playbook `veloci-ramp-tor.json` version 2, Forge's attack (arm `playbook`). Commander: Pantlaza, Sun-Favored
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**68 wins in 200 tables: 34.0%** (95% 28% to 41%); an even share is 25%. 5 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 18 of 50, 16 of 50, 15 of 50, 19 of 50.
Games ran 46.2 turns in all. It won on its own turn 13.0 on average. When it lost it was out by its own turn 11.0.
Of its 127 losses it was the first player out in 33, the second in 54, the last opponent standing in 40. What took it out: LifeReachedZero 124, CommanderDamage 4, Milled 1, IntentionalDraw 1.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| squirreled-away | 62 | 26 (42%) | 13 (21%) | 5 |
| deadly-disguise | 65 | 27 (42%) | 5 (8%) | 7 |
| revenant-recon | 75 | 29 (39%) | 15 (20%) | 15 |
| blight-curse | 76 | 27 (36%) | 5 (7%) | 4 |
| miracle-worker | 68 | 22 (32%) | 18 (26%) | 16 |
| mutant-menace | 66 | 21 (32%) | 15 (23%) | 17 |
| ahoy-mateys | 62 | 19 (31%) | 14 (23%) | 16 |
| death-toll | 61 | 17 (28%) | 21 (34%) | 15 |
| blood-rites | 65 | 16 (25%) | 21 (32%) | 19 |

## Tempo

- A mulligan in 26% of games. Lands at the start of its own turns 4, 6, 8: 3.35, 5.49, 7.39; cards in hand: 5.72, 5.35, 4.88. Short of four lands at the start of turn 5 in 14% of games.
- Commander first cast on its own turn 5.0 (median; quartiles 4 to 6), never cast in 1% of games, 2.24 casts a game.
- 20.3 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 5%.
- Damage dealt 56.6 a game (11.5 of it by the commander), taken 35.3.
- When it lost it held 4.02 nonland cards, 3.75 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 34.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Marauding Raptor | 2 | 58 | 0% |  | 33% | 34% | -2 | 29 |
| Fiery Confluence | 4 | 73 | 44% | 9.5 | 45% | 28% | +18 | 22 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Zacama, Primal Calamity | 9 | 37 | 76% | 11.0 | 57% | 29% | +28 | 4 |
| Wakening Sun's Avatar | 8 | 52 | 83% | 10 | 56% | 26% | +29 | 7 |
| Savage Stomp | 3 | 57 | 77% | 8.0 | 53% | 27% | +26 | 7 |
| Scion of Calamity | 5 | 57 | 86% | 10 | 51% | 27% | +24 | 7 |
| Apex Altisaur | 9 | 61 | 56% | 10.5 | 51% | 27% | +24 | 13 |
| Xenagos, God of Revels | 5 | 45 | 78% | 8 | 49% | 30% | +19 | 4 |
| Quartzwood Crasher | 5 | 66 | 74% | 10 | 48% | 27% | +22 | 9 |
| Cultivate | 3 | 54 | 100% | 8.0 | 48% | 29% | +19 | 2 |
| Sol Ring | 1 | 81 | 100% | 7 | 47% | 25% | +22 | 2 |
| Regal Behemoth | 6 | 58 | 69% | 10.0 | 47% | 29% | +18 | 13 |
| Wrathful Raptors | 5 | 58 | 71% | 9 | 47% | 29% | +18 | 8 |
| Migration Path | 4 | 43 | 93% | 6.5 | 46% | 31% | +16 | 0 |
| Curious Altisaur | 4 | 61 | 66% | 10.0 | 46% | 29% | +17 | 18 |
| Path to Exile | 1 | 48 | 100% | 7.0 | 46% | 30% | +16 | 0 |
| Farseek | 2 | 46 | 100% | 7.0 | 46% | 30% | +15 | 1 |
| Kinjalli's Sunwing | 3 | 68 | 84% | 8 | 46% | 28% | +18 | 7 |
| Thunderherd Migration | 2 | 55 | 98% | 7.5 | 46% | 30% | +16 | 1 |
| Akroma's Will | 4 | 86 | 93% | 9.0 | 45% | 25% | +20 | 7 |
| Fiery Confluence | 4 | 73 | 44% | 9.5 | 45% | 28% | +18 | 22 |
| Atzocan Seer | 3 | 71 | 63% | 8 | 45% | 28% | +17 | 14 |
| Wayward Swordtooth | 3 | 60 | 75% | 9 | 45% | 29% | +16 | 9 |
| Bellowing Aegisaur | 6 | 45 | 71% | 10.0 | 44% | 31% | +13 | 13 |
| Zetalpa, Primal Dawn | 8 | 59 | 73% | 9 | 44% | 30% | +14 | 15 |
| Rampant Growth | 2 | 55 | 100% | 6 | 44% | 30% | +13 | 1 |
| Rishkar's Expertise | 6 | 58 | 84% | 9 | 43% | 30% | +13 | 6 |
| Earthshaker Dreadmaw | 6 | 49 | 80% | 9 | 43% | 31% | +12 | 6 |
| Topiary Stomper | 3 | 66 | 67% | 9.0 | 42% | 30% | +12 | 16 |
| Etali, Primal Storm | 6 | 45 | 73% | 9 | 42% | 32% | +11 | 7 |
| Ranging Raptors | 3 | 64 | 80% | 8 | 42% | 30% | +12 | 7 |
| Otepec Huntmaster | 2 | 74 | 99% | 8 | 42% | 29% | +12 | 2 |
| Chandra's Ignition | 5 | 67 | 55% | 9 | 42% | 30% | +12 | 14 |
| From the Rubble | 6 | 60 | 60% | 9.5 | 42% | 31% | +11 | 12 |
| Shifting Ceratops | 4 | 65 | 65% | 8.0 | 42% | 30% | +11 | 14 |
| Dinosaur Egg | 2 | 51 | 84% | 8 | 41% | 32% | +10 | 7 |
| Wayta, Trainer Prodigy | 3 | 49 | 96% | 8 | 41% | 32% | +9 | 2 |
| Runic Armasaur | 3 | 54 | 83% | 9 | 41% | 32% | +9 | 5 |
| Temple Altisaur | 5 | 59 | 71% | 10.0 | 41% | 31% | +9 | 15 |
| Descendants' Path | 3 | 62 | 94% | 8.5 | 40% | 31% | +9 | 2 |
| Arcane Signet | 2 | 80 | 96% | 7 | 40% | 30% | +10 | 1 |
| Itzquinth, Firstborn of Gishath | 2 | 46 | 65% | 6.5 | 39% | 32% | +7 | 10 |
| Thrashing Brontodon | 3 | 64 | 70% | 10 | 39% | 32% | +8 | 13 |
| Raging Regisaur | 4 | 70 | 66% | 10.0 | 39% | 32% | +7 | 17 |
| Raging Swordtooth | 5 | 65 | 89% | 10.0 | 38% | 32% | +7 | 7 |
| Rampaging Brontodon | 7 | 60 | 77% | 10.0 | 38% | 32% | +6 | 13 |
| Thundering Spineback | 7 | 47 | 72% | 9.0 | 38% | 33% | +6 | 8 |
| Sunfrill Imitator | 3 | 79 | 77% | 9 | 38% | 31% | +7 | 9 |
| Lifecrafter's Bestiary | 3 | 68 | 97% | 7.0 | 37% | 33% | +4 | 3 |
| Progenitor's Icon | 3 | 79 | 96% | 6.5 | 37% | 32% | +4 | 2 |
| Drover of the Mighty | 2 | 63 | 97% | 8 | 36% | 33% | +4 | 1 |
| Ripjaw Raptor | 4 | 63 | 68% | 10 | 36% | 33% | +4 | 13 |
| Majestic Heliopterus | 4 | 75 | 75% | 9.0 | 36% | 33% | +3 | 12 |
| Regisaur Alpha | 5 | 48 | 71% | 9.5 | 35% | 34% | +2 | 15 |
| Ixalli's Lorekeeper | 1 | 71 | 99% | 6.0 | 35% | 33% | +2 | 0 |
| Deathgorge Scavenger | 3 | 69 | 61% | 9.0 | 35% | 34% | +1 | 15 |
| Rhythm of the Wild | 3 | 49 | 92% | 7 | 35% | 34% | +1 | 2 |
| Return of the Wildspeaker | 5 | 63 | 68% | 9 | 33% | 34% | -1 | 13 |
| Verdant Sun's Avatar | 7 | 48 | 60% | 10 | 33% | 34% | -1 | 11 |
| Marauding Raptor | 2 | 58 | 0% |  | 33% | 34% | -2 | 29 |
| Generous Gift | 3 | 52 | 96% | 7.0 | 33% | 34% | -2 | 3 |
| Bronzebeak Foragers | 4 | 40 | 55% | 9.0 | 30% | 35% | -5 | 14 |
