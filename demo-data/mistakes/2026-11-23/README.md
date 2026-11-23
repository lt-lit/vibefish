# Mistakes counted on 2026-11-23: the league of twelve with every hook in every seat

`league-run` #6 (run id 45083908949, commit c37c68a, harness 0.4.13, seed 20261440 on `runner/leagues/bots-v2.json`, 50
cycles): 600 games, 200 a deck, every seat a pool deck under the playbook shipped on 2026-11-22 evening, the first set in
which all twelve carry the six hooks (the leader's kill, the attack aimed, free damage, the guard, the removal triggers
aimed, the blocks). The league's rollup is on the dashboard (`../../runs/2026-11-22-bots-v2-snapshot-2026-11-10-s20261440-bots/`);
the 20 shard artifacts and the run's own rollup were fetched, and the rollup made from the shards is the run's own.
The figures in brackets are the pool's baseline without any hook (`../2026-11-22/`, the shipped arms of `ab-run` #58:
2,400 games on the same pool, every seat a bot; other tables and four times the games, so a reading across runs).

- `league-run-6-all-seats.json`: every seat together (`runner/mistakes.py RUN_DIR --json`).
- `league-run-6-by-deck.json`: the same by deck (`--by-deck`).
- `league-run-6-attackers-by-danger.json`: whom the attackers went at (`docs/agents/attack_danger.py RUN_DIR --json`).

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 1,957 |
| ... the opponent was the last one (the kill wins the game) | 340 turns, 6 missed, 1.8% (4.0%) |
| ... the most dangerous of several (life + 2 x nonland permanents) | 460 turns, 14 missed, 3.0% (12.3%); nothing sent at that opponent on 1 of the 14 |
| ... a less dangerous one while a more dangerous one lived (not a mistake) | 1,157 turns, 737 left alone, 63.7% (56.5%) |
| set aside: a kill by the count on a turn a permanent limited the attackers | 91 turns |
| turns on which only a commander gave a sure kill (new with harness 0.4.13) | of the last opponent 3 (0 with nobody out), of the most dangerous 19 (5 with nobody out, nothing sent at that opponent on 5), of a lesser one 34 (23 left alone); a commander would have reached 21 but could be blocked on 231 more |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 1,426; the seat died that turn in 1,402 |
| deaths by a block not made | 1 (150 in the baseline's 2,400 games) |
| deaths with the seat's own creatures tapped | 157, 6.5 a hundred seat-games (5.3) |
| deaths on a turn a commander's damage on the seat reached 21 | 109, 4.5 a hundred seat-games (6.9) |
| turns with an able attacker on which the seat attacked | 61.4% (52.4%); 63.4% of the damage it could send (61.9%) |
| turns with an opponent who could not block: attacked it | 60.0% of 7,451 (29.3%); attacked only opponents that could block 21.2% (30.3%); attacked nobody 18.7% (40.4%) |
| attackers at the opponent that looks most dangerous | with three opponents alive 57.2% of 20,666 (50.8%; a random opponent 33.3%), with two 65.4% of 7,467 (58.1%); at the player who went on to win 31.4% and 42.6% of the attackers of seats that did not (26.8%, 36.9%) |
| games without a winner | 4 of 600 (`docs/agents/unfinished.py`), all on the thirty-minute clock: two in Tricky Terrain's Scute Swarm, one with a board of Wretched Ranks' Zombie tokens, one with no long chain; none in Eldrazi Incursion's chain. They took 2.0 of the 19.2 hours of play (31 of 2,400 in the baseline) |

## By deck (200 seat-games each)

| Deck | Wins of 200 | Attacked, of turns it could | Open board attacked | Sure kill missed: the most dangerous of several | the last opponent | a lesser one left alone | A commander's sure kill of the most dangerous or the last opponent, nobody out | A commander would have reached 21 but could be blocked | Deaths in combat | a block not made | tapped out | commander damage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Enduring Enchantments | 84 | 67.2% | 69.1% | 1 of 71 | 1 of 49 | 66 of 115 | 0 of 0 | 4 | 79 | 0 | 13 | 8 |
| Eldrazi Incursion | 70 | 56.4% | 57.5% | 3 of 51 | 0 of 48 | 60 of 110 | 0 of 0 | 1 | 107 | 0 | 5 | 6 |
| Token Triumph | 60 | 61.5% | 70.0% | 1 of 69 | 1 of 36 | 108 of 160 | 0 of 0 | 4 | 104 | 0 | 8 | 15 |
| Quick Draw | 57 | 54.8% | 56.8% | 2 of 28 | 0 of 37 | 61 of 97 | 0 of 0 | 0 | 99 | 0 | 8 | 10 |
| Deep Clue Sea | 55 | 65.2% | 52.6% | 0 of 41 | 1 of 24 | 57 of 86 | 0 of 2 | 64 | 116 | 0 | 15 | 11 |
| Planeswalker Party | 51 | 57.0% | 52.1% | 0 of 15 | 1 of 29 | 25 of 53 | 0 of 0 | 0 | 119 | 0 | 8 | 5 |
| Hail, Caesar | 43 | 67.2% | 62.3% | 0 of 16 | 1 of 23 | 44 of 87 | 0 of 0 | 2 | 132 | 0 | 15 | 9 |
| Goblin Storm | 42 | 61.1% | 76.6% | 2 of 45 | 0 of 19 | 62 of 91 | 0 of 0 | 4 | 112 | 0 | 14 | 9 |
| Tricky Terrain | 41 | 69.8% | 45.3% | 3 of 55 | 1 of 20 | 80 of 89 | 0 of 0 | 0 | 124 | 0 | 19 | 6 |
| Elven Council | 33 | 58.3% | 57.9% | 0 of 32 | 0 of 25 | 62 of 103 | 1 of 3 | 35 | 136 | 1 | 15 | 10 |
| Limit Break | 31 | 61.5% | 50.8% | 1 of 14 | 0 of 15 | 37 of 66 | 4 of 17 | 117 | 142 | 0 | 19 | 6 |
| Wretched Ranks | 29 | 57.7% | 59.1% | 1 of 23 | 0 of 15 | 75 of 100 | 0 of 0 | 0 | 132 | 0 | 18 | 14 |

Limit Break sat in this league under version 4, without the commander's kill it has had since 2026-11-23 (`ab-run` #66,
`../../ab/2026-11-23-ab-v34/`): 17 of the league's 22 turns on which only a commander gave a sure kill of the most
dangerous or the last opponent are its own, and 4 of the 5 left with nobody out. Elven Council has 3 such turns in its
200 seat-games and Deep Clue Sea 2; no other deck of the pool has one.

