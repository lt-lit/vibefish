# Playtest: miracle-worker

- List: `Miracle Worker [DSC] [2024].dck`
- Pilot: playbook `miracle-worker.json` version 3, Forge's attack (arm `playbook`). Commander: Aminatou, Veil Piercer
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**52 wins in 200 tables: 26.0%** (95% 20% to 32%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 12 of 50, 14 of 50, 15 of 50, 11 of 50.
Games ran 47.9 turns in all. It won on its own turn 14.3 on average. When it lost it was out by its own turn 11.4.
Of its 144 losses it was the first player out in 42, the second in 61, the last opponent standing in 41. What took it out: LifeReachedZero 143, IntentionalDraw 2, CommanderDamage 1.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| deadly-disguise | 65 | 21 (32%) | 2 (3%) | 5 |
| veloci-ramp-tor | 62 | 18 (29%) | 20 (32%) | 20 |
| squirreled-away | 75 | 20 (27%) | 11 (15%) | 5 |
| death-toll | 61 | 16 (26%) | 18 (30%) | 13 |
| blood-rites | 65 | 17 (26%) | 24 (37%) | 15 |
| ahoy-mateys | 62 | 16 (26%) | 16 (26%) | 15 |
| blight-curse | 76 | 18 (24%) | 23 (30%) | 13 |
| mutant-menace | 68 | 16 (24%) | 13 (19%) | 12 |
| revenant-recon | 66 | 14 (21%) | 17 (26%) | 16 |

## Tempo

- A mulligan in 26% of games. Lands at the start of its own turns 4, 6, 8: 2.74, 4.38, 5.79; cards in hand: 6.05, 5.56, 4.5. Short of four lands at the start of turn 5 in 38% of games.
- Commander first cast on its own turn 4 (median; quartiles 4 to 5), never cast in 2% of games, 2.2 casts a game.
- 16.9 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 7%.
- Damage dealt 33.2 a game (3.1 of it by the commander), taken 31.1.
- When it lost it held 3.12 nonland cards, 2.56 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (62 cards); the deck won 26.0% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Mind Flayer, the Shadow | 7 | 42 | 0% |  | 29% | 25% | +3 | 19 |
| Inkshield | 5 | 58 | 31% | 12.0 | 45% | 18% | +26 | 23 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Sphere of Safety | 5 | 45 | 71% | 10.5 | 51% | 19% | +32 | 7 |
| Inkshield | 5 | 58 | 31% | 12.0 | 45% | 18% | +26 | 23 |
| Shark Typhoon | 6 | 58 | 52% | 10.5 | 41% | 20% | +22 | 10 |
| Metamorphosis Fanatic | 6 | 51 | 65% | 10 | 41% | 21% | +20 | 14 |
| Brainstorm | 1 | 57 | 95% | 7.0 | 40% | 20% | +20 | 0 |
| One with the Multiverse | 8 | 57 | 54% | 10 | 40% | 20% | +20 | 12 |
| Monologue Tax | 3 | 50 | 82% | 7 | 40% | 21% | +19 | 3 |
| Aminatou's Augury | 8 | 48 | 81% | 10 | 40% | 22% | +18 | 9 |
| Extravagant Replication | 6 | 56 | 71% | 10.0 | 39% | 21% | +19 | 8 |
| Life Insurance | 5 | 51 | 55% | 10.5 | 39% | 22% | +18 | 15 |
| Otherworldly Gaze | 1 | 42 | 83% | 6 | 38% | 23% | +15 | 3 |
| Timely Ward | 3 | 51 | 86% | 8.0 | 37% | 22% | +15 | 2 |
| Diabolic Vision | 2 | 44 | 84% | 10 | 36% | 23% | +13 | 6 |
| Azorius Signet | 2 | 47 | 98% | 6.0 | 36% | 23% | +13 | 0 |
| Redress Fate | 8 | 61 | 57% | 11 | 36% | 22% | +14 | 18 |
| Thirst for Meaning | 3 | 50 | 78% | 9 | 36% | 23% | +13 | 9 |
| Moon-Blessed Cleric | 3 | 40 | 92% | 8 | 35% | 24% | +11 | 3 |
| Arcane Denial | 2 | 43 | 77% | 8 | 35% | 24% | +11 | 7 |
| Burnished Hart | 3 | 44 | 93% | 7 | 34% | 24% | +10 | 2 |
| Fear of Sleep Paralysis | 6 | 53 | 77% | 10 | 34% | 23% | +11 | 11 |
| Orzhov Signet | 2 | 64 | 100% | 6.0 | 33% | 23% | +10 | 0 |
| Demon of Fate's Design | 6 | 55 | 74% | 9 | 33% | 23% | +9 | 9 |
| Arcane Signet | 2 | 46 | 100% | 5.0 | 33% | 24% | +9 | 0 |
| Archetype of Imagination | 6 | 43 | 56% | 11.0 | 33% | 24% | +8 | 14 |
| Prognostic Sphinx | 5 | 46 | 72% | 11 | 33% | 24% | +9 | 9 |
| Terminus | 6 | 46 | 76% | 8 | 33% | 24% | +9 | 7 |
| Secret Arcade // Dusty Parlor | 8 | 84 | 93% | 7.5 | 32% | 22% | +11 | 2 |
| Mirrormade | 3 | 47 | 66% | 9 | 32% | 24% | +8 | 9 |
| Athreos, Shroud-Veiled | 6 | 66 | 74% | 10 | 32% | 23% | +9 | 14 |
| Doomwake Giant | 5 | 65 | 65% | 8.0 | 31% | 24% | +7 | 17 |
| Soaring Lightbringer | 5 | 49 | 92% | 8 | 31% | 24% | +6 | 6 |
| Mind Stone | 2 | 53 | 100% | 5 | 30% | 24% | +6 | 3 |
| Brainstone | 1 | 50 | 92% | 5.5 | 30% | 25% | +5 | 2 |
| Commander's Sphere | 3 | 60 | 97% | 6.5 | 30% | 24% | +6 | 5 |
| Sigil of the Empty Throne | 5 | 54 | 85% | 8.0 | 30% | 25% | +5 | 6 |
| Bottomless Pool // Locker Room | 6 | 51 | 98% | 8.0 | 29% | 25% | +5 | 1 |
| Entreat the Angels | 3 | 51 | 86% | 10.0 | 29% | 25% | +5 | 11 |
| Utter End | 4 | 51 | 88% | 8 | 29% | 25% | +5 | 5 |
| Verge Rangers | 3 | 48 | 83% | 7.0 | 29% | 25% | +4 | 13 |
| Auramancer | 3 | 45 | 80% | 8.5 | 29% | 25% | +4 | 7 |
| Portent | 1 | 45 | 98% | 8.0 | 29% | 25% | +4 | 3 |
| Mind Flayer, the Shadow | 7 | 42 | 0% |  | 29% | 25% | +3 | 19 |
| Time Wipe | 5 | 39 | 80% | 9 | 28% | 26% | +3 | 5 |
| Telling Time | 2 | 65 | 72% | 8 | 28% | 25% | +3 | 11 |
| Spirit-Sister's Call | 5 | 58 | 62% | 11.0 | 28% | 25% | +2 | 15 |
| Ancient Cellarspawn | 3 | 53 | 87% | 8.0 | 26% | 26% | +1 | 6 |
| Starfield Mystic | 2 | 39 | 95% | 6 | 26% | 26% | -1 | 2 |
| Swords to Plowshares | 1 | 55 | 98% | 5.0 | 26% | 26% | -1 | 0 |
| Cramped Vents // Access Maze | 11 | 56 | 82% | 9.0 | 25% | 26% | -1 | 9 |
| Read the Bones | 3 | 56 | 88% | 8 | 25% | 26% | -1 | 9 |
| Ondu Spiritdancer | 5 | 49 | 92% | 8 | 24% | 26% | -2 | 6 |
| Cast Out | 4 | 61 | 92% | 6.0 | 23% | 27% | -4 | 2 |
| Nightmare Shepherd | 4 | 49 | 82% | 9.0 | 22% | 27% | -5 | 7 |
| Phenomenon Investigators | 4 | 49 | 80% | 9 | 22% | 27% | -5 | 5 |
| Solemn Simulacrum | 4 | 55 | 69% | 8.0 | 22% | 28% | -6 | 10 |
| The Eldest Reborn | 5 | 46 | 87% | 8.5 | 22% | 27% | -6 | 6 |
| Ponder | 1 | 42 | 90% | 6.5 | 21% | 27% | -6 | 7 |
| Sol Ring | 1 | 42 | 100% | 6.0 | 21% | 27% | -6 | 1 |
| The Master of Keys | 3 | 45 | 71% | 9.0 | 20% | 28% | -8 | 9 |
| Dream Eater | 6 | 36 | 86% | 8 | 19% | 27% | -8 | 3 |
| Mesa Enchantress | 3 | 53 | 96% | 7 | 19% | 29% | -10 | 4 |
| Return to Dust | 4 | 54 | 82% | 8.0 | 18% | 29% | -10 | 9 |
