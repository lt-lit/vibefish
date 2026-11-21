# Mistakes counted at the owner's table, 2026-11-21: the second baseline

The same count as `../2026-11-20/` on 2,000 new games (DESIGN.md §35): the ten shipped arms of `ab-run` #46 (run id
44843287002, commit aa25502, harness 0.4.1, seed 20261390), 200 tables a deck at the owner's table, every seat under the
playbook that was shipped until 2026-11-21. These are the base arms of the ten exams read that day, and the last games
played before the hooks written for these mistakes shipped; the first baseline is in brackets.

- `owners-table-shipped.json`: every seat together (`runner/mistakes.py RUN_DIR... --json`).
- `owners-table-shipped-by-deck.json`: the same by deck (`--by-deck`). Both keep the first forty kills not taken as examples.
- `attackers-by-danger.json`: whom the attackers went at (`docs/agents/attack_danger.py RUN_DIR... --json`).

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 6,192 (6,236) |
| missed | 2,237, 36% (2,222, 36%): 1,912 with nothing sent at that opponent, 325 with too little or stopped |
| ... the opponent was the last one (the kill wins the game) | 1,436 turns, 78 missed, 5% (1,454, 80, 6%) |
| ... the most dangerous of several (life + 2 x nonland permanents) | 1,093 turns, 172 missed, 16% (1,118, 158, 14%) |
| ... a less dangerous one while a more dangerous one lived | 3,663 turns, 1,987 missed, 54% (3,664, 1,984, 54%) |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 4,366; the seat died that turn in 4,226 (4,423; 4,279) |
| deaths by a block not made | 6 (54, of which 46 had an attacker with trample; these logs carry trample in the block count) |
| deaths tapped out | 574, 13.6% of the deaths in combat (666, 15.6%: the same count without trample, which a creature kept home does not stop whole) |
| deaths on a turn a commander's damage on the seat reached 21 | 473, 11.2% (457, 10.7%) |
| turns with an able attacker on which the seat attacked | 57% (58%); 39 to 78% by deck |
| turns with an opponent who could not block: attacked it | 31% of 20,145 (30% of 19,341); attacked only opponents that could block 34% (35%); attacked nobody 35% (35%) |
| attackers at the opponent that looks most dangerous | with three opponents alive 48.8% of 42,914 (47.8%; a random opponent 33.3%), with two 51.5% of 19,865 (53.4%); at the player who went on to win 24.5% and 29.8% of the attackers of seats that did not (24.3%, 32.7%) |
| declarations that sent nothing at the most dangerous opponent | 11,971 of 25,647: the one attacked had the lowest life at the table in 75%, the damage sure to get through was at least as much at the most dangerous one in 72%, and in 5,803 that held with the most dangerous one ahead by five or more |
| games without a winner | 25 of 2,000 (`docs/agents/unfinished.py`): 22 in one deck's endless chain (Miracle Worker's Ondu Spiritdancer copying itself, 21 on the thirty-minute clock and one draw), two in Blight Curse chains (Blowfly Infestation with Flourishing Defenses, an exception after the loop had gone round 3,663 times; with Hapatra, a draw), one draw of everybody at once. The 25 took 11.1 of the 66.3 hours of play |

The counts repeat within a point on new games, apart from the two that the logs now measure better (trample). So the
figures are properties of the pilots and not of one draw of tables, and a hook's effect on them can be read against
either baseline.
