# Mistakes counted on 2026-11-22: the pool's first baseline, and the owner's table with the hooks in every seat

## The pool of twelve

The count of `../2026-11-20/` and `../2026-11-21/` (DESIGN.md §34, §35) on the pool's decks: the twelve shipped arms of
`ab-run` #58 (run id 44934264368, commit 50fb281, harness 0.4.10, seed 20261400), 200 tables a deck on
`runner/leagues/bots-v2.json`, 2,400 games played on 2026-11-21, every seat under its shipped playbook. None of the twelve
has a hook on what is Forge's (the attack is Forge's own for ten of them and go-wide for Hail, Caesar and Tricky Terrain),
so these are the games the hooks' exam on the pool is read against (`ab-run` #59, the same tables). The second baseline at
the owner's table is in brackets: other decks and another table, so a reading across runs.

- `pool-shipped.json`: every seat together (`runner/mistakes.py RUN_DIR... --json`).
- `pool-shipped-by-deck.json`: the same by deck (`--by-deck`). Both keep the first forty kills not taken as examples.
- `attackers-by-danger.json`: whom the attackers went at (`docs/agents/attack_danger.py RUN_DIR... --json`).

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 7,524 (6,192 in 2,000 games) |
| missed | 2,659, 35% (36%): 2,376 with nothing sent at that opponent, 283 with too little or stopped |
| ... the opponent was the last one (the kill wins the game) | 1,650 turns, 66 missed, 4% (5%) |
| ... the most dangerous of several (life + 2 x nonland permanents) | 1,642 turns, 202 missed, 12% (16%) |
| ... a less dangerous one while a more dangerous one lived | 4,232 turns, 2,391 missed, 56% (54%) |
| set aside: a kill by the count on a turn Silent Arbiter allowed one attacker | 249 turns (none at the owner's table: no deck there has such a card) |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 5,400; the seat died that turn in 5,299 |
| deaths by a block not made | 150, 2.8% of the deaths in combat. Not comparable with the 6 of the second baseline: these logs carry a commander's damage in the block count (harness 0.4.3 and later), so a death a block on a commander would have stopped is counted here and was not there |
| deaths tapped out | 508, 9.6% (13.6%) |
| deaths on a turn a commander's damage on the seat reached 21 | 665, 12.5% (11.2%) |
| set aside: deaths in combat on a turn Silent Arbiter allowed one blocker | 32 (in neither of the two counts of blocks) |
| turns with an able attacker on which the seat attacked | 52% (57%); 43 to 70% by deck |
| turns with an opponent who could not block: attacked it | 29% of 28,625 (31%); attacked only opponents that could block 30% (34%); attacked nobody 40% (35%) |
| attackers at the opponent that looks most dangerous | with three opponents alive 50.8% of 71,644 (48.8%; a random opponent 33.3%), with two 58.1% of 35,025 (51.5%); at the player who went on to win 26.8% and 36.9% of the attackers of seats that did not (24.5%, 29.8%) |
| declarations that sent nothing at the most dangerous opponent | 15,980 of 35,994 (3,332 more with a tie for the most dangerous are left out): the one attacked had the lowest life at the table in 68%, the damage sure to get through was at least as much at the most dangerous one in 69%, and in 7,310 that held with the most dangerous one ahead by five or more |
| games without a winner | 31 of 2,400 (`docs/agents/unfinished.py`): 17 on the thirty-minute clock, 10 draws, 4 Forge exceptions; they took 9.5 of the 89.6 hours of play |

So the pool's pilots make the mistakes the owner's ten made before their hooks, at rates a little lower: a sure kill of
the most dangerous opponent passed up on 12% of the turns it is there, half of the attackers at that opponent, an open
board attacked on three turns in ten. That was expected (what is counted is Forge's AI, and it is the same AI) and is now
measured.

## A blind spot of the count, found here and closed

The first count of these games (committed in 11f14ba, an hour before this one) had 7,773 turns with a sure kill and the
winning kill missed on 103 of 1,698 turns. A third of those misses were not misses. Planeswalker Party plays Silent
Arbiter (no more than one creature can attack each combat, no more than one can block), and the `combat` line's damage
"sure to get through" does not know a limit on the number of attackers: a seat with eighty power that sends one creature
at the last opponent was counted as passing up a kill, turn after turn, while doing all the card allows.
`runner/mistakes.py` now follows such permanents through the zone lines and sets those turns aside (`kill_limited_turns`;
deaths in combat under the blocker limit are `deaths_block_limited` and in neither count of blocks). What moved: the
winning kill missed on 66 of 1,650 turns where the first count had 103 of 1,698; the most dangerous opponent's on 202 of
1,642 where it had 251 of 1,705. The counts at the owner's table do not move at all (no deck there has such a card;
checked on the second baseline's games). The harness's own arithmetic has the same gap, and the hooks are safe from it:
an attack they change is validated by Forge, and an invalid one is put back as it was.

## By deck (every seat the deck sat in, as the seat under test or as an opponent)

| Deck | Seat-games | Attacked, of turns it could | Open board attacked | Sure kill missed: the most dangerous of several | the last opponent | a lesser one | Deaths in combat | a block not made | tapped out | commander damage | Kill turns set aside |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Deep Clue Sea | 728 | 57% | 25% | 8 of 80 | 4 of 102 | 132 of 264 | 398 | 20 | 44 | 54 | 19 |
| Eldrazi Incursion | 828 | 47% | 29% | 32 of 259 | 7 of 216 | 191 of 375 | 390 | 7 | 37 | 63 | 19 |
| Elven Council | 820 | 50% | 26% | 4 of 91 | 0 of 110 | 209 of 366 | 489 | 10 | 49 | 53 | 28 |
| Enduring Enchantments | 808 | 57% | 33% | 17 of 237 | 4 of 230 | 216 of 454 | 352 | 20 | 32 | 52 | 12 |
| Goblin Storm | 840 | 45% | 30% | 23 of 160 | 2 of 107 | 224 of 398 | 527 | 10 | 48 | 67 | 14 |
| Hail, Caesar (go-wide) | 890 | 58% | 33% | 11 of 98 | 0 of 118 | 189 of 379 | 492 | 18 | 41 | 63 | 13 |
| Limit Break | 840 | 55% | 25% | 3 of 24 | 2 of 67 | 172 of 305 | 534 | 8 | 43 | 43 | 9 |
| Planeswalker Party | 734 | 53% | 36% | 6 of 83 | 10 of 127 | 73 of 174 | 404 | 0 | 27 | 18 | 47 |
| Quick Draw | 751 | 51% | 27% | 6 of 95 | 2 of 133 | 189 of 339 | 392 | 16 | 51 | 52 | 12 |
| Token Triumph | 855 | 43% | 27% | 21 of 204 | 7 of 180 | 261 of 466 | 486 | 18 | 46 | 91 | 18 |
| Tricky Terrain (go-wide) | 778 | 70% | 33% | 49 of 192 | 20 of 155 | 328 of 380 | 416 | 9 | 51 | 51 | 42 |
| Wretched Ranks | 728 | 45% | 28% | 22 of 119 | 8 of 105 | 207 of 332 | 419 | 14 | 39 | 58 | 16 |

One row stands out. Tricky Terrain passes up the kill that wins the game on 20 of 155 turns and the kill of the most
dangerous opponent on 49 of 192 (13% and 26%; the other eleven together 3% and 11%). Its attack is its own: go-wide at the
opponent with the highest life, and only with two creatures or more to send after its reserve, which it lacked in half of
its 6,185 attack decisions, where Forge declared instead. Whether the misses are the policy's or Forge's has not been read
game by game. It is what `"finish": "leader"` is for, and worth reading when the candidates have played.

## The games without a winner

| Games | Ended | What the last turn held |
|---|---|---|
| 14 (3.4 hours of play) | 7 draws, 6 on the clock, 1 exception | Eldrazi Incursion's commander, wherever the deck sat (4 of them in its own 200 tables): Ulalek, Fused Atrocity's trigger paid for again and again, 44 to 1,129 cast or zone lines of one card in the last turn. The playbook pays whenever ten mana or fewer are at hand, as often as the trigger comes, and each payment copies the triggers that are still waiting. Version 1's notes had this as an open defect from one goldfish game of forty |
| 5 (1.5 hours) | 3 draws, 2 on the clock | Tricky Terrain's Scute Swarm copying itself with every land, 302 to 2,023 lines of it in the last turn. The trigger is not optional, so no trigger rule can stop it |
| 1 | on the clock | Quick Draw: 61 lines of one Dragon Elemental token in the last turn |
| 3 | exceptions | Forge exceptions in games with Quick Draw at the table and no long chain (the card with the most lines in the last turn: Crackling Spellslinger twice, Stella Lee once) |
| 8 | on the clock | no long chain: long games, five of them at Tricky Terrain's own tables |

The last three rows together took 4.5 hours. The fourteen are the pool's version of Miracle Worker's endless chain
(DESIGN.md §35) at a smaller price: 3.4 of 89.6 hours of play, where that one took a sixth of every exam at the owner's
table, because seven of these end within six minutes in a draw Forge declares (the six on the clock took thirty minutes
each). Its fix is a limit a turn on the trigger rule (`playbook/variants/eldrazi-incursion-limit.json`, harness 0.4.11),
which finished all four of the deck's own broken tables in replays; it plays beside the shipped arm on these tables with
`ab-run` #59.

## The owner's table with the hooks in every seat

The same count on the ten next-version arms of `ab-run` #57 (run id 44934245433, commit 473a1b1, harness 0.4.10, seed
20261410): 2,000 games at the owner's table in which every seat plays its version of 2026-11-21, with the hooks and
without the guard (DESIGN.md §36). The second baseline at this table, the same decks before the hooks
(`../2026-11-21/`), is in brackets; these are other tables.

- `owners-table-next.json`, `owners-table-next-by-deck.json`, `owners-table-next-attackers-by-danger.json`: as above.

| | |
|---|---|
| turns on which a seat was sure to kill an opponent | 6,279 (6,192) |
| missed | 2,291, 36% (36%) |
| ... the opponent was the last one | 1,277 turns, 51 missed, 4% (5%) |
| ... the most dangerous of several | 1,298 turns, 57 missed, 4% (16%) |
| ... a less dangerous one while a more dangerous one lived | 3,704 turns, 2,183 missed, 59% (54%) |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 4,505; the seat died that turn in 4,370 (4,366; 4,226) |
| deaths by a block not made | 19: Blood Rites 12, Miracle Worker 6, Mutant Menace 1. The first two are the decks without the block hook; the eight with it have one such death in 6,504 seat-games. (The 6 of the second baseline are not comparable: its logs did not carry a commander's damage in the block count) |
| deaths tapped out | 745, 17.0% of the deaths in combat (574, 13.6%) |
| deaths on a turn a commander's damage on the seat reached 21 | 273, 6.2% (473, 11.2%) |
| turns with an able attacker on which the seat attacked | 64% (57%); 45 to 84% by deck |
| turns with an opponent who could not block: attacked it | 53% of 20,577 (31%); attacked only opponents that could block 27% (34%); attacked nobody 20% (35%). By deck 31 to 77%: the four without that hook 31 to 42%, the six with it 55 to 77% |
| attackers at the opponent that looks most dangerous | with three opponents alive 58.4% of 49,085 (48.8%), with two 65.3% of 16,584 (51.5%); at the player who went on to win 28.5% and 36.2% of the attackers of seats that did not (24.5%, 29.8%) |
| declarations that sent nothing at the most dangerous opponent | 10,033 of 27,918 (11,971 of 25,647), 2,851 more with a tie left out |
| games without a winner | 6 of 2,000, 0.6 of 51.0 hours of play (25, 11.1 of 66.3 hours) |

What the hooks were written for has moved, at a table where everyone has them: the kill of the most dangerous opponent is
missed a quarter as often, six attackers in ten go at that opponent where five did, free damage is taken on half of the
turns it is there. Two things moved that no hook was written for. Deaths tapped out are up by 30%: the price of attacking
more, and what the guard is for (it is in none of these games; in the guard arms of the same run the seat under test dies
that way 169 times where it does 193 times without it). And a commander's damage kills four times in ten less often,
before any block is added: the likely cause is that an attack which follows the most dangerous opponent spreads a
commander's damage over the table, where Forge's own keeps going at the same weak player. That is a guess from the counts.
