# Playtest: blood-rites

- List: `Blood Rites [LCC] [2023].dck`
- Pilot: playbook `blood-rites.json` version 2, Forge's attack (arm `playbook`). Commander: Clavileño, First of the Blessed
- Table: 4 players, opponents drawn from `owners-table-v1`; 600 opponent seats under their playbook, 0 under stock Forge AI; seed 20261350, snapshot-2026-11-10

## Result

**75 wins in 200 tables: 37.5%** (95% 31% to 44%); an even share is 25%. 4 games were not finished (turn cap or clock).

By seat (first to act is seat 1): 17 of 50, 19 of 50, 18 of 50, 21 of 50.
Games ran 45.2 turns in all. It won on its own turn 13.0 on average. When it lost it was out by its own turn 10.4.
Of its 121 losses it was the first player out in 52, the second in 29, the last opponent standing in 40. What took it out: LifeReachedZero 114, CommanderDamage 8.

## Opponents

| Opponent | Tables | This deck won | The opponent won | Took this deck out |
|---|---|---|---|---|
| deadly-disguise | 65 | 34 (52%) | 0 (0%) | 3 |
| squirreled-away | 75 | 34 (45%) | 5 (7%) | 5 |
| death-toll | 65 | 27 (42%) | 13 (20%) | 14 |
| blight-curse | 76 | 30 (40%) | 13 (17%) | 12 |
| ahoy-mateys | 62 | 23 (37%) | 18 (29%) | 20 |
| revenant-recon | 66 | 22 (33%) | 20 (30%) | 14 |
| mutant-menace | 68 | 22 (32%) | 16 (24%) | 18 |
| veloci-ramp-tor | 62 | 18 (29%) | 22 (36%) | 15 |
| miracle-worker | 61 | 15 (25%) | 14 (23%) | 9 |

## Tempo

- A mulligan in 22% of games. Lands at the start of its own turns 4, 6, 8: 2.98, 4.66, 6.13; cards in hand: 5.74, 4.48, 3.87. Short of four lands at the start of turn 5 in 21% of games.
- Commander first cast on its own turn 3.0 (median; quartiles 3 to 4), never cast in 0% of games, 2.62 casts a game.
- 14.9 spells a game. Idle turns (from its third turn on, no spell cast with an affordable card in hand): 5%.
- Damage dealt 44.6 a game (5.4 of it by the commander), taken 43.1.
- When it lost it held 3.01 nonland cards, 2.8 of them affordable with its lands.

## Cards

Nonland cards drawn in at least 20 games (62 cards); the deck won 37.5% of all games. The win-rate columns are noisy (see the tool's notes): look at them, do not believe them.

### Drawn and mostly not cast

Cast in under half of the games they were drawn. That is the pilot as much as the list: Forge's AI never casts some cards at all (`controller/vibefish-sim.sh check` lists a deck's AI-flagged cards), holds reactive cards for a moment that may not come, and a playbook casts what its rules name. A card that people would cast and the pilot does not is a gap in the pilot.

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Pact of the Serpent | 3 | 47 | 0% |  | 47% | 35% | +12 | 20 |
| New Blood | 4 | 40 | 0% |  | 50% | 34% | +16 | 16 |
| March of the Canonized | 2 | 50 | 46% | 10 | 46% | 35% | +11 | 16 |

### Every card, by win rate when drawn

