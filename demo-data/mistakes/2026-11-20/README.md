# Mistakes counted at the owner's table, 2026-11-20

The first count at scale of the mistakes `runner/mistakes.py` reads from the logs (DESIGN.md §34): the ten shipped arms of
`ab-run` #45 (run id 44801095534, commit 772c943, harness 0.4.0, seed 20261380), 200 tables a deck at the owner's table, every
seat under its shipped playbook: 2,000 games, 8,000 seat-games.

- `owners-table-shipped.json`: every seat together (`runner/mistakes.py RUN_DIR... --json`).
- `owners-table-shipped-by-deck.json`: the same by deck (`--by-deck`). Both keep the first forty kills not taken as examples.
- `attackers-by-danger.json`: whom the attackers went at (`docs/agents/attack_danger.py RUN_DIR... --json`), added on 2026-11-21 with the split of the open-board turns; no earlier figure changed.

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 6,236 |
| an opponent it was sure to kill went out that turn | 3,814 |
| another opponent went out instead | 200 |
| missed | 2,222 (36%): 1,913 with nothing sent at that opponent, 309 with too little or stopped |
| ... the opponent was the last one (the kill wins the game) | 1,454 turns, 80 missed (6%) |
| ... the most dangerous of several (life + 2 x nonland permanents) | 1,118 turns, 158 missed (14%) |
| ... a less dangerous one while a more dangerous one lived | 3,664 turns, 1,984 missed (54%) |
| counted once an opponent instead of once a turn (`docs/agents/kill_chances.py`) | 5,616 opponents: out on the first turn the kill was sure 2,819 (50%), on a later one 1,101 (20%), on none 1,696 (30%); of those let live 336 won the game |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 4,423; the seat died that turn in 4,279 |
| deaths by a block not made | 54 (1.3% of the deaths in combat); 46 of them had an attacker with trample, which a block does not stop whole (`docs/agents/block_check.py`), and 8 had neither |
| deaths tapped out | 666 (15.6%): the seat had attacked on its own turn before in 485 (with every creature that could in 289; the attack took a player out in 142; the killer was a player it had attacked in 217, another in 268), and had not in 181 (`docs/agents/tapped_out.py`) |
| deaths on a turn a commander's damage on the seat reached 21 | 457 (10.7%), in neither of the two rows above: these logs do not say whether that commander could have been blocked (harness 0.4.3 does) |
| turns with an able attacker on which the seat attacked | 58% (39 to 78% by deck) |
| turns with an opponent who could not block: attacked it | 30% (22 to 41%) of 19,341; attacked only opponents that could block 35% (22 to 52%); attacked nobody 35% (18 to 52%) |
| attackers at the opponent that looks most dangerous (`attackers-by-danger.json`, `docs/agents/attack_danger.py`) | with three opponents alive 47.8% of 43,245 (a random opponent 33.3%), with two 53.4% of 20,376; at the player who went on to win 24.3% and 32.7% of the attackers of seats that did not |
| declarations that sent nothing at the most dangerous opponent | 12,144 of 25,882: the one attacked had the lowest life at the table in 73%, the damage sure to get through was at least as much at the most dangerous one in 72%, and in 5,786 that held with the most dangerous one ahead by five or more |

Counted again on 2026-11-21, when replays of these tables showed that most of the deaths first counted as a block not made (135) were deaths by commander damage: 81 of them, nearly all to one flying commander, The Wise Mothman. The first version of this table had 4,290 lethal attacks, 4,146 deaths, 135 by a block not made and 686 tapped out; the files are the recount.

The exam these games belong to showed that the third kind of kill is not a mistake: a seat that took every such kill won fewer
tables than the same seat leaving the weaker opponent alive (`demo-data/ab/README.md`, `2026-11-20-ab-v24/`). The mistakes among
the kills are the first two kinds: 238 turns in 2,000 games, one in eight or nine games.
