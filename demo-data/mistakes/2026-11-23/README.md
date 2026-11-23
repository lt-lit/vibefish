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
