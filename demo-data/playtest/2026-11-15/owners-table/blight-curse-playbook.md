# Playtest: blight-curse

- List: `Blight Curse [ECC] [2026].dck`
- Pilot: playbook `blight-curse.json` version 2, Forge's attack (arm `playbook`). Commander: Auntie Ool, Cursewretch
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**53 wins in 200 tables: 26.5%** (95% 21% to 33%); an even share is 25%. 3 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 16 of 50, 8 of 50, 18 of 50, 11 of 50.
Games ran 45.0 turns in all. It won on its own turn 13.5 on average. When it lost it was out by its own turn 10.7.
Of its 144 losses it was the first player out in 38, the second in 48, the last opponent standing in 58. What took it out: LifeReachedZero 143, CommanderDamage 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| squirreled-away | 75 | 28 (37%) | 12 (16%) | 6 |
| miracle-worker | 61 | 22 (36%) | 14 (23%) | 11 |
| death-toll | 65 | 18 (28%) | 16 (25%) | 15 |
| blood-rites | 76 | 21 (28%) | 23 (30%) | 18 |
| deadly-disguise | 65 | 17 (26%) | 11 (17%) | 8 |
| veloci-ramp-tor | 62 | 15 (24%) | 22 (36%) | 23 |
| mutant-menace | 68 | 15 (22%) | 13 (19%) | 16 |
| revenant-recon | 66 | 14 (21%) | 14 (21%) | 9 |
| ahoy-mateys | 62 | 9 (14%) | 19 (31%) | 22 |

## Tempo

