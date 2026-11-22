# Mistakes counted on the pool of twelve, 2026-11-22: the pool's first baseline

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
| turns on which a seat was sure to kill an opponent | 7,773 (6,192 in 2,000 games) |
| missed | 2,872, 37% (36%): 2,488 with nothing sent at that opponent, 384 with too little or stopped |
| ... the opponent was the last one (the kill wins the game) | 1,698 turns, 103 missed, 6% (5%) |
| ... the most dangerous of several (life + 2 x nonland permanents) | 1,705 turns, 251 missed, 15% (16%) |
| ... a less dangerous one while a more dangerous one lived | 4,370 turns, 2,518 missed, 58% (54%) |
| attacks that left at least a seat's life unblocked, or a commander's lethal damage | 5,400; the seat died that turn in 5,299 |
| deaths by a block not made | 153, 2.9% of the deaths in combat. Not comparable with the 6 of the second baseline: these logs carry a commander's damage in the block count (harness 0.4.3 and later), so a death a block on a commander would have stopped is counted here and was not there |
| deaths tapped out | 510, 9.6% (13.6%) |
| deaths on a turn a commander's damage on the seat reached 21 | 665, 12.5% (11.2%) |
| turns with an able attacker on which the seat attacked | 52% (57%); 43 to 70% by deck |
| turns with an opponent who could not block: attacked it | 29% of 28,625 (31%); attacked only opponents that could block 30% (34%); attacked nobody 40% (35%) |
| attackers at the opponent that looks most dangerous | with three opponents alive 50.8% of 71,644 (48.8%; a random opponent 33.3%), with two 58.1% of 35,025 (51.5%); at the player who went on to win 26.8% and 36.9% of the attackers of seats that did not (24.5%, 29.8%) |
| declarations that sent nothing at the most dangerous opponent | 15,980 of 35,994 (3,332 more with a tie for the most dangerous are left out): the one attacked had the lowest life at the table in 68%, the damage sure to get through was at least as much at the most dangerous one in 69%, and in 7,310 that held with the most dangerous one ahead by five or more |
| games without a winner | 31 of 2,400 (`docs/agents/unfinished.py`): 17 on the thirty-minute clock, 10 draws, 4 Forge exceptions; they took 9.5 of the 89.6 hours of play |

So the pool's pilots make the same mistakes at the same rates as the owner's ten did before their hooks: a sure kill of
the most dangerous opponent passed up on 15% of the turns it is there, half of the attackers at that opponent, an open
board attacked on three turns in ten. That was expected (what is counted is Forge's AI, and it is the same AI) and is now
measured.

## By deck (every seat the deck sat in, as the seat under test or as an opponent)

| Deck | Seat-games | Attacked, of turns it could | Open board attacked | Sure kill missed: the most dangerous of several | the last opponent | a lesser one | Deaths in combat | a block not made | tapped out | commander damage |
|---|---|---|---|---|---|---|---|---|---|---|
| Deep Clue Sea | 728 | 57% | 25% | 11 of 86 | 7 of 106 | 141 of 273 | 398 | 20 | 44 | 54 |
| Eldrazi Incursion | 828 | 47% | 29% | 36 of 263 | 7 of 217 | 204 of 389 | 390 | 7 | 37 | 63 |
| Elven Council | 820 | 50% | 26% | 6 of 95 | 4 of 115 | 225 of 385 | 489 | 10 | 49 | 53 |
| Enduring Enchantments | 808 | 57% | 33% | 19 of 239 | 4 of 230 | 226 of 464 | 352 | 20 | 32 | 52 |
| Goblin Storm | 840 | 45% | 30% | 28 of 165 | 2 of 107 | 233 of 407 | 527 | 10 | 48 | 67 |
| Hail, Caesar (go-wide) | 890 | 58% | 33% | 12 of 101 | 1 of 121 | 194 of 386 | 492 | 19 | 41 | 63 |
| Limit Break | 840 | 55% | 25% | 3 of 24 | 2 of 68 | 179 of 313 | 534 | 9 | 43 | 43 |
| Planeswalker Party | 734 | 53% | 36% | 15 of 94 | 20 of 141 | 92 of 196 | 404 | 0 | 27 | 18 |
| Quick Draw | 751 | 51% | 27% | 9 of 99 | 3 of 134 | 195 of 346 | 392 | 17 | 52 | 52 |
| Token Triumph | 855 | 43% | 27% | 23 of 208 | 7 of 181 | 274 of 479 | 486 | 18 | 46 | 91 |
| Tricky Terrain (go-wide) | 778 | 70% | 33% | 57 of 202 | 38 of 173 | 342 of 394 | 416 | 9 | 52 | 51 |
| Wretched Ranks | 728 | 45% | 28% | 32 of 129 | 8 of 105 | 213 of 338 | 419 | 14 | 39 | 58 |

Two rows stand out. Tricky Terrain passes up the kill that wins the game on 38 of 173 turns and the kill of the most
dangerous opponent on 57 of 202, several times any other deck's share. Its attack is its own (go-wide at the opponent with
the highest life, and only with two attackers or more), so these are the policy's misses and not Forge's; why it misses
them has not been read game by game. Planeswalker Party, whose attack is Forge's, passes up the winning kill on 20 of 141
turns. Both are what `"finish": "leader"` is for, and both are worth reading when the candidates have played.

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
table, because seven of these end within six minutes in a draw Forge declares (the six on the clock took thirty minutes each). Its fix is a limit a turn on the trigger rule
(`playbook/variants/eldrazi-incursion-limit.json`, harness 0.4.11), which finished all four of the deck's own broken tables
in replays; it plays beside the shipped arm on these tables with `ab-run` #59.
