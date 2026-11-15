# Playtest: squirreled-away

- List: `Squirreled Away [BLC] [2024].dck`
- Pilot: playbook `squirreled-away.json` version 3, Forge's attack (arm `playbook`). Commander: Hazel of the Rootbloom
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**36 wins in 200 tables: 18.0%** (95% 13% to 24%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 10 of 50, 7 of 50, 7 of 50, 12 of 50.
Games ran 47.1 turns in all. It won on its own turn 13.1 on average. When it lost it was out by its own turn 11.4.
Of its 160 losses it was the first player out in 50, the second in 52, the last opponent standing in 58. What took it out: LifeReachedZero 159, Milled 2, CommanderDamage 1.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| blight-curse | 76 | 17 (22%) | 16 (21%) | 13 |
| mutant-menace | 66 | 14 (21%) | 17 (26%) | 22 |
| miracle-worker | 68 | 14 (21%) | 20 (29%) | 17 |
| deadly-disguise | 65 | 13 (20%) | 7 (11%) | 7 |
| death-toll | 61 | 12 (20%) | 21 (34%) | 8 |
| revenant-recon | 75 | 13 (17%) | 21 (28%) | 23 |
| ahoy-mateys | 62 | 9 (14%) | 19 (31%) | 19 |
| veloci-ramp-tor | 62 | 8 (13%) | 18 (29%) | 16 |
| blood-rites | 65 | 8 (12%) | 21 (32%) | 16 |

## Tempo

- A mulligan in 28% of games. Lands at the start of its own turns 4, 6, 8: 2.89, 4.53, 5.91; cards in hand: 5.36, 4.51, 3.91. Short of four lands at the start of turn 5 in 23% of games.
- Commander first cast on its own turn 4.0 (median; quartiles 4 to 5), never cast in 1% of games, 2.46 casts a game.
- 14.8 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 3%.
- Damage dealt 24.8 a game (4.5 of it by the commander), taken 49.0.
- When it lost it held 3.11 nonland cards, 2.76 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (61 cards); the deck won 18.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Maelstrom Pulse | 3 | 60 | 0% |  | 25% | 15% | +10 | 42 |
| Shamanic Revelation | 5 | 44 | 27% | 11.0 | 25% | 16% | +9 | 23 |
| Decree of Pain | 8 | 39 | 36% | 10.0 | 13% | 19% | -6 | 14 |
| Plaguecrafter | 3 | 44 | 41% | 9.0 | 18% | 18% | +0 | 20 |
| End-Raze Forerunners | 8 | 54 | 44% | 11.0 | 17% | 18% | -2 | 24 |
| Maskwood Nexus | 4 | 48 | 48% | 10 | 21% | 17% | +4 | 20 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Zulaport Cutthroat | 2 | 59 | 95% | 8.0 | 37% | 10% | +27 | 4 |
| Bastion of Remembrance | 3 | 48 | 85% | 7 | 35% | 12% | +23 | 4 |
| Haywire Mite | 1 | 40 | 80% | 6.0 | 35% | 14% | +21 | 5 |
| Poison-Tip Archer | 4 | 41 | 85% | 9 | 34% | 14% | +20 | 3 |
| Nadier's Nightblade | 3 | 58 | 90% | 8.0 | 33% | 12% | +21 | 7 |
| Moldervine Reclamation | 5 | 38 | 55% | 10 | 32% | 15% | +17 | 11 |
| Beastmaster Ascension | 3 | 49 | 90% | 7.0 | 31% | 14% | +17 | 2 |
| Idol of Oblivion | 2 | 57 | 96% | 7 | 30% | 13% | +16 | 1 |
| Honored Dreyleader | 3 | 50 | 82% | 9 | 28% | 15% | +13 | 9 |
| Beledros Witherbloom | 7 | 47 | 66% | 9 | 28% | 15% | +13 | 9 |
| Nested Shambler | 1 | 55 | 96% | 5 | 27% | 14% | +13 | 4 |
| Ogre Slumlord | 5 | 45 | 64% | 9 | 27% | 16% | +11 | 14 |
| Woe Strider | 3 | 53 | 66% | 9 | 26% | 15% | +11 | 12 |
| Maelstrom Pulse | 3 | 60 | 0% |  | 25% | 15% | +10 | 42 |
| Ravenous Squirrel | 1 | 52 | 88% | 6.5 | 25% | 16% | +10 | 7 |
| Shamanic Revelation | 5 | 44 | 27% | 11.0 | 25% | 16% | +9 | 23 |
| Swarmyard Massacre | 5 | 32 | 84% | 8 | 25% | 17% | +8 | 5 |
| Saw in Half | 3 | 57 | 96% | 5 | 25% | 15% | +9 | 0 |
| Golgari Signet | 2 | 49 | 98% | 5.5 | 24% | 16% | +9 | 1 |
| Rootcast Apprenticeship | 4 | 49 | 53% | 9.0 | 24% | 16% | +9 | 15 |
| Windgrace's Judgment | 5 | 54 | 93% | 7.0 | 24% | 16% | +8 | 5 |
| Morbid Opportunist | 3 | 46 | 76% | 9 | 24% | 16% | +8 | 11 |
| Talisman of Resilience | 2 | 59 | 100% | 5 | 24% | 16% | +8 | 1 |
| Sol Ring | 1 | 60 | 98% | 7 | 23% | 16% | +8 | 1 |
| Chitterspitter | 3 | 52 | 92% | 8.0 | 23% | 16% | +7 | 4 |
| Cache Grab | 2 | 48 | 83% | 9.0 | 23% | 16% | +6 | 7 |
| Deadly Dispute | 2 | 48 | 90% | 7 | 23% | 16% | +6 | 2 |
| Tireless Provisioner | 3 | 44 | 89% | 9 | 23% | 17% | +6 | 4 |
| Insatiable Frugivore | 4 | 49 | 61% | 9.0 | 22% | 17% | +6 | 20 |
| Gourmand's Talent | 1 | 63 | 97% | 6 | 22% | 16% | +6 | 1 |
| Sword of the Squeak | 2 | 50 | 84% | 8.5 | 22% | 17% | +5 | 5 |
| Chittering Witch | 4 | 46 | 67% | 10 | 22% | 17% | +5 | 14 |
| Plumb the Forbidden | 2 | 46 | 98% | 4 | 22% | 17% | +5 | 1 |
| Chatterfang, Squirrel General | 3 | 51 | 88% | 7 | 22% | 17% | +5 | 5 |
| Gilded Goose | 1 | 56 | 95% | 6 | 21% | 17% | +5 | 5 |
| Arasta of the Endless Web | 4 | 52 | 73% | 8.0 | 21% | 17% | +4 | 11 |
| Putrefy | 3 | 52 | 98% | 6 | 21% | 17% | +4 | 2 |
| Maskwood Nexus | 4 | 48 | 48% | 10 | 21% | 17% | +4 | 20 |
| Binding the Old Gods | 4 | 39 | 90% | 7 | 20% | 17% | +3 | 5 |
| Skullclamp | 1 | 49 | 98% | 7.0 | 20% | 17% | +3 | 4 |
| Toski, Bearer of Secrets | 4 | 54 | 87% | 7 | 20% | 17% | +3 | 6 |
| Squirrel Nest | 3 | 40 | 75% | 9.0 | 20% | 18% | +3 | 6 |
| The Odd Acorn Gang | 5 | 45 | 84% | 8.0 | 20% | 17% | +3 | 9 |
| Academy Manufactor | 3 | 46 | 91% | 7.0 | 20% | 18% | +2 | 4 |
| Moonstone Eulogist | 5 | 51 | 67% | 10.0 | 20% | 17% | +2 | 14 |
| Tear Asunder | 2 | 56 | 96% | 6.0 | 20% | 17% | +2 | 2 |
| Arcane Signet | 2 | 57 | 98% | 7.0 | 19% | 18% | +2 | 3 |
| Wolfwillow Haven | 2 | 47 | 72% | 6.5 | 19% | 18% | +2 | 11 |
| Scurry of Squirrels | 3 | 48 | 77% | 9 | 19% | 18% | +1 | 12 |
| Skyfisher Spider | 4 | 49 | 88% | 7 | 18% | 18% | +1 | 1 |
| Plaguecrafter | 3 | 44 | 41% | 9.0 | 18% | 18% | +0 | 20 |
| Second Harvest | 4 | 59 | 90% | 9 | 17% | 18% | -1 | 10 |
| End-Raze Forerunners | 8 | 54 | 44% | 11.0 | 17% | 18% | -2 | 24 |
| Casualties of War | 6 | 55 | 73% | 8.0 | 16% | 19% | -2 | 9 |
| Prosperous Innkeeper | 2 | 70 | 91% | 7.0 | 16% | 19% | -4 | 2 |
| Deep Forest Hermit | 5 | 58 | 88% | 9 | 16% | 19% | -4 | 9 |
| Chatterstorm | 2 | 42 | 71% | 8.5 | 14% | 19% | -5 | 13 |
| Squirrel Sovereign | 2 | 52 | 98% | 6 | 14% | 20% | -6 | 2 |
| Decree of Pain | 8 | 39 | 36% | 10.0 | 13% | 19% | -6 | 14 |
| Hazel's Brewmaster | 4 | 56 | 79% | 10.0 | 11% | 21% | -10 | 16 |
| Garruk, Cursed Huntsman | 6 | 38 | 90% | 9.0 | 10% | 20% | -9 | 5 |
