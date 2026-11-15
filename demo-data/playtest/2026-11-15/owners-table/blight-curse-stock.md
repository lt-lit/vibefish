# Playtest: blight-curse

- List: `Blight Curse [ECC] [2026].dck`
- Pilot: stock Forge AI (arm `stock`). Commander: Auntie Ool, Cursewretch
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**41 wins in 200 tables: 20.5%** (95% 15% to 27%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 10 of 50, 12 of 50, 10 of 50, 9 of 50.
Games ran 45.7 turns in all. It won on its own turn 13.0 on average. When it lost it was out by its own turn 11.2.
Of its 155 losses it was the first player out in 49, the second in 49, the last opponent standing in 57. What took it out: LifeReachedZero 149, CommanderDamage 3, Milled 3, IntentionalDraw 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| deadly-disguise | 65 | 18 (28%) | 3 (5%) | 8 |
| squirreled-away | 75 | 18 (24%) | 14 (19%) | 10 |
| revenant-recon | 66 | 15 (23%) | 15 (23%) | 12 |
| ahoy-mateys | 62 | 13 (21%) | 19 (31%) | 16 |
| mutant-menace | 68 | 14 (21%) | 20 (29%) | 19 |
| death-toll | 65 | 13 (20%) | 18 (28%) | 12 |
| miracle-worker | 61 | 12 (20%) | 19 (31%) | 12 |
| veloci-ramp-tor | 62 | 10 (16%) | 21 (34%) | 18 |
| blood-rites | 76 | 10 (13%) | 26 (34%) | 20 |

## Tempo

- A mulligan in 16% of games. Lands at the start of its own turns 4, 6, 8: 2.75, 4.29, 5.77; cards in hand: 5.98, 5.55, 5.11. Short of four lands at the start of turn 5 in 38% of games.
- Commander first cast on its own turn 5 (median; quartiles 4 to 7), never cast in 12% of games, 1.43 casts a game.
- 13.6 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 9%.
- Damage dealt 19.1 a game (2.4 of it by the commander), taken 36.7.
- When it lost it held 4.01 nonland cards, 3.85 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 20.5% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Channeler Initiate | 2 | 59 | 0% |  | 29% | 17% | +12 | 31 |
| Black Sun's Zenith | 2 | 58 | 0% |  | 29% | 17% | +12 | 36 |
| Devoted Druid | 2 | 56 | 0% |  | 29% | 17% | +11 | 29 |
| Fire Covenant | 3 | 45 | 0% |  | 27% | 19% | +8 | 29 |
| Cathartic Reunion | 2 | 62 | 8% | 11 | 29% | 17% | +12 | 29 |
| Soul Snuffers | 4 | 49 | 14% | 9 | 24% | 19% | +5 | 27 |
| Painful Truths | 3 | 57 | 39% | 9.0 | 18% | 22% | -4 | 27 |
| Harmonize | 4 | 60 | 43% | 10.0 | 30% | 16% | +14 | 20 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Massacre Girl, Known Killer | 4 | 52 | 86% | 7 | 35% | 16% | +19 | 3 |
| Ferrafor, Young Yew | 7 | 61 | 75% | 9.0 | 34% | 14% | +20 | 12 |
| Chimil, the Inner Sun | 6 | 55 | 73% | 10.0 | 33% | 16% | +17 | 11 |
| Midnight Banshee | 6 | 52 | 75% | 9 | 33% | 16% | +16 | 7 |
| Harmonize | 4 | 60 | 43% | 10.0 | 30% | 16% | +14 | 20 |
| The Reaper, King No More | 6 | 50 | 78% | 8 | 30% | 17% | +13 | 3 |
| Black Sun's Zenith | 2 | 58 | 0% |  | 29% | 17% | +12 | 36 |
| Everlasting Torment | 3 | 55 | 67% | 7 | 29% | 17% | +12 | 11 |
| Necroskitter | 3 | 55 | 60% | 8 | 29% | 17% | +12 | 13 |
| Aberrant Return | 6 | 62 | 89% | 9 | 29% | 17% | +12 | 6 |
| Cathartic Reunion | 2 | 62 | 8% | 11 | 29% | 17% | +12 | 29 |
| Archfiend of Ifnir | 5 | 59 | 71% | 8.0 | 29% | 17% | +12 | 6 |
| Channeler Initiate | 2 | 59 | 0% |  | 29% | 17% | +12 | 31 |
| Binding the Old Gods | 4 | 63 | 51% | 9.5 | 29% | 17% | +12 | 18 |
| Burning Curiosity | 3 | 49 | 96% | 7 | 29% | 18% | +11 | 1 |
| Devoted Druid | 2 | 56 | 0% |  | 29% | 17% | +11 | 29 |
| Persist | 2 | 47 | 85% | 9.0 | 28% | 18% | +9 | 7 |
| Oft-Nabbed Goat | 2 | 55 | 84% | 6.5 | 27% | 18% | +9 | 6 |
| Blowfly Infestation | 3 | 59 | 54% | 8.5 | 27% | 18% | +9 | 10 |
| Village Pillagers | 5 | 63 | 87% | 8 | 27% | 18% | +10 | 9 |
| Carnifex Demon | 6 | 52 | 83% | 9 | 27% | 18% | +9 | 4 |
| Grave Venerations | 4 | 56 | 61% | 8.0 | 27% | 18% | +9 | 12 |
| Fire Covenant | 3 | 45 | 0% |  | 27% | 19% | +8 | 29 |
| Incremental Blight | 5 | 60 | 85% | 9 | 27% | 18% | +9 | 4 |
| Commander's Sphere | 3 | 53 | 60% | 5.5 | 26% | 18% | +8 | 9 |
| Wickerbough Elder | 4 | 46 | 83% | 8.0 | 26% | 19% | +7 | 4 |
| Flourishing Defenses | 5 | 50 | 56% | 10.0 | 26% | 19% | +7 | 10 |
| Sol Ring | 1 | 54 | 94% | 7 | 26% | 18% | +7 | 3 |
| Contagion Clasp | 2 | 51 | 71% | 7.0 | 26% | 19% | +7 | 6 |
| Eventide's Shadow | 5 | 48 | 71% | 11.0 | 25% | 19% | +6 | 12 |
| Hoarder's Greed | 4 | 44 | 91% | 7.5 | 25% | 19% | +6 | 1 |
| Night's Whisper | 2 | 73 | 64% | 8 | 25% | 18% | +7 | 18 |
| Soul Snuffers | 4 | 49 | 14% | 9 | 24% | 19% | +5 | 27 |
| Vraska, Betrayal's Sting | 6 | 53 | 76% | 9.0 | 24% | 19% | +5 | 7 |
| Lasting Tarfire | 2 | 62 | 73% | 9 | 24% | 19% | +5 | 5 |
| Arcane Signet | 2 | 46 | 87% | 7.0 | 24% | 20% | +4 | 2 |
| Liliana, Death Wielder | 7 | 46 | 76% | 9 | 24% | 20% | +4 | 7 |
| Tree of Perdition | 4 | 67 | 79% | 9 | 24% | 19% | +5 | 12 |
| Terminate | 2 | 59 | 98% | 6.0 | 24% | 19% | +5 | 1 |
| Puppeteer Clique | 5 | 56 | 86% | 7.0 | 23% | 19% | +4 | 4 |
| Putrefy | 3 | 65 | 95% | 7.5 | 23% | 19% | +4 | 4 |
| Chain Reaction | 4 | 61 | 66% | 8.0 | 23% | 19% | +4 | 14 |
| Ignoble Hierarch | 1 | 54 | 98% | 5 | 22% | 20% | +2 | 3 |
| Puca's Covenant | 3 | 46 | 56% | 7.5 | 22% | 20% | +2 | 7 |
| Kulrath Knight | 5 | 51 | 67% | 7.0 | 22% | 20% | +1 | 12 |
| The Scorpion God | 5 | 47 | 70% | 8 | 21% | 20% | +1 | 10 |
| Grim Poppet | 7 | 50 | 56% | 10.0 | 20% | 21% | -1 | 8 |
| Assassin's Trophy | 2 | 51 | 96% | 7 | 20% | 21% | -1 | 0 |
| Dusk Urchins | 3 | 56 | 79% | 7.0 | 20% | 21% | -1 | 8 |
| Skinrender | 4 | 56 | 66% | 9 | 20% | 21% | -1 | 11 |
| Infernal Grasp | 2 | 62 | 95% | 6 | 19% | 21% | -2 | 4 |
| Glissa Sunslayer | 3 | 57 | 91% | 8.0 | 19% | 21% | -2 | 8 |
| Grave Titan | 6 | 52 | 75% | 9 | 19% | 21% | -2 | 7 |
| Sinister Gnarlbark | 3 | 52 | 75% | 8 | 19% | 21% | -2 | 9 |
| Dread Tiller | 3 | 53 | 87% | 7.0 | 19% | 21% | -2 | 5 |
| Wickersmith's Tools | 3 | 48 | 62% | 8.0 | 19% | 21% | -2 | 10 |
| Cathartic Pyre | 2 | 59 | 93% | 6 | 19% | 21% | -3 | 3 |
| Painful Truths | 3 | 57 | 39% | 9.0 | 18% | 22% | -4 | 27 |
| Hapatra, Vizier of Poisons | 2 | 56 | 80% | 6 | 16% | 22% | -6 | 13 |
| Evolution Sage | 3 | 50 | 72% | 7.0 | 14% | 23% | -9 | 13 |