| Card | MV | Games drawn | Cast when drawn | Turn of first cast | Won when drawn | Won when not | Points | In hand at a loss |
|---|---|---|---|---|---|---|---|---|
| Exquisite Blood | 5 | 39 | 95% | 7 | 64% | 31% | +33 | 1 |
| Cruel Celebrant | 2 | 47 | 83% | 6 | 53% | 33% | +20 | 3 |
| Radiant Destiny | 3 | 46 | 100% | 7.0 | 52% | 33% | +19 | 1 |
| Patron of the Vein | 6 | 48 | 90% | 8 | 52% | 33% | +19 | 2 |
| Bloodline Necromancer | 5 | 47 | 60% | 9.0 | 51% | 33% | +18 | 12 |
| Falkenrath Noble | 4 | 55 | 80% | 9.5 | 51% | 32% | +18 | 10 |
| Etchings of the Chosen | 3 | 42 | 98% | 8 | 50% | 34% | +16 | 2 |
| New Blood | 4 | 40 | 0% |  | 50% | 34% | +16 | 16 |
| Promise of Aclazotz | 2 | 42 | 98% | 8 | 50% | 34% | +16 | 0 |
| Charismatic Conqueror | 2 | 59 | 93% | 6 | 49% | 33% | +17 | 6 |
| Cordial Vampire | 2 | 51 | 98% | 6.5 | 49% | 34% | +15 | 2 |
| Nighthawk Scavenger | 3 | 49 | 82% | 9.0 | 49% | 34% | +15 | 7 |
| Dusk Legion Sergeant | 2 | 43 | 91% | 6 | 49% | 34% | +14 | 4 |
| Carmen, Cruel Skymarcher | 5 | 35 | 74% | 9.0 | 49% | 35% | +13 | 7 |
| Sanctum Seeker | 4 | 42 | 90% | 8.0 | 48% | 35% | +13 | 4 |
| Elenda, the Dusk Rose | 4 | 40 | 88% | 7 | 48% | 35% | +12 | 6 |
| Timothar, Baron of Bats | 6 | 53 | 79% | 8.5 | 47% | 34% | +13 | 6 |
| Drana, Liberator of Malakir | 3 | 47 | 94% | 7.0 | 47% | 35% | +12 | 4 |
| Pact of the Serpent | 3 | 47 | 0% |  | 47% | 35% | +12 | 20 |
| Talisman of Hierarchy | 2 | 47 | 100% | 6 | 47% | 35% | +12 | 0 |
| Blade of the Bloodchief | 1 | 58 | 95% | 7 | 47% | 34% | +13 | 1 |
| Bartolomé del Presidio | 2 | 56 | 89% | 8.0 | 46% | 34% | +12 | 9 |
| March of the Canonized | 2 | 50 | 46% | 10 | 46% | 35% | +11 | 16 |
| Kindred Boon | 4 | 46 | 87% | 8.0 | 46% | 35% | +11 | 9 |
| Mind Stone | 2 | 35 | 100% | 4 | 46% | 36% | +10 | 0 |
| Sorin, Lord of Innistrad | 4 | 46 | 94% | 8 | 46% | 35% | +11 | 5 |
| Austere Command | 6 | 44 | 55% | 9.5 | 46% | 35% | +10 | 13 |
| Arcane Signet | 2 | 49 | 98% | 4.0 | 45% | 35% | +10 | 0 |
| Order of Sacred Dusk | 8 | 49 | 86% | 8.0 | 45% | 35% | +10 | 5 |
| Blood Artist | 2 | 43 | 91% | 7 | 44% | 36% | +9 | 6 |
| Sol Ring | 1 | 43 | 98% | 7.0 | 44% | 36% | +9 | 0 |
| Viscera Seer | 1 | 34 | 88% | 6.0 | 44% | 36% | +8 | 4 |
| Utter End | 4 | 50 | 98% | 6 | 44% | 35% | +9 | 0 |
| Twilight Prophet | 4 | 51 | 74% | 7.5 | 43% | 36% | +8 | 9 |
| Dusk Legion Zealot | 2 | 52 | 86% | 6 | 42% | 36% | +6 | 8 |
| Indulgent Aristocrat | 1 | 55 | 96% | 8 | 42% | 36% | +6 | 4 |
| Vona, Butcher of Magan | 5 | 34 | 74% | 7 | 41% | 37% | +4 | 7 |
| Mavren Fein, Dusk Apostle | 3 | 49 | 98% | 6.5 | 41% | 36% | +4 | 1 |
| Butcher of Malakir | 7 | 48 | 50% | 9.0 | 40% | 37% | +3 | 13 |
| Champion of Dusk | 5 | 48 | 69% | 9 | 40% | 37% | +3 | 14 |
| Redemption Choir | 4 | 43 | 58% | 9 | 40% | 37% | +3 | 14 |
| Elenda's Hierophant | 3 | 49 | 82% | 8.5 | 39% | 37% | +2 | 7 |
| Martyr of Dusk | 2 | 52 | 88% | 7.5 | 38% | 37% | +1 | 3 |
| Orzhov Signet | 2 | 47 | 100% | 6 | 38% | 37% | +1 | 0 |
| Return to Dust | 4 | 55 | 91% | 8.0 | 38% | 37% | +1 | 4 |
| Olivia's Wrath | 5 | 45 | 80% | 8.0 | 38% | 37% | +0 | 5 |
| Bloodghast | 2 | 51 | 67% | 8.5 | 37% | 38% | -0 | 10 |
| Commander's Sphere | 3 | 51 | 98% | 4.0 | 37% | 38% | -0 | 0 |
| Legion Lieutenant | 2 | 50 | 94% | 7 | 36% | 38% | -2 | 7 |
| Yahenni, Undying Partisan | 3 | 54 | 76% | 8 | 35% | 38% | -3 | 11 |
| Heirloom Blade | 3 | 49 | 92% | 7 | 35% | 38% | -4 | 2 |
| Wayfarer's Bauble | 1 | 52 | 94% | 5 | 35% | 38% | -4 | 3 |
| Master of Dark Rites | 1 | 55 | 87% | 4.0 | 34% | 39% | -4 | 5 |
| Damn | 2 | 38 | 95% | 5.5 | 34% | 38% | -4 | 1 |
| Glass-Cast Heart | 3 | 39 | 87% | 6.5 | 33% | 38% | -5 | 3 |
| Swords to Plowshares | 1 | 52 | 100% | 7.0 | 33% | 39% | -6 | 2 |
| Oathsworn Vampire | 2 | 43 | 74% | 7.0 | 33% | 39% | -6 | 5 |
| Village Rites | 1 | 37 | 70% | 8.0 | 32% | 39% | -6 | 15 |
| Crossway Troublemakers | 6 | 38 | 82% | 9 | 32% | 39% | -7 | 9 |
| Bloodtracker | 4 | 49 | 71% | 8 | 31% | 40% | -9 | 11 |
| Swiftfoot Boots | 2 | 38 | 97% | 7 | 29% | 40% | -11 | 2 |
| Welcoming Vampire | 3 | 53 | 85% | 7 | 28% | 41% | -12 | 8 |
