# Playtest: blight-curse

- List: `Blight Curse [ECC] [2026].dck`
- Pilot: stock Forge AI (arm `stock`). Commander: Auntie Ool, Cursewretch
- Table: 4 players, opponents drawn from `bots-v2`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261260, snapshot-2026-11-10

## Result

**46 wins in 200 tables: 23.0%** (95% 18% to 29%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 16 of 50, 14 of 50, 8 of 50, 8 of 50.
Games ran 46.4 turns in all. It won on its own turn 14.5 on average. When it lost it was out by its own turn 11.1.
Of its 150 losses it was the first player out in 40, the second in 53, the last opponent standing in 57. What took it out: LifeReachedZero 143, Milled 4, OpponentWon 4, IntentionalDraw 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| elven-council | 41 | 14 (34%) | 8 (20%) | 8 |
| token-triumph | 50 | 17 (34%) | 14 (28%) | 11 |
| tricky-terrain | 49 | 16 (33%) | 13 (26%) | 5 |
| deep-clue-sea | 52 | 13 (25%) | 14 (27%) | 11 |
| enduring-enchantments | 52 | 13 (25%) | 18 (35%) | 16 |
| eldrazi-incursion | 50 | 12 (24%) | 12 (24%) | 14 |
| limit-break | 48 | 10 (21%) | 8 (17%) | 9 |
| goblin-storm | 50 | 9 (18%) | 14 (28%) | 15 |
| planeswalker-party | 51 | 9 (18%) | 12 (24%) | 8 |
| wretched-ranks | 54 | 9 (17%) | 6 (11%) | 8 |
| quick-draw | 55 | 9 (16%) | 15 (27%) | 11 |
| hail-caesar | 48 | 7 (15%) | 16 (33%) | 10 |

## Tempo

- A mulligan in 26% of games. Lands at the start of its own turns 4, 6, 8: 2.79, 4.42, 5.9; cards in hand: 5.92, 5.54, 5.35. Short of four lands at the start of turn 5 in 34% of games.
- Commander first cast on its own turn 6 (median; quartiles 4 to 8), never cast in 14% of games, 1.48 casts a game.
- 14.0 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 10%.
- Damage dealt 22.8 a game (3.1 of it by the commander), taken 50.1.
- When it lost it held 4.39 nonland cards, 4.12 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 23.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Devoted Druid | 2 | 66 | 0% |  | 29% | 20% | +9 | 34 |
| Black Sun's Zenith | 2 | 63 | 0% |  | 24% | 23% | +1 | 42 |
| Fire Covenant | 3 | 54 | 0% |  | 30% | 20% | +9 | 32 |
| Channeler Initiate | 2 | 49 | 2% | 6 | 31% | 20% | +10 | 27 |
| Soul Snuffers | 4 | 56 | 12% | 8 | 29% | 21% | +8 | 31 |
| Cathartic Reunion | 2 | 58 | 22% | 12 | 36% | 18% | +19 | 26 |
| Harmonize | 4 | 62 | 29% | 9.5 | 36% | 17% | +18 | 24 |
| Painful Truths | 3 | 51 | 47% | 7.5 | 35% | 19% | +16 | 16 |
| Skinrender | 4 | 57 | 49% | 10.0 | 33% | 19% | +14 | 17 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Tree of Perdition | 4 | 61 | 69% | 9.5 | 44% | 14% | +31 | 11 |
| Chimil, the Inner Sun | 6 | 45 | 62% | 11.0 | 42% | 17% | +25 | 6 |
| Midnight Banshee | 6 | 54 | 67% | 9.0 | 39% | 17% | +22 | 9 |
| Puppeteer Clique | 5 | 52 | 88% | 8.0 | 36% | 18% | +18 | 7 |
| Cathartic Reunion | 2 | 58 | 22% | 12 | 36% | 18% | +19 | 26 |
| Harmonize | 4 | 62 | 29% | 9.5 | 36% | 17% | +18 | 24 |
| Painful Truths | 3 | 51 | 47% | 7.5 | 35% | 19% | +16 | 16 |
| Blowfly Infestation | 3 | 55 | 73% | 8.0 | 34% | 19% | +16 | 7 |
| Vraska, Betrayal's Sting | 6 | 64 | 78% | 9.0 | 34% | 18% | +17 | 14 |
| Burning Curiosity | 3 | 59 | 97% | 7 | 34% | 18% | +16 | 6 |
| Ignoble Hierarch | 1 | 59 | 95% | 8.0 | 34% | 18% | +16 | 4 |
| Putrefy | 3 | 59 | 95% | 8.0 | 34% | 18% | +16 | 4 |
| The Scorpion God | 5 | 62 | 86% | 9 | 34% | 18% | +16 | 14 |
| Arcane Signet | 2 | 54 | 80% | 6 | 33% | 19% | +14 | 5 |
| Carnifex Demon | 6 | 54 | 80% | 7 | 33% | 19% | +14 | 6 |
| Necroskitter | 3 | 48 | 75% | 8.5 | 33% | 20% | +14 | 6 |
| Skinrender | 4 | 57 | 49% | 10.0 | 33% | 19% | +14 | 17 |
| The Reaper, King No More | 6 | 61 | 70% | 8 | 33% | 19% | +14 | 7 |
| Persist | 2 | 55 | 78% | 9 | 33% | 19% | +13 | 14 |
| Sol Ring | 1 | 47 | 96% | 7 | 32% | 20% | +12 | 4 |
| Ferrafor, Young Yew | 7 | 44 | 59% | 8.0 | 32% | 20% | +11 | 8 |
| Hoarder's Greed | 4 | 60 | 92% | 7 | 32% | 19% | +12 | 3 |
| Assassin's Trophy | 2 | 73 | 97% | 7 | 32% | 18% | +13 | 3 |
| Grave Venerations | 4 | 51 | 72% | 9 | 31% | 20% | +11 | 11 |
| Cathartic Pyre | 2 | 48 | 92% | 7.0 | 31% | 20% | +11 | 1 |
| Infernal Grasp | 2 | 64 | 89% | 7 | 31% | 19% | +12 | 3 |
| Archfiend of Ifnir | 5 | 58 | 57% | 9 | 31% | 20% | +11 | 8 |
| Grave Titan | 6 | 65 | 80% | 10.0 | 31% | 19% | +12 | 6 |
| Channeler Initiate | 2 | 49 | 2% | 6 | 31% | 20% | +10 | 27 |
| Aberrant Return | 6 | 66 | 77% | 9 | 30% | 19% | +11 | 15 |
| Massacre Girl, Known Killer | 4 | 66 | 82% | 8.0 | 30% | 19% | +11 | 10 |
| Chain Reaction | 4 | 67 | 61% | 8 | 30% | 20% | +10 | 11 |
| Evolution Sage | 3 | 64 | 75% | 7.0 | 30% | 20% | +10 | 11 |
| Fire Covenant | 3 | 54 | 0% |  | 30% | 20% | +9 | 32 |
| Oft-Nabbed Goat | 2 | 51 | 86% | 6.0 | 29% | 21% | +9 | 5 |
| Kulrath Knight | 5 | 55 | 80% | 8.0 | 29% | 21% | +8 | 10 |
| Devoted Druid | 2 | 66 | 0% |  | 29% | 20% | +9 | 34 |
| Incremental Blight | 5 | 56 | 88% | 8 | 29% | 21% | +8 | 5 |
| Puca's Covenant | 3 | 56 | 68% | 7.0 | 29% | 21% | +8 | 13 |
| Soul Snuffers | 4 | 56 | 12% | 8 | 29% | 21% | +8 | 31 |
| Village Pillagers | 5 | 49 | 76% | 9 | 29% | 21% | +7 | 8 |
| Hapatra, Vizier of Poisons | 2 | 67 | 82% | 8 | 28% | 20% | +8 | 12 |
| Liliana, Death Wielder | 7 | 53 | 64% | 9.0 | 28% | 21% | +7 | 11 |
| Glissa Sunslayer | 3 | 58 | 90% | 7.0 | 28% | 21% | +7 | 3 |
| Wickersmith's Tools | 3 | 58 | 69% | 8.0 | 28% | 21% | +7 | 12 |
| Flourishing Defenses | 5 | 40 | 65% | 8.5 | 28% | 22% | +6 | 8 |
| Contagion Clasp | 2 | 55 | 71% | 7 | 27% | 21% | +6 | 9 |
| Wickerbough Elder | 4 | 48 | 81% | 5 | 27% | 22% | +5 | 7 |
| Terminate | 2 | 66 | 96% | 6 | 26% | 22% | +4 | 1 |
| Grim Poppet | 7 | 51 | 51% | 10.0 | 26% | 22% | +3 | 6 |
| Commander's Sphere | 3 | 44 | 75% | 6 | 25% | 22% | +3 | 6 |
| Dusk Urchins | 3 | 61 | 75% | 7.0 | 25% | 22% | +2 | 3 |
| Sinister Gnarlbark | 3 | 58 | 69% | 8.0 | 24% | 22% | +2 | 9 |
| Everlasting Torment | 3 | 50 | 60% | 8.0 | 24% | 23% | +1 | 15 |
| Black Sun's Zenith | 2 | 63 | 0% |  | 24% | 23% | +1 | 42 |
| Lasting Tarfire | 2 | 47 | 77% | 6.5 | 23% | 23% | +1 | 7 |
| Dread Tiller | 3 | 52 | 92% | 7.0 | 23% | 23% | +0 | 4 |
| Night's Whisper | 2 | 56 | 57% | 8.0 | 21% | 24% | -2 | 12 |
| Eventide's Shadow | 5 | 61 | 61% | 9 | 21% | 24% | -2 | 21 |
| Binding the Old Gods | 4 | 44 | 68% | 10.0 | 18% | 24% | -6 | 8 |