- A mulligan in 16% of games. Lands at the start of its own turns 4, 6, 8: 2.75, 4.39, 5.91; cards in hand: 5.96, 5.59, 5.56. Short of four lands at the start of turn 5 in 38% of games.
- Commander first cast on its own turn 5.0 (median; quartiles 4 to 5), never cast in 0% of games, 2.48 casts a game.
- 16.0 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 4%.
- Damage dealt 23.2 a game (4.7 of it by the commander), taken 36.3.
- When it lost it held 4.49 nonland cards, 4.26 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 26.5% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Fire Covenant | 3 | 50 | 0% |  | 34% | 24% | +10 | 30 |
| Eventide's Shadow | 5 | 57 | 12% | 11 | 32% | 24% | +7 | 25 |
| Black Sun's Zenith | 2 | 69 | 36% | 9 | 28% | 26% | +2 | 29 |
| The Scorpion God | 5 | 61 | 41% | 11 | 38% | 22% | +16 | 27 |
| Carnifex Demon | 6 | 64 | 42% | 11 | 42% | 19% | +23 | 19 |
| Grim Poppet | 7 | 60 | 45% | 12 | 40% | 21% | +19 | 14 |
| Archfiend of Ifnir | 5 | 68 | 46% | 11 | 32% | 24% | +9 | 23 |
| Tree of Perdition | 4 | 61 | 46% | 7.0 | 34% | 23% | +11 | 18 |
| Wickerbough Elder | 4 | 56 | 46% | 9.0 | 34% | 24% | +10 | 10 |
| Puppeteer Clique | 5 | 75 | 47% | 10 | 31% | 24% | +7 | 23 |
| Aberrant Return | 6 | 62 | 47% | 10 | 34% | 23% | +11 | 19 |
| Everlasting Torment | 3 | 61 | 48% | 8 | 34% | 23% | +11 | 15 |
| Kulrath Knight | 5 | 56 | 48% | 10 | 38% | 22% | +15 | 15 |
| Ferrafor, Young Yew | 7 | 66 | 48% | 10.0 | 33% | 23% | +10 | 17 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Grave Venerations | 4 | 59 | 81% | 8.0 | 42% | 20% | +22 | 4 |
| Carnifex Demon | 6 | 64 | 42% | 11 | 42% | 19% | +23 | 19 |
| Lasting Tarfire | 2 | 62 | 94% | 7.0 | 42% | 20% | +22 | 2 |
| Flourishing Defenses | 5 | 48 | 65% | 9 | 42% | 22% | +20 | 8 |
| Dusk Urchins | 3 | 53 | 70% | 8 | 42% | 21% | +20 | 8 |
| Village Pillagers | 5 | 59 | 76% | 9 | 41% | 21% | +20 | 14 |
| Sol Ring | 1 | 52 | 100% | 6.0 | 40% | 22% | +19 | 2 |
| Grim Poppet | 7 | 60 | 45% | 12 | 40% | 21% | +19 | 14 |
| Channeler Initiate | 2 | 56 | 62% | 5 | 39% | 22% | +18 | 5 |
| Skinrender | 4 | 61 | 74% | 7 | 39% | 21% | +18 | 8 |
| Binding the Old Gods | 4 | 63 | 75% | 8 | 38% | 21% | +17 | 9 |
| The Reaper, King No More | 6 | 45 | 56% | 8 | 38% | 23% | +15 | 8 |
| The Scorpion God | 5 | 61 | 41% | 11 | 38% | 22% | +16 | 27 |
| Kulrath Knight | 5 | 56 | 48% | 10 | 38% | 22% | +15 | 15 |
| Harmonize | 4 | 69 | 55% | 9.5 | 36% | 21% | +15 | 21 |
| Blowfly Infestation | 3 | 72 | 76% | 7 | 36% | 21% | +15 | 5 |
| Incremental Blight | 5 | 61 | 74% | 10 | 36% | 22% | +14 | 11 |
| Soul Snuffers | 4 | 61 | 85% | 9.0 | 36% | 22% | +14 | 6 |
| Contagion Clasp | 2 | 50 | 64% | 8.0 | 36% | 23% | +13 | 8 |
| Vraska, Betrayal's Sting | 6 | 67 | 76% | 9 | 36% | 22% | +14 | 8 |
| Arcane Signet | 2 | 56 | 98% | 6 | 36% | 23% | +13 | 3 |
| Assassin's Trophy | 2 | 59 | 98% | 7.0 | 36% | 23% | +13 | 2 |
| Sinister Gnarlbark | 3 | 59 | 93% | 7 | 36% | 23% | +13 | 1 |
| Cathartic Reunion | 2 | 79 | 78% | 7.5 | 35% | 21% | +15 | 11 |
| Ignoble Hierarch | 1 | 57 | 96% | 5 | 35% | 23% | +12 | 0 |
| Evolution Sage | 3 | 63 | 92% | 7.0 | 35% | 23% | +12 | 4 |
| Infernal Grasp | 2 | 72 | 90% | 7 | 35% | 22% | +13 | 1 |
| Liliana, Death Wielder | 7 | 52 | 50% | 11.0 | 35% | 24% | +11 | 16 |
| Necroskitter | 3 | 58 | 59% | 8.0 | 34% | 23% | +11 | 10 |
| Everlasting Torment | 3 | 61 | 48% | 8 | 34% | 23% | +11 | 15 |
| Tree of Perdition | 4 | 61 | 46% | 7.0 | 34% | 23% | +11 | 18 |
| Fire Covenant | 3 | 50 | 0% |  | 34% | 24% | +10 | 30 |
| Aberrant Return | 6 | 62 | 47% | 10 | 34% | 23% | +11 | 19 |
| Wickerbough Elder | 4 | 56 | 46% | 9.0 | 34% | 24% | +10 | 10 |
| Burning Curiosity | 3 | 57 | 68% | 8 | 33% | 24% | +10 | 14 |
| Ferrafor, Young Yew | 7 | 66 | 48% | 10.0 | 33% | 23% | +10 | 17 |
| Midnight Banshee | 6 | 60 | 75% | 9 | 33% | 24% | +10 | 14 |
| Night's Whisper | 2 | 73 | 81% | 6 | 33% | 23% | +10 | 8 |
| Putrefy | 3 | 61 | 98% | 7.5 | 33% | 24% | +9 | 6 |
| Archfiend of Ifnir | 5 | 68 | 46% | 11 | 32% | 24% | +9 | 23 |
| Oft-Nabbed Goat | 2 | 62 | 95% | 8 | 32% | 24% | +8 | 1 |
| Hoarder's Greed | 4 | 53 | 51% | 9 | 32% | 24% | +8 | 15 |
| Dread Tiller | 3 | 60 | 58% | 8 | 32% | 24% | +7 | 12 |
| Wickersmith's Tools | 3 | 63 | 97% | 7 | 32% | 24% | +8 | 1 |
| Eventide's Shadow | 5 | 57 | 12% | 11 | 32% | 24% | +7 | 25 |
| Grave Titan | 6 | 64 | 62% | 10.5 | 31% | 24% | +7 | 15 |
| Persist | 2 | 65 | 66% | 10 | 31% | 24% | +6 | 19 |
| Puppeteer Clique | 5 | 75 | 47% | 10 | 31% | 24% | +7 | 23 |
| Massacre Girl, Known Killer | 4 | 49 | 59% | 8 | 31% | 25% | +5 | 12 |
| Puca's Covenant | 3 | 56 | 88% | 7 | 30% | 25% | +5 | 1 |
| Glissa Sunslayer | 3 | 63 | 76% | 8.0 | 30% | 25% | +5 | 8 |
| Painful Truths | 3 | 67 | 79% | 8 | 30% | 25% | +5 | 12 |
| Commander's Sphere | 3 | 64 | 98% | 5 | 30% | 25% | +5 | 3 |
| Hapatra, Vizier of Poisons | 2 | 68 | 97% | 7.0 | 29% | 25% | +4 | 6 |
| Devoted Druid | 2 | 62 | 98% | 8 | 29% | 25% | +4 | 4 |
| Terminate | 2 | 69 | 96% | 7.0 | 29% | 25% | +4 | 4 |
| Chimil, the Inner Sun | 6 | 54 | 67% | 8.5 | 28% | 26% | +2 | 11 |
| Cathartic Pyre | 2 | 65 | 92% | 7.0 | 28% | 26% | +2 | 2 |
| Black Sun's Zenith | 2 | 69 | 36% | 9 | 28% | 26% | +2 | 29 |
| Chain Reaction | 4 | 68 | 59% | 10.0 | 26% | 26% | +0 | 19 |
