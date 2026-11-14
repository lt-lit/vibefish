# Playtest: blight-curse

- List: `Blight Curse [ECC] [2026].dck`
- Pilot: playbook `blight-curse-wretch.json` version 1, go_wide attack (arm `playbook`). Commander: Auntie Ool, Cursewretch
- Table: 4 players, opponents drawn from `bots-v2`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261260, snapshot-2026-11-10

## Result

**41 wins in 200 tables: 20.5%** (95% 15% to 27%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 10 of 50, 11 of 50, 10 of 50, 10 of 50.
Games ran 44.8 turns in all. It won on its own turn 12.7 on average. When it lost it was out by its own turn 10.8.
Of its 155 losses it was the first player out in 48, the second in 47, the last opponent standing in 60. What took it out: LifeReachedZero 148, Milled 3, OpponentWon 3, IntentionalDraw 3, CommanderDamage 2.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| tricky-terrain | 49 | 13 (26%) | 8 (16%) | 7 |
| elven-council | 41 | 10 (24%) | 10 (24%) | 10 |
| eldrazi-incursion | 50 | 11 (22%) | 11 (22%) | 14 |
| goblin-storm | 50 | 11 (22%) | 23 (46%) | 21 |
| token-triumph | 50 | 11 (22%) | 15 (30%) | 17 |
| planeswalker-party | 51 | 11 (22%) | 8 (16%) | 6 |
| deep-clue-sea | 52 | 11 (21%) | 15 (29%) | 11 |
| hail-caesar | 48 | 10 (21%) | 15 (31%) | 10 |
| quick-draw | 55 | 11 (20%) | 19 (34%) | 13 |
| enduring-enchantments | 52 | 9 (17%) | 19 (36%) | 19 |
| wretched-ranks | 54 | 8 (15%) | 9 (17%) | 9 |
| limit-break | 48 | 7 (15%) | 3 (6%) | 3 |

## Tempo

- A mulligan in 26% of games. Lands at the start of its own turns 4, 6, 8: 2.79, 4.4, 5.87; cards in hand: 5.89, 5.83, 5.94. Short of four lands at the start of turn 5 in 32% of games.
- Commander first cast on its own turn 4 (median; quartiles 4 to 5), never cast in 2% of games, 2.06 casts a game.
- 14.8 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 6%.
- Damage dealt 20.5 a game (5.3 of it by the commander), taken 53.2.
- When it lost it held 4.88 nonland cards, 4.47 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (60 cards); the deck won 20.5% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Fire Covenant | 3 | 65 | 0% |  | 29% | 16% | +13 | 40 |
| Black Sun's Zenith | 2 | 57 | 0% |  | 25% | 19% | +6 | 36 |
| Soul Snuffers | 4 | 65 | 3% | 10.0 | 25% | 18% | +6 | 35 |
| Liliana, Death Wielder | 7 | 56 | 14% | 11.0 | 21% | 20% | +1 | 26 |
| Incremental Blight | 5 | 54 | 18% | 9.5 | 32% | 16% | +15 | 26 |
| Binding the Old Gods | 4 | 42 | 19% | 9.5 | 24% | 20% | +4 | 16 |
| Eventide's Shadow | 5 | 66 | 20% | 9 | 20% | 21% | -1 | 36 |
| Chain Reaction | 4 | 59 | 24% | 8.5 | 19% | 21% | -3 | 33 |
| Aberrant Return | 6 | 62 | 26% | 10.5 | 29% | 17% | +12 | 29 |
| Skinrender | 4 | 58 | 26% | 11 | 24% | 19% | +5 | 22 |
| Ferrafor, Young Yew | 7 | 54 | 26% | 10.5 | 32% | 16% | +15 | 17 |
| Midnight Banshee | 6 | 61 | 30% | 9.5 | 26% | 18% | +8 | 21 |
| Channeler Initiate | 2 | 71 | 38% | 3 | 35% | 12% | +23 | 19 |
| Puppeteer Clique | 5 | 60 | 40% | 9.5 | 28% | 17% | +11 | 25 |
| Blowfly Infestation | 3 | 61 | 44% | 9 | 23% | 19% | +4 | 18 |
| Grim Poppet | 7 | 50 | 46% | 9 | 28% | 18% | +10 | 11 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Channeler Initiate | 2 | 71 | 38% | 3 | 35% | 12% | +23 | 19 |
| Ignoble Hierarch | 1 | 52 | 98% | 6 | 35% | 16% | +19 | 1 |
| Chimil, the Inner Sun | 6 | 37 | 60% | 9.0 | 32% | 18% | +15 | 3 |
| Contagion Clasp | 2 | 59 | 73% | 7 | 32% | 16% | +17 | 8 |
| Ferrafor, Young Yew | 7 | 54 | 26% | 10.5 | 32% | 16% | +15 | 17 |
| Incremental Blight | 5 | 54 | 18% | 9.5 | 32% | 16% | +15 | 26 |
| Necroskitter | 3 | 51 | 65% | 8 | 31% | 17% | +15 | 11 |
| Tree of Perdition | 4 | 51 | 72% | 9 | 31% | 17% | +15 | 15 |
| Cathartic Reunion | 2 | 66 | 88% | 7.0 | 30% | 16% | +15 | 7 |
| Grave Venerations | 4 | 60 | 92% | 7 | 30% | 16% | +14 | 4 |
| Vraska, Betrayal's Sting | 6 | 60 | 82% | 9 | 30% | 16% | +14 | 5 |
| Archfiend of Ifnir | 5 | 64 | 70% | 9 | 30% | 16% | +13 | 11 |
| Fire Covenant | 3 | 65 | 0% |  | 29% | 16% | +13 | 40 |
| Hoarder's Greed | 4 | 55 | 87% | 7.0 | 29% | 17% | +12 | 6 |
| Aberrant Return | 6 | 62 | 26% | 10.5 | 29% | 17% | +12 | 29 |
| Flourishing Defenses | 5 | 52 | 85% | 8.0 | 29% | 18% | +11 | 5 |
| Puppeteer Clique | 5 | 60 | 40% | 9.5 | 28% | 17% | +11 | 25 |
| Terminate | 2 | 60 | 97% | 6.0 | 28% | 17% | +11 | 1 |
| Carnifex Demon | 6 | 64 | 62% | 9.0 | 28% | 17% | +11 | 18 |
| Grim Poppet | 7 | 50 | 46% | 9 | 28% | 18% | +10 | 11 |
| Grave Titan | 6 | 51 | 72% | 9 | 28% | 18% | +9 | 17 |
| Arcane Signet | 2 | 62 | 100% | 6.0 | 27% | 17% | +10 | 1 |
| Dread Tiller | 3 | 55 | 69% | 8.0 | 27% | 18% | +9 | 6 |
| Harmonize | 4 | 55 | 89% | 7 | 27% | 18% | +9 | 8 |
| Putrefy | 3 | 59 | 93% | 8 | 27% | 18% | +9 | 2 |
| Hapatra, Vizier of Poisons | 2 | 74 | 97% | 8.0 | 27% | 17% | +10 | 6 |
| Cathartic Pyre | 2 | 56 | 96% | 8.0 | 27% | 18% | +9 | 3 |
| Sol Ring | 1 | 60 | 97% | 6.0 | 27% | 18% | +9 | 1 |
| Night's Whisper | 2 | 53 | 96% | 7 | 26% | 18% | +8 | 1 |
| Midnight Banshee | 6 | 61 | 30% | 9.5 | 26% | 18% | +8 | 21 |
| Wickersmith's Tools | 3 | 65 | 98% | 7.0 | 26% | 18% | +8 | 3 |
| Painful Truths | 3 | 59 | 93% | 7 | 25% | 18% | +7 | 6 |
| Sinister Gnarlbark | 3 | 59 | 97% | 6 | 25% | 18% | +7 | 5 |
| The Scorpion God | 5 | 59 | 66% | 9 | 25% | 18% | +7 | 22 |
| Village Pillagers | 5 | 63 | 60% | 9.5 | 25% | 18% | +7 | 25 |
| Devoted Druid | 2 | 73 | 96% | 6.0 | 25% | 18% | +7 | 4 |
| Black Sun's Zenith | 2 | 57 | 0% |  | 25% | 19% | +6 | 36 |
| Soul Snuffers | 4 | 65 | 3% | 10.0 | 25% | 18% | +6 | 35 |
| Commander's Sphere | 3 | 54 | 96% | 6.0 | 24% | 19% | +5 | 2 |
| Skinrender | 4 | 58 | 26% | 11 | 24% | 19% | +5 | 22 |
| Binding the Old Gods | 4 | 42 | 19% | 9.5 | 24% | 20% | +4 | 16 |
| Glissa Sunslayer | 3 | 63 | 76% | 8.0 | 24% | 19% | +5 | 10 |
| Kulrath Knight | 5 | 63 | 71% | 8 | 24% | 19% | +5 | 14 |
| Infernal Grasp | 2 | 59 | 92% | 7.0 | 24% | 19% | +5 | 4 |
| Everlasting Torment | 3 | 51 | 51% | 7.5 | 24% | 20% | +4 | 15 |
| The Reaper, King No More | 6 | 56 | 62% | 7 | 23% | 19% | +4 | 9 |
| Blowfly Infestation | 3 | 61 | 44% | 9 | 23% | 19% | +4 | 18 |
| Evolution Sage | 3 | 71 | 94% | 8 | 22% | 19% | +3 | 5 |
| Massacre Girl, Known Killer | 4 | 59 | 70% | 8 | 22% | 20% | +2 | 18 |
| Lasting Tarfire | 2 | 60 | 98% | 8 | 22% | 20% | +2 | 4 |
| Liliana, Death Wielder | 7 | 56 | 14% | 11.0 | 21% | 20% | +1 | 26 |
| Assassin's Trophy | 2 | 61 | 98% | 6.0 | 21% | 20% | +1 | 1 |
| Wickerbough Elder | 4 | 55 | 71% | 9 | 20% | 21% | -1 | 18 |
| Eventide's Shadow | 5 | 66 | 20% | 9 | 20% | 21% | -1 | 36 |
| Oft-Nabbed Goat | 2 | 56 | 98% | 6 | 20% | 21% | -1 | 3 |
| Persist | 2 | 56 | 75% | 9.0 | 20% | 21% | -1 | 16 |
| Puca's Covenant | 3 | 64 | 94% | 7.0 | 19% | 21% | -2 | 4 |
| Chain Reaction | 4 | 59 | 24% | 8.5 | 19% | 21% | -3 | 33 |
| Dusk Urchins | 3 | 62 | 73% | 7 | 18% | 22% | -4 | 12 |
| Burning Curiosity | 3 | 54 | 94% | 8 | 15% | 23% | -8 | 6 |
