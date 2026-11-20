# Mistakes counted at the owner's table, 2026-11-20

The first count at scale of the mistakes `runner/mistakes.py` reads from the logs (DESIGN.md §34): the ten shipped arms of
`ab-run` #45 (run id 44801095534, commit 772c943, harness 0.4.0, seed 20261380), 200 tables a deck at the owner's table, every
seat under its shipped playbook: 2,000 games, 8,000 seat-games.

- `owners-table-shipped.json`: every seat together (`runner/mistakes.py RUN_DIR... --json`).
- `owners-table-shipped-by-deck.json`: the same by deck (`--by-deck`). Both keep the first forty kills not taken as examples.

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
| attacks that left at least a seat's life unblocked | 4,290; the seat died that turn in 4,146 |
| deaths by a block not made | 135 (3.3% of the deaths in combat); 59 of them had an attacker with trample, which a block does not stop whole (`docs/agents/block_check.py`) |
| deaths tapped out | 686 (16.5%): the seat had attacked on its own turn before in 500 (with every creature that could in 297; the attack took a player out in 145; the killer was a player it had attacked in 223, another in 277), and had not in 186 (`docs/agents/tapped_out.py`) |
| turns with an able attacker on which the seat attacked | 58% (39 to 78% by deck) |
| turns with an opponent who could not block: attacked it | 30% (22 to 41%) |

The exam these games belong to showed that the third kind of kill is not a mistake: a seat that took every such kill won fewer
tables than the same seat leaving the weaker opponent alive (`demo-data/ab/README.md`, `2026-11-20-ab-v24/`). The mistakes among
the kills are the first two kinds: 238 turns in 2,000 games, one in eight or nine games.
