# Playtest: revenant-recon

- List: `Revenant Recon [MKC] [2024].dck`
- Pilot: playbook `revenant-recon.json` version 4, Forge's attack (arm `playbook`). Commander: Mirko, Obsessive Theorist
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**48 wins in 200 tables: 24.0%** (95% 19% to 30%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 15 of 50, 8 of 50, 12 of 50, 13 of 50.
Games ran 46.5 turns in all. It won on its own turn 13.3 on average. When it lost it was out by its own turn 11.3.
Of its 148 losses it was the first player out in 38, the second in 64, the last opponent standing in 46. What took it out: LifeReachedZero 148, CommanderDamage 1.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| deadly-disguise | 65 | 21 (32%) | 8 (12%) | 6 |
| squirreled-away | 75 | 20 (27%) | 10 (13%) | 9 |
| veloci-ramp-tor | 62 | 16 (26%) | 23 (37%) | 21 |
| ahoy-mateys | 62 | 15 (24%) | 21 (34%) | 21 |
| blood-rites | 65 | 15 (23%) | 22 (34%) | 20 |
| blight-curse | 76 | 17 (22%) | 22 (29%) | 10 |
| mutant-menace | 66 | 14 (21%) | 15 (23%) | 11 |
| miracle-worker | 68 | 14 (21%) | 7 (10%) | 6 |
| death-toll | 61 | 12 (20%) | 20 (33%) | 14 |

## Tempo

- A mulligan in 42% of games. Lands at the start of its own turns 4, 6, 8: 2.85, 4.34, 5.7; cards in hand: 5.71, 4.57, 3.87. Short of four lands at the start of turn 5 in 30% of games.
- Commander first cast on its own turn 3 (median; quartiles 3 to 4), never cast in 2% of games, 2.67 casts a game.
- 16.9 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 5%.
- Damage dealt 36.5 a game (11.4 of it by the commander), taken 34.1.
- When it lost it held 3.36 nonland cards, 2.94 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (62 cards); the deck won 24.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Toxic Deluge | 3 | 44 | 0% |  | 30% | 22% | +7 | 27 |
| Counterpoint | 5 | 53 | 28% | 10 | 32% | 21% | +11 | 25 |
| Charnel Serenade | 6 | 58 | 40% | 11 | 41% | 17% | +24 | 10 |
| Foreboding Steamboat | 5 | 59 | 42% | 10 | 20% | 26% | -5 | 23 |
| Watcher of Hours | 6 | 43 | 46% | 11.0 | 35% | 21% | +14 | 2 |
| Phyrexian Metamorph | 4 | 53 | 49% | 8.0 | 19% | 26% | -7 | 19 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Massacre Wurm | 6 | 43 | 84% | 9.0 | 42% | 19% | +23 | 4 |
| Charnel Serenade | 6 | 58 | 40% | 11 | 41% | 17% | +24 | 10 |
| Sphinx of the Second Sun | 8 | 45 | 64% | 10 | 40% | 19% | +21 | 9 |
| Rise of the Dark Realms | 9 | 49 | 51% | 12 | 39% | 19% | +20 | 15 |
| Black Sun's Zenith | 2 | 50 | 50% | 10 | 38% | 19% | +19 | 11 |
| Consider | 1 | 51 | 94% | 7.0 | 37% | 20% | +18 | 6 |
| Syr Konrad, the Grim | 5 | 51 | 74% | 9.0 | 37% | 20% | +18 | 9 |
| Ransom Note | 1 | 57 | 91% | 5.0 | 37% | 19% | +18 | 1 |
| Deep Analysis | 4 | 65 | 51% | 10 | 35% | 18% | +17 | 20 |
| Sol Ring | 1 | 60 | 97% | 6.5 | 35% | 19% | +16 | 1 |
| Watcher of Hours | 6 | 43 | 46% | 11.0 | 35% | 21% | +14 | 2 |
| Case of the Shifting Visage | 3 | 49 | 94% | 6.5 | 35% | 20% | +14 | 3 |
| Dream Eater | 6 | 47 | 72% | 10.0 | 34% | 21% | +13 | 9 |
| Curate | 2 | 59 | 92% | 8.0 | 34% | 20% | +14 | 9 |
| Dimir Signet | 2 | 51 | 98% | 7.0 | 33% | 21% | +13 | 2 |
| Master of Death | 3 | 61 | 88% | 7.0 | 33% | 20% | +13 | 15 |
| Counterpoint | 5 | 53 | 28% | 10 | 32% | 21% | +11 | 25 |
| Disinformation Campaign | 3 | 50 | 70% | 9 | 32% | 21% | +11 | 18 |
| Mulldrifter | 5 | 41 | 71% | 8 | 32% | 22% | +10 | 7 |
| Enhanced Surveillance | 2 | 54 | 91% | 8 | 32% | 21% | +10 | 1 |
| Overseer of the Damned | 7 | 54 | 80% | 11 | 32% | 21% | +10 | 11 |
| Vizier of Many Faces | 4 | 35 | 51% | 8.0 | 31% | 22% | +9 | 12 |
| Discovery // Dispersal | 7 | 48 | 96% | 8.0 | 31% | 22% | +10 | 0 |
| Connive // Concoct | 9 | 55 | 80% | 8.0 | 31% | 21% | +10 | 8 |
| Unshakable Tail | 3 | 49 | 82% | 8.0 | 31% | 22% | +9 | 10 |
| Phyrexian Arena | 3 | 53 | 91% | 8.0 | 30% | 22% | +8 | 5 |
| Animate Dead | 2 | 57 | 88% | 7.5 | 30% | 22% | +8 | 7 |
| Talisman of Dominance | 2 | 57 | 100% | 8 | 30% | 22% | +8 | 2 |
| Arcane Signet | 2 | 61 | 97% | 6 | 30% | 22% | +8 | 1 |
| Toxic Deluge | 3 | 44 | 0% |  | 30% | 22% | +7 | 27 |
| Brainstorm | 1 | 51 | 86% | 7.0 | 29% | 22% | +7 | 3 |
| Mind Stone | 2 | 58 | 100% | 4.0 | 29% | 22% | +7 | 1 |
| Grave Titan | 6 | 48 | 81% | 8 | 29% | 22% | +7 | 7 |
| Mission Briefing | 2 | 62 | 94% | 8.0 | 29% | 22% | +7 | 3 |
| Eye of Duskmantle | 7 | 45 | 67% | 9.5 | 29% | 23% | +6 | 5 |
| Pile On | 4 | 59 | 97% | 7 | 29% | 22% | +7 | 1 |
| Sinister Starfish | 2 | 52 | 100% | 6.0 | 29% | 22% | +6 | 2 |
| Lazav, the Multifarious | 2 | 46 | 87% | 7.0 | 28% | 23% | +6 | 7 |
| Thought Vessel | 2 | 60 | 97% | 7.0 | 28% | 22% | +6 | 0 |
| Ephara's Dispersal | 3 | 64 | 91% | 6.0 | 28% | 22% | +6 | 2 |
| Dogged Detective | 2 | 58 | 88% | 8 | 28% | 22% | +5 | 19 |
| Notion Rain | 3 | 55 | 67% | 10 | 27% | 23% | +5 | 15 |
| Reanimate | 1 | 55 | 93% | 7 | 27% | 23% | +5 | 5 |
| Baleful Strix | 2 | 48 | 83% | 7.0 | 27% | 23% | +4 | 8 |
| Price of Fame | 4 | 57 | 96% | 6 | 26% | 23% | +3 | 2 |
| Twilight Prophet | 4 | 47 | 68% | 9.0 | 26% | 24% | +2 | 14 |
| Everflowing Chalice | 0 | 54 | 68% | 9 | 24% | 24% | +0 | 10 |
| Ravenous Chupacabra | 4 | 50 | 90% | 7 | 24% | 24% | +0 | 6 |
| Dimir Spybug | 2 | 47 | 98% | 6.5 | 23% | 24% | -1 | 0 |
| Final-Word Phantom | 3 | 43 | 84% | 7.0 | 23% | 24% | -1 | 6 |
| Whispering Snitch | 2 | 48 | 96% | 4.0 | 23% | 24% | -1 | 2 |
| Thoughtbound Phantasm | 1 | 49 | 92% | 4 | 22% | 24% | -2 | 4 |
| Nightveil Sprite | 2 | 50 | 88% | 6.5 | 22% | 25% | -3 | 7 |
| Copy Catchers | 2 | 52 | 85% | 5.5 | 21% | 25% | -4 | 4 |
| Marvo, Deep Operative | 5 | 52 | 69% | 10.0 | 21% | 25% | -4 | 15 |
| Otherworldly Gaze | 1 | 67 | 81% | 5.0 | 21% | 26% | -5 | 8 |
| Amphin Mutineer | 4 | 48 | 85% | 8 | 21% | 25% | -4 | 7 |
| Foreboding Steamboat | 5 | 59 | 42% | 10 | 20% | 26% | -5 | 23 |
| Doom Whisperer | 5 | 40 | 85% | 11.0 | 20% | 25% | -5 | 10 |
| Necromancy | 3 | 53 | 70% | 8 | 19% | 26% | -7 | 16 |
| Phyrexian Metamorph | 4 | 53 | 49% | 8.0 | 19% | 26% | -7 | 19 |
| Shriekmaw | 5 | 44 | 80% | 6 | 18% | 26% | -7 | 6 |
