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
