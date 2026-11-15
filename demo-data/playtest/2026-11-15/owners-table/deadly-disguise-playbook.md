# Playtest: deadly-disguise

- List: `Deadly Disguise [MKC] [2024].dck`
- Pilot: playbook `deadly-disguise.json` version 2, Forge's attack (arm `playbook`). Commander: Kaust, Eyes of the Glade
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**18 wins in 200 tables: 9.0%** (95% 6% to 14%); an even share is 25%. 5 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 6 of 50, 3 of 50, 4 of 50, 5 of 50.
Games ran 45.8 turns in all. It won on its own turn 14.5 on average. When it lost it was out by its own turn 10.9.
Of its 177 losses it was the first player out in 41, the second in 76, the last opponent standing in 60. What took it out: LifeReachedZero 175, CommanderDamage 5.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| miracle-worker | 61 | 8 (13%) | 8 (13%) | 9 |
| squirreled-away | 75 | 9 (12%) | 20 (27%) | 12 |
| revenant-recon | 66 | 7 (11%) | 16 (24%) | 16 |
| blight-curse | 76 | 8 (10%) | 18 (24%) | 10 |
| mutant-menace | 68 | 6 (9%) | 21 (31%) | 23 |
| blood-rites | 65 | 5 (8%) | 26 (40%) | 18 |
| veloci-ramp-tor | 62 | 4 (6%) | 16 (26%) | 17 |
| death-toll | 65 | 4 (6%) | 25 (38%) | 14 |
| ahoy-mateys | 62 | 3 (5%) | 27 (44%) | 27 |

## Tempo