## The receiving seat (`docs/agents/received.py`)

What the other three players do to a seat's board, counted for every seat and grouped by the deck that receives: each
nonland card that is not a token and leaves the battlefield is filed by what took it (another player's spell or ability
that named it, a spell that swept it without naming it, combat, the seat's own doing) and by whose turn it was. It is the
measure an opponent is to be judged by (DESIGN.md §29) and the baseline for the rules for other players' turns: neither
league below has a seat that holds its removal for another player's turn.

### The owner's table, `league-run` #5 (504 games, the versions of the morning of 2026-11-22; `received-league-run-5.json`)

| Deck | Seat-games | Commander casts a seat-game | Its commander answered, a hundred seat-games | Seat-games with it answered at least once | Commander exits: named by another player's spell or ability, swept, combat, own or other | Of the answers: on the remover's own turn, on the seat's own, on a third player's | Other nonland permanents answered a seat-game (named, swept) | lost in combat | Aimed at its permanents a seat-game, share at its commander |
|---|---|---|---|---|---|---|---|---|---|
| mutant-menace | 204 | 2.23 | 147 | 77.9% | 210, 90, 17, 19 | 98.3%, 1.7%, 0.0% | 2.45 (1.00, 1.45) | 0.62 | 3.47, 42.1% |
| deadly-disguise | 200 | 2.50 | 141 | 71.5% | 85, 197, 57, 39 | 98.2%, 0.7%, 1.1% | 4.16 (1.35, 2.80) | 1.16 | 3.39, 19.0% |
| squirreled-away | 204 | 2.19 | 134 | 74.0% | 168, 106, 26, 23 | 98.2%, 1.5%, 0.4% | 2.66 (0.84, 1.82) | 0.85 | 3.38, 38.1% |
| revenant-recon | 204 | 2.27 | 120 | 72.5% | 129, 115, 36, 51 | 97.1%, 2.0%, 0.8% | 3.42 (0.96, 2.47) | 0.93 | 3.11, 32.8% |
| blood-rites | 200 | 2.52 | 114 | 70.5% | 59, 170, 75, 70 | 97.8%, 1.3%, 0.9% | 4.17 (1.52, 2.64) | 1.50 | 4.29, 12.8% |
| veloci-ramp-tor | 204 | 2.26 | 109 | 64.7% | 94, 129, 47, 33 | 97.3%, 1.8%, 0.9% | 4.39 (1.57, 2.81) | 1.05 | 3.65, 21.1% |
| death-toll | 200 | 2.14 | 104 | 64.5% | 99, 109, 51, 19 | 97.1%, 2.4%, 0.5% | 4.01 (1.88, 2.13) | 1.91 | 4.63, 16.4% |
| blight-curse | 200 | 2.20 | 94 | 63.0% | 47, 140, 50, 77 | 98.4%, 0.5%, 1.1% | 3.34 (1.27, 2.06) | 0.91 | 3.02, 21.4% |
| miracle-worker | 200 | 2.12 | 89 | 60.5% | 62, 116, 41, 75 | 100.0%, 0.0%, 0.0% | 2.76 (1.11, 1.65) | 0.76 | 3.46, 19.0% |
| ahoy-mateys | 200 | 1.86 | 64 | 45.5% | 31, 96, 84, 44 | 99.2%, 0.8%, 0.0% | 4.37 (1.83, 2.54) | 1.50 | 3.05, 9.7% |
| all ten | 2016 | 2.23 | 112 | 66.5% | 984, 1268, 484, 450 | 98.1%, 1.3%, 0.6% | 3.57 (1.33, 2.24) | 1.12 | 3.54, 22.9% |

### The pool, `league-run` #6 (600 games, the versions of 2026-11-22 evening; `received-league-run-6.json`)

| Deck | Seat-games | Commander casts a seat-game | Its commander answered, a hundred seat-games | Seat-games with it answered at least once | Commander exits: named by another player's spell or ability, swept, combat, own or other | Of the answers: on the remover's own turn, on the seat's own, on a third player's | Other nonland permanents answered a seat-game (named, swept) | lost in combat | Aimed at its permanents a seat-game, share at its commander |
|---|---|---|---|---|---|---|---|---|---|
| token-triumph | 200 | 2.87 | 165 | 73.5% | 76, 254, 57, 64 | 95.8%, 2.1%, 2.1% | 4.49 (1.27, 3.21) | 0.91 | 3.42, 19.9% |
| enduring-enchantments | 200 | 2.52 | 153 | 73.5% | 132, 174, 42, 26 | 95.4%, 3.6%, 1.0% | 4.63 (0.89, 3.75) | 0.77 | 2.81, 36.4% |
| deep-clue-sea | 200 | 2.62 | 141 | 72.5% | 98, 184, 39, 116 | 97.2%, 2.1%, 0.7% | 3.73 (0.96, 2.77) | 0.64 | 3.15, 28.5% |
| elven-council | 200 | 2.52 | 136 | 70.5% | 97, 176, 51, 81 | 98.5%, 1.5%, 0.0% | 4.44 (1.17, 3.27) | 0.70 | 2.94, 25.2% |
| quick-draw | 200 | 2.42 | 136 | 70.0% | 68, 205, 47, 41 | 97.4%, 1.5%, 1.1% | 4.40 (0.85, 3.55) | 0.91 | 3.65, 23.9% |
| tricky-terrain | 200 | 2.71 | 122 | 63.0% | 44, 201, 98, 85 | 95.9%, 3.3%, 0.8% | 3.88 (1.11, 2.77) | 1.59 | 3.69, 10.9% |
| wretched-ranks | 200 | 2.04 | 112 | 66.5% | 91, 134, 25, 81 | 98.2%, 1.3%, 0.4% | 3.62 (1.10, 2.51) | 1.01 | 3.00, 20.5% |
| limit-break | 200 | 2.06 | 110 | 64.0% | 100, 120, 36, 44 | 95.0%, 4.5%, 0.5% | 3.92 (1.10, 2.82) | 0.61 | 2.75, 27.0% |
| eldrazi-incursion | 200 | 2.05 | 110 | 56.5% | 72, 147, 30, 46 | 96.8%, 2.7%, 0.5% | 3.16 (0.97, 2.19) | 0.70 | 3.29, 13.4% |
| hail-caesar | 200 | 2.21 | 109 | 64.5% | 108, 110, 46, 82 | 99.1%, 0.5%, 0.5% | 3.35 (0.99, 2.37) | 1.15 | 3.15, 24.1% |
| goblin-storm | 200 | 1.82 | 84 | 59.5% | 60, 108, 40, 48 | 97.0%, 2.4%, 0.6% | 3.48 (0.74, 2.74) | 0.71 | 2.04, 19.6% |
| planeswalker-party | 200 | 3.58 | 39 | 33.0% | 47, 31, 441, 79 | 97.4%, 1.3%, 1.3% | 3.27 (1.13, 2.13) | 2.27 | 3.46, 7.5% |
| all twelve | 2400 | 2.45 | 118 | 63.9% | 993, 1844, 952, 793 | 96.9%, 2.3%, 0.8% | 3.86 (1.03, 2.84) | 1.00 | 3.11, 21.0% |

At both tables a commander is taken off the battlefield by another player's spell or ability a little more than once a
seat-game (112 and 118 times a hundred seat-games; in 67% and 64% of the seat-games at least once), more often by a wipe than by
a spell that names it, and 98% and 97% of those answers come on the remover's own turn. The cards that do it are the decks' wipes and
their removal (`by_card` in the two files). Planeswalker Party's commander is a planeswalker: it leaves in combat, attacked,
and is seldom answered by a spell.

## The owner's table again: `league-run` #7 on the tables of `league-run` #5

`league-run` #7 (run id 45096445356, commit d8dc8ff, harness 0.4.13; seed 20261430 on `runner/leagues/owners-table-v1.json`,
63 cycles: 504 games) plays the seed and cycles of `league-run` #5 again, so the same 504 tables, seat for seat and shuffle
for shuffle (checked: every table has #5's seating and seed), under the versions shipped on 2026-11-23. What differs from
#5: the rules for other players' turns in nine decks (all but Ahoy Mateys), Mutant Menace's commander's kill, Blight Curse's
limit a turn on one trigger, and the harness (0.4.13 where #5 was on 0.4.11). The 20 shard artifacts and the run's own
rollup were fetched; the rollup made from the shards is the run's own. On the dashboard
(`../../runs/2026-11-23-owners-table-v1-snapshot-2026-11-10-s20261430-bots/`). `league-run` #5's figures are in brackets
(`../2026-11-22/owners-table-shipped*.json`).

- `owners-table-league-run-7.json`, `owners-table-league-run-7-by-deck.json`, `owners-table-league-run-7-attackers-by-danger.json`: the count, as above.
- `received-league-run-7.json`: the receiving seat (`received-league-run-5.json` is the side before).
- `league-pair-5-7.json`: the two leagues table by table (`docs/agents/league_pair.py`).

### Table by table

248 of the 504 tables have the same winner in both leagues (49.2%), and 61 are the same game to the last cast, attack and
loss. The first line that differs comes at turn 14 at the median (a quarter of the tables by turn 11, three quarters by
turn 23). A game takes 43.9 turns (43.5) and 94 seconds (90); one game has no winner (a draw Forge declared
at turn 43), none had in #5. Every seat changed at once, so a deck's line is its own rules and its opponents' together:
a description of the table before and after, not a measurement of the deck's change (`ab-run` #64 is that, one seat at
a time: 123 tables against 117 over the ten decks).

| Deck | Versions | Tables | Wins in #5 | Wins in #7 | Won in both | Only in #5 | Only in #7 | Exact test on the two |
|---|---|---|---|---|---|---|---|---|
| Veloci-Ramp-Tor | 6 to 7 | 204 | 64 | 81 | 42 | 22 | 39 | 0.04 |
| Blood Rites | 6 to 7 | 200 | 67 | 72 | 39 | 28 | 33 | 0.61 |
| Death Toll | 5 to 6 | 200 | 53 | 61 | 29 | 24 | 32 | 0.35 |
| Revenant Recon | 7 to 8 | 204 | 48 | 58 | 29 | 19 | 29 | 0.19 |
| Ahoy Mateys | 4 to 4 | 200 | 66 | 55 | 32 | 34 | 23 | 0.18 |
| Blight Curse | 5 to 7 | 200 | 42 | 52 | 19 | 23 | 33 | 0.23 |
| Mutant Menace | 5 to 7 | 204 | 43 | 40 | 18 | 25 | 22 | 0.77 |
| Miracle Worker | 6 to 7 | 200 | 44 | 39 | 16 | 28 | 23 | 0.58 |
| Squirreled Away | 7 to 8 | 204 | 44 | 25 | 13 | 31 | 12 | 0.01 |
| Deadly Disguise | 5 to 6 | 200 | 33 | 20 | 11 | 22 | 9 | 0.03 |

Three of the ten lines are beyond what the exact test allows one deck at 0.05: Veloci-Ramp-Tor up (22 tables against
39), Squirreled Away down (31 against 12) and Deadly Disguise down (22 against 9). Among ten decks one such line is to be
expected about four times in ten when nothing changed, three are not; the lines are not independent (a table one deck
gains another loses). Squirreled Away's and Deadly Disguise's own rules were level when only they had them (`ab-run` #64:
7 tables against 7, and 7 against 9), so what moved is the table around them or chance, and one pair of leagues cannot
say which. Their own rules at the table as it is now are the thing that can be measured (the two decks' second sample,
CLAUDE.md, In flight).

### The receiving seat, before and after

| | `league-run` #5 | `league-run` #7 |
|---|---|---|
| commander casts a seat-game | 2.23 | 2.23 |
| a commander taken off the battlefield by another player's spell or ability, a hundred seat-games | 111.7 (984 named, 1268 swept) | 109.5 (964 named, 1244 swept) |
| seat-games in which that happened at least once | 66.5% | 66.8% |
| of those answers: on the remover's own turn | 98.1% | 85.5% |
| ... on the seat's own turn | 1.3% | 7.0% |
| ... on a third player's turn | 0.6% | 7.5% |
| other nonland permanents answered a seat-game (named, swept) | 3.57 (1.33, 2.24) | 3.71 (1.39, 2.32) |
| of those: on the remover's own turn | 97.6% | 91.3% |
| other nonland permanents lost in combat a seat-game | 1.12 | 1.12 |
| commanders lost in combat | 484 | 548 |
| other players' spells and abilities aimed at its permanents a seat-game, share at its commander | 3.54, 22.9% | 3.51, 22.1% |

A seat receives as much removal as before: its commander is answered once a seat-game and a little more, 3.6 to 3.7 of
its other permanents a game. What changed is when. One answer to a commander in seven now comes on a turn that is not
the remover's own, where it was one in fifty; for the other permanents one in eleven, from one in forty. The rules hold
a deck's single-target instants only, and most of what answers a commander is a wipe or a creature's or a sorcery's
doing (`by_card`), which is why it is one in seven and not more.

| Deck | Its commander answered, a hundred seat-games: #5, #7 | Named by a spell or ability: #5, #7 | Of the answers not on the remover's own turn: #5, #7 | Other permanents answered a seat-game: #5, #7 |
|---|---|---|---|---|
| Veloci-Ramp-Tor | 109, 105 | 94, 94 | 2.7%, 14.0% | 4.39, 4.72 |
| Blood Rites | 114, 128 | 59, 78 | 2.2%, 12.1% | 4.17, 4.31 |
| Death Toll | 104, 108 | 99, 95 | 2.9%, 15.8% | 4.01, 4.38 |
| Revenant Recon | 120, 123 | 129, 131 | 2.9%, 21.5% | 3.42, 3.93 |
| Ahoy Mateys | 64, 70 | 31, 43 | 0.8%, 15.0% | 4.37, 4.47 |
| Blight Curse | 94, 76 | 47, 31 | 1.6%, 9.9% | 3.34, 2.96 |
| Mutant Menace | 147, 119 | 210, 168 | 1.7%, 18.9% | 2.45, 2.12 |
| Miracle Worker | 89, 88 | 62, 78 | 0.0%, 16.5% | 2.76, 3.06 |
| Squirreled Away | 134, 150 | 168, 188 | 1.8%, 19.7% | 2.66, 2.71 |
| Deadly Disguise | 141, 128 | 85, 58 | 1.8%, 0.4% | 4.16, 4.47 |

The Wise Mothman is named by a removal spell 168 times where it was 210. A likely reason, not a measured one: removal kept for the end
step goes at the best permanent of the opponent that looks most dangerous, where Forge's AI on its own turn takes the best
target anywhere, and the Mothman is that target more often than its deck is that opponent.

### The counted mistakes, every seat

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 1,735 (1,631) |
| ... the opponent was the last one | 329 turns, 9 missed, 2.7% (314, 6, 1.9%) |
| ... the most dangerous of several | 357 turns, 24 missed, 6.7% (363, 20, 5.5%); nothing sent at that opponent on 2 |
| ... a less dangerous one while a more dangerous one lived (not a mistake) | 1,049 turns, 690 left alone, 65.8% (954, 603, 63.2%) |
| turns on which only a commander gave a sure kill (harness 0.4.13; #5's logs do not have it) | of the last opponent 2 (0 with nobody out), of the most dangerous 25 (1 with nobody out), of a lesser one 36 (27 left alone); a commander would have reached 21 but could be blocked on 128 more |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 1,123; the seat died that turn in 1,097, 54.4 a hundred seat-games (1,135; 1,095, 54.3) |
| deaths by a block not made | 0 (0) |
| deaths with the seat's own creatures tapped | 152, 7.5 a hundred seat-games (170, 8.4) |
| deaths on a turn a commander's damage on the seat reached 21 | 90, 4.5 a hundred seat-games (85, 4.2) |
| turns with an able attacker on which the seat attacked | 66.4% (66.2%) |
| turns with an opponent who could not block: attacked it | 65.1% of 5,369 (64.4% of 5,162); attacked nobody 11.9% (12.1%) |
| attackers at the opponent that looks most dangerous | with three opponents alive 56.5% of 13,276 (55.7% of 12,923), with two 64.6% of 4,588 (63.5% of 4,768); at the player who went on to win 29.2% and 38.8% of the attackers of seats that did not (28.1%, 39.5%) |

The attack and the blocks are where they were, as they should be: nothing in the rules for other players' turns touches
them. The commander's kill is counted at this table for the first time. Mutant Menace, with the option, has 20 of the 27 turns
on which only a commander gave a sure kill of the most dangerous or the last opponent and left one with nobody out;
Revenant Recon has 5, Miracle Worker and Veloci-Ramp-Tor one each, all taken. The one left is a tie: two opponents
looked equally dangerous, the walk of `"finish": "leader"` stopped at the first, which had no sure kill, and the second,
which the Mothman was sure to kill, was not looked at (game g00299, turn 21). The count files a tie under the most
dangerous; the walk should too.

## Seats out of the game on their own turn (`own-turn-deaths.json`)

`runner/mistakes.py` counts them since 2026-11-23 (ITS OWN TURN; DESIGN.md §45): a seat out of the game on its own
turn, and of those the ones where the `life` line that took it to zero lies between the `cast` line of a spell of its
own and that spell's `resolve` line: it paid for its own spell with its game. The file holds, for `league-run` #5, #6
and #7, each deck's counts and every such death with the game, the turn, the kind and the card.

| | Games | Out on their own turn | By the price of their own spell | After their own spell had resolved | By an ability or trigger they controlled |
|---|---|---|---|---|---|
| `league-run` #5 (the owner's table, the versions of 2026-11-22) | 504 | 113 | 17 | 1 | 48 |
| `league-run` #7 (the same tables, the versions of 2026-11-23) | 504 | 105 | 16 | 1 | 49 |
| `league-run` #6 (the pool) | 600 | 30 | none | none | 20 |

The 33 at the owner's table: Reanimate 18 (Revenant Recon 15, Death Toll 3), Eventide's Shadow 5 (Blight Curse; three
more of its casts emptied the library and are filed as not by life), Rakdos Charm 4 (Ahoy Mateys), Notion Rain 2
(Revenant Recon), Hoarder's Greed 2 and Painful Truths 1 (Blight Curse), Pact of the Serpent 1 (Veloci-Ramp-Tor,
cast through Etali). The column of abilities and triggers is mostly another deck's doing (Radiation, from Mutant
Menace's rad counters: 31 and 38; the emblem of Chandra, Awakened Inferno at the pool: 13) and is not judged. Not by
life: Death Toll had no card left to draw on its own turn in 7 and 5 of its 200 games.
