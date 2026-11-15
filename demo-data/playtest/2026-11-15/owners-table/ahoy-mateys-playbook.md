# Playtest: ahoy-mateys

- List: `Ahoy Mateys [LCC] [2023].dck`
- Pilot: playbook `ahoy-mateys.json` version 2, go_wide attack (arm `playbook`). Commander: Admiral Brass, Unsinkable
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**65 wins in 200 tables: 32.5%** (95% 26% to 39%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 14 of 50, 20 of 50, 17 of 50, 14 of 50.
Games ran 41.5 turns in all. It won on its own turn 11.0 on average. When it lost it was out by its own turn 9.7.
Of its 131 losses it was the first player out in 69, the second in 42, the last opponent standing in 20. What took it out: LifeReachedZero 131, CommanderDamage 1.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| miracle-worker | 61 | 25 (41%) | 6 (10%) | 11 |
| revenant-recon | 66 | 26 (39%) | 8 (12%) | 5 |
| deadly-disguise | 65 | 23 (35%) | 10 (15%) | 7 |
| blood-rites | 76 | 26 (34%) | 25 (33%) | 12 |
| blight-curse | 62 | 20 (32%) | 16 (26%) | 9 |
| mutant-menace | 68 | 21 (31%) | 10 (15%) | 16 |
| death-toll | 65 | 20 (31%) | 18 (28%) | 13 |
| squirreled-away | 75 | 23 (31%) | 19 (25%) | 12 |
| veloci-ramp-tor | 62 | 11 (18%) | 19 (31%) | 14 |

## Tempo

- A mulligan in 26% of games. Lands at the start of its own turns 4, 6, 8: 2.99, 4.56, 5.94; cards in hand: 5.21, 4.4, 3.84. Short of four lands at the start of turn 5 in 20% of games.
- Commander first cast on its own turn 5.0 (median; quartiles 5 to 6), never cast in 1% of games, 2.02 casts a game.
- 13.6 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 4%.
- Damage dealt 67.3 a game (8.5 of it by the commander), taken 27.9.
- When it lost it held 3.11 nonland cards, 2.95 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (62 cards); the deck won 32.5% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Rakdos Charm | 2 | 41 | 37% | 6 | 42% | 30% | +11 | 12 |
| Zara, Renegade Recruiter | 5 | 37 | 43% | 9.0 | 32% | 32% | -0 | 19 |
| Dire Fleet Ravager | 5 | 45 | 49% | 9.0 | 31% | 33% | -2 | 18 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Evacuation | 5 | 41 | 61% | 10 | 49% | 28% | +20 | 2 |
| Corsair Captain | 3 | 44 | 93% | 7 | 48% | 28% | +20 | 3 |
| Azure Fleet Admiral | 4 | 45 | 60% | 9 | 47% | 28% | +18 | 11 |
| Sol Ring | 1 | 45 | 98% | 5.0 | 47% | 28% | +18 | 0 |
| Angrath's Marauders | 7 | 36 | 53% | 8 | 44% | 30% | +15 | 7 |
| Don Andres, the Renegade | 4 | 50 | 58% | 8 | 44% | 29% | +15 | 15 |
| Admiral Beckett Brass | 4 | 49 | 90% | 7.0 | 43% | 29% | +14 | 1 |
| King Narfi's Betrayal | 3 | 35 | 54% | 7 | 43% | 30% | +13 | 7 |
| Hostage Taker | 4 | 47 | 89% | 7.0 | 43% | 29% | +13 | 5 |
| Timestream Navigator | 2 | 48 | 81% | 6 | 42% | 30% | +12 | 7 |
| Ghost of Ramirez DePietro | 3 | 41 | 61% | 8 | 42% | 30% | +11 | 9 |
| Rakdos Charm | 2 | 41 | 37% | 6 | 42% | 30% | +11 | 12 |
| Feed the Swarm | 2 | 46 | 87% | 7.0 | 41% | 30% | +11 | 2 |
| The Grim Captain's Locker | 4 | 49 | 65% | 9.0 | 41% | 30% | +11 | 12 |
| Coercive Recruiter | 5 | 52 | 81% | 7.0 | 40% | 30% | +11 | 9 |
| Faithless Looting | 1 | 38 | 76% | 7 | 40% | 31% | +9 | 3 |
| Distant Melody | 4 | 41 | 58% | 7.0 | 39% | 31% | +8 | 12 |
| Chaos Warp | 3 | 44 | 91% | 6.0 | 39% | 31% | +8 | 4 |
| Dire Fleet Daredevil | 2 | 44 | 77% | 6.0 | 39% | 31% | +8 | 8 |
| Windfall | 3 | 50 | 52% | 8.0 | 38% | 31% | +7 | 18 |
| Amphin Mutineer | 4 | 48 | 79% | 8.0 | 38% | 31% | +7 | 4 |
| Prismari Command | 3 | 48 | 88% | 7.0 | 38% | 31% | +7 | 4 |
| Ramirez DePietro, Pillager | 4 | 57 | 88% | 7.0 | 37% | 31% | +6 | 7 |
| Francisco, Fowl Marauder | 2 | 60 | 87% | 5.0 | 37% | 31% | +6 | 6 |
| Port Razer | 5 | 49 | 82% | 9.0 | 37% | 31% | +6 | 8 |
| Herald's Horn | 3 | 44 | 89% | 6 | 36% | 31% | +5 | 2 |
| Merchant Raiders | 4 | 47 | 79% | 8 | 36% | 31% | +5 | 8 |
| Wayfarer's Bauble | 1 | 36 | 92% | 6 | 36% | 32% | +4 | 6 |
| Blood Money | 7 | 42 | 60% | 9 | 36% | 32% | +4 | 8 |
| Gemcutter Buccaneer | 4 | 45 | 89% | 8.0 | 36% | 32% | +4 | 7 |
| Dimir Signet | 2 | 37 | 100% | 6 | 35% | 32% | +3 | 0 |
| Fathom Fleet Captain | 2 | 43 | 95% | 7 | 35% | 32% | +3 | 3 |
| Pitiless Plunderer | 4 | 43 | 56% | 9.0 | 35% | 32% | +3 | 15 |
| Skeleton Crew | 4 | 55 | 86% | 7 | 34% | 32% | +3 | 1 |
| Broadside Bombardiers | 3 | 41 | 83% | 7.0 | 34% | 32% | +2 | 4 |
| Icon of Ancestry | 3 | 44 | 93% | 6 | 34% | 32% | +2 | 0 |
| Captivating Crew | 4 | 50 | 58% | 8 | 34% | 32% | +2 | 9 |
| Lethal Scheme | 4 | 47 | 98% | 7.0 | 34% | 32% | +2 | 2 |
| Storm Fleet Negotiator | 3 | 53 | 70% | 8 | 34% | 32% | +2 | 10 |
| Bident of Thassa | 4 | 39 | 62% | 7.0 | 33% | 32% | +1 | 9 |
| Blasphemous Act | 9 | 36 | 67% | 8.0 | 33% | 32% | +1 | 6 |
| Shared Animosity | 3 | 39 | 87% | 6.5 | 33% | 32% | +1 | 4 |
| Zara, Renegade Recruiter | 5 | 37 | 43% | 9.0 | 32% | 32% | -0 | 19 |
| Enterprising Scallywag | 2 | 47 | 70% | 6 | 32% | 33% | -1 | 9 |
| Departed Deckhand | 2 | 41 | 80% | 7 | 32% | 33% | -1 | 5 |
| Dire Fleet Ravager | 5 | 45 | 49% | 9.0 | 31% | 33% | -2 | 18 |
| Malcolm, Keen-Eyed Navigator | 3 | 45 | 89% | 5.5 | 31% | 33% | -2 | 2 |
| Izzet Signet | 2 | 52 | 100% | 5.0 | 31% | 33% | -2 | 3 |
| The Indomitable | 4 | 49 | 61% | 8.0 | 31% | 33% | -3 | 16 |
| Rakdos Signet | 2 | 46 | 98% | 5 | 30% | 33% | -3 | 2 |
| Kari Zev, Skyship Raider | 2 | 53 | 91% | 4.0 | 30% | 33% | -3 | 7 |
| Vanquisher's Banner | 5 | 44 | 84% | 7 | 30% | 33% | -4 | 8 |
| Warkite Marauder | 2 | 39 | 77% | 7.0 | 28% | 34% | -5 | 7 |
| Spectral Sailor | 1 | 50 | 88% | 5.0 | 28% | 34% | -6 | 4 |
| Siren Stormtamer | 1 | 47 | 98% | 6.0 | 28% | 34% | -6 | 1 |
| Arm-Mounted Anchor | 3 | 42 | 88% | 6 | 26% | 34% | -8 | 4 |
| Arcane Signet | 2 | 56 | 95% | 4 | 25% | 35% | -10 | 0 |
| Daring Saboteur | 2 | 45 | 89% | 5.5 | 24% | 35% | -10 | 5 |
| Commander's Sphere | 3 | 38 | 90% | 5.0 | 24% | 35% | -11 | 3 |
| Black Market Connections | 3 | 55 | 84% | 6.5 | 24% | 36% | -12 | 8 |
| Breeches, Brazen Plunderer | 4 | 47 | 87% | 7 | 23% | 35% | -12 | 7 |
| Captain Lannery Storm | 3 | 52 | 81% | 6.5 | 19% | 37% | -18 | 10 |