- A mulligan in 16% of games. Lands at the start of its own turns 4, 6, 8: 2.96, 4.47, 5.8; cards in hand: 6.02, 4.79, 4.12. Short of four lands at the start of turn 5 in 34% of games.
- Commander first cast on its own turn 3 (median; quartiles 2 to 4), never cast in 0% of games, 2.58 casts a game.
- 12.6 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 12%.
- Damage dealt 20.2 a game (2.3 of it by the commander), taken 42.9.
- When it lost it held 2.68 nonland cards, 2.36 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (62 cards); the deck won 9.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Boltbender | 4 | 44 | 0% |  | 16% | 7% | +9 | 14 |
| Akroma, Angel of Fury | 8 | 39 | 0% |  | 20% | 6% | +14 | 1 |
| Krosan Cloudscraper | 10 | 35 | 0% |  | 11% | 8% | +3 | 4 |
| Exalted Angel | 6 | 35 | 0% |  | 11% | 8% | +3 | 3 |
| Krosan Colossus | 9 | 34 | 0% |  | 15% | 8% | +7 | 6 |
| Salt Road Ambushers | 4 | 32 | 0% |  | 3% | 10% | -7 | 5 |
| Root Elemental | 6 | 30 | 0% |  | 13% | 8% | +5 | 3 |
| Experiment Twelve | 4 | 26 | 0% |  | 23% | 7% | +16 | 2 |
| Ashcloud Phoenix | 4 | 21 | 0% |  | 10% | 9% | +1 | 2 |
| Nantuko Vigilante | 4 | 39 | 3% | 10 | 13% | 8% | +5 | 10 |
| Imperial Hellkite | 7 | 28 | 4% | 16 | 14% | 8% | +6 | 2 |
| Deathmist Raptor | 3 | 38 | 8% | 6 | 5% | 10% | -5 | 9 |
| Yedora, Grave Gardener | 5 | 47 | 19% | 9 | 13% | 8% | +5 | 23 |
| Showstopping Surprise | 5 | 45 | 22% | 9.0 | 16% | 7% | +8 | 31 |
| Scourge of the Throne | 6 | 66 | 23% | 11 | 11% | 8% | +2 | 34 |
| Den Protector | 2 | 29 | 24% | 3 | 14% | 8% | +6 | 3 |
| Sidar Kondo of Jamuraa | 4 | 36 | 31% | 9 | 8% | 9% | -1 | 14 |
| Printlifter Ooze | 2 | 22 | 32% | 3 | 18% | 8% | +10 | 1 |
| Ohran Frostfang | 5 | 40 | 32% | 10 | 12% | 8% | +4 | 18 |
| Temur War Shaman | 6 | 44 | 34% | 11 | 7% | 10% | -3 | 18 |
| Hidden Dragonslayer | 2 | 37 | 35% | 4 | 14% | 8% | +6 | 5 |
| Master of Pearls | 2 | 25 | 36% | 7 | 12% | 9% | +3 | 3 |
| Broodhatch Nantuko | 2 | 26 | 38% | 4.0 | 12% | 9% | +3 | 1 |
| Ainok Survivalist | 2 | 28 | 39% | 5 | 4% | 10% | -6 | 3 |
| Seedborn Muse | 5 | 33 | 39% | 9 | 27% | 5% | +22 | 8 |
| Dusk // Dawn | 9 | 45 | 42% | 9 | 4% | 10% | -6 | 17 |
| Saryth, the Viper's Fang | 4 | 40 | 42% | 11 | 12% | 8% | +4 | 15 |
| Tesak, Judith's Hellhound | 4 | 49 | 43% | 9 | 8% | 9% | -1 | 23 |
| Hooded Hydra | 2 | 35 | 43% | 11 | 20% | 7% | +13 | 12 |
| Whisperwood Elemental | 5 | 50 | 44% | 9.0 | 12% | 8% | +4 | 16 |
| Unexplained Absence | 4 | 33 | 46% | 12 | 12% | 8% | +4 | 13 |
| Thelonite Hermit | 4 | 42 | 48% | 10.0 | 17% | 7% | +10 | 6 |
| Duskana, the Rage Mother | 5 | 44 | 48% | 9 | 14% | 8% | +6 | 15 |
| Nervous Gardener | 2 | 35 | 49% | 4 | 9% | 9% | -1 | 3 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Seedborn Muse | 5 | 33 | 39% | 9 | 27% | 5% | +22 | 8 |
| Experiment Twelve | 4 | 26 | 0% |  | 23% | 7% | +16 | 2 |
| Akroma, Angel of Fury | 8 | 39 | 0% |  | 20% | 6% | +14 | 1 |
| Hooded Hydra | 2 | 35 | 43% | 11 | 20% | 7% | +13 | 12 |
| Printlifter Ooze | 2 | 22 | 32% | 3 | 18% | 8% | +10 | 1 |
| Beast Whisperer | 4 | 39 | 56% | 9.5 | 18% | 7% | +11 | 10 |
| Mastery of the Unseen | 2 | 41 | 85% | 7 | 17% | 7% | +10 | 1 |
| Veiled Ascension | 4 | 47 | 92% | 7 | 17% | 6% | +11 | 2 |
| Thelonite Hermit | 4 | 42 | 48% | 10.0 | 17% | 7% | +10 | 6 |
| Sol Ring | 1 | 50 | 98% | 5 | 16% | 7% | +9 | 0 |
| Boltbender | 4 | 44 | 0% |  | 16% | 7% | +9 | 14 |
| Showstopping Surprise | 5 | 45 | 22% | 9.0 | 16% | 7% | +8 | 31 |
| Welcoming Vampire | 3 | 45 | 64% | 8 | 16% | 7% | +8 | 8 |
| Chaos Warp | 3 | 39 | 97% | 7.0 | 15% | 8% | +8 | 0 |
| Path to Exile | 1 | 46 | 98% | 4 | 15% | 7% | +8 | 1 |
| Krosan Colossus | 9 | 34 | 0% |  | 15% | 8% | +7 | 6 |
| Lifecrafter's Bestiary | 3 | 41 | 93% | 6.0 | 15% | 8% | +7 | 1 |
| Wild Growth | 1 | 48 | 100% | 5.0 | 15% | 7% | +7 | 3 |
| Decimate | 4 | 35 | 71% | 10 | 14% | 8% | +6 | 9 |
| Imperial Hellkite | 7 | 28 | 4% | 16 | 14% | 8% | +6 | 2 |
| Toski, Bearer of Secrets | 4 | 42 | 55% | 8 | 14% | 8% | +7 | 11 |
| Den Protector | 2 | 29 | 24% | 3 | 14% | 8% | +6 | 3 |
| Return of the Wildspeaker | 5 | 51 | 53% | 7 | 14% | 7% | +6 | 16 |
| Arcane Signet | 2 | 44 | 96% | 5.5 | 14% | 8% | +6 | 1 |
| Duskana, the Rage Mother | 5 | 44 | 48% | 9 | 14% | 8% | +6 | 15 |
| Jeska's Will | 3 | 44 | 73% | 9.0 | 14% | 8% | +6 | 10 |
| Hidden Dragonslayer | 2 | 37 | 35% | 4 | 14% | 8% | +6 | 5 |
| Root Elemental | 6 | 30 | 0% |  | 13% | 8% | +5 | 3 |
| Nature's Lore | 2 | 38 | 100% | 6.0 | 13% | 8% | +5 | 0 |
| Nantuko Vigilante | 4 | 39 | 3% | 10 | 13% | 8% | +5 | 10 |
| Panoptic Projektor | 4 | 39 | 92% | 5.0 | 13% | 8% | +5 | 2 |
| Scroll of Fate | 3 | 47 | 96% | 6 | 13% | 8% | +5 | 2 |
| Yedora, Grave Gardener | 5 | 47 | 19% | 9 | 13% | 8% | +5 | 23 |
| Fell the Mighty | 5 | 40 | 80% | 8.0 | 12% | 8% | +4 | 4 |
| Ohran Frostfang | 5 | 40 | 32% | 10 | 12% | 8% | +4 | 18 |
| Saryth, the Viper's Fang | 4 | 40 | 42% | 11 | 12% | 8% | +4 | 15 |
| True Identity | 2 | 32 | 50% | 4.0 | 12% | 8% | +4 | 3 |
| Unexplained Absence | 4 | 33 | 46% | 12 | 12% | 8% | +4 | 13 |
| Master of Pearls | 2 | 25 | 36% | 7 | 12% | 9% | +3 | 3 |
| Trail of Mystery | 2 | 50 | 96% | 4.5 | 12% | 8% | +4 | 2 |
| Whisperwood Elemental | 5 | 50 | 44% | 9.0 | 12% | 8% | +4 | 16 |
| Broodhatch Nantuko | 2 | 26 | 38% | 4.0 | 12% | 9% | +3 | 1 |
| Exalted Angel | 6 | 35 | 0% |  | 11% | 8% | +3 | 3 |
| Krosan Cloudscraper | 10 | 35 | 0% |  | 11% | 8% | +3 | 4 |
| Mirror Entity | 3 | 53 | 66% | 9 | 11% | 8% | +3 | 12 |
| Three Visits | 2 | 45 | 89% | 4.5 | 11% | 8% | +3 | 3 |
| Scourge of the Throne | 6 | 66 | 23% | 11 | 11% | 8% | +2 | 34 |
| Austere Command | 6 | 41 | 61% | 10 | 10% | 9% | +1 | 13 |
| Ashcloud Phoenix | 4 | 21 | 0% |  | 10% | 9% | +1 | 2 |
| Obscuring Aether | 1 | 43 | 91% | 5 | 9% | 9% | +0 | 3 |
| Nervous Gardener | 2 | 35 | 49% | 4 | 9% | 9% | -1 | 3 |
| Ugin's Mastery | 4 | 35 | 89% | 8 | 9% | 9% | -1 | 3 |
| Sakura-Tribe Elder | 2 | 47 | 100% | 5 | 8% | 9% | -1 | 1 |
| Ransom Note | 1 | 36 | 100% | 4.0 | 8% | 9% | -1 | 0 |
| Sidar Kondo of Jamuraa | 4 | 36 | 31% | 9 | 8% | 9% | -1 | 14 |
| Tesak, Judith's Hellhound | 4 | 49 | 43% | 9 | 8% | 9% | -1 | 23 |
| Temur War Shaman | 6 | 44 | 34% | 11 | 7% | 10% | -3 | 18 |
| Deathmist Raptor | 3 | 38 | 8% | 6 | 5% | 10% | -5 | 9 |
| Dusk // Dawn | 9 | 45 | 42% | 9 | 4% | 10% | -6 | 17 |
| Ainok Survivalist | 2 | 28 | 39% | 5 | 4% | 10% | -6 | 3 |
| Salt Road Ambushers | 4 | 32 | 0% |  | 3% | 10% | -7 | 5 |
| Neheb, the Eternal | 5 | 45 | 60% | 8 | 2% | 11% | -9 | 11 |
