# demo-data/ab

Paired A/B results for per-deck AI data (`runner/ab.py rollup`, DESIGN.md §19), one file per deck and run. The dashboard
does not read these yet; the numbers are summarised in DESIGN.md. Each file holds the arms' win rates with Wilson
intervals, the paired differences, and every game's seats, seed, winner and length.

`2026-11-10-ab-v1b/` is the v1 arms again on 100 new tables per deck (seed 20261110, `ab-run` #2; consecutive seeds share the
opponents of 69 of the 100 tables, in other seats and on other shuffles), and
`2026-11-10-ab-v1-pooled/` pools each deck's two seeds into one 200-table measurement (`runner/ab.py pool`, kind `ab-pool`:
games keyed by run seed and table, the same statistics).

`2026-11-10-ab-v2/` is the CI playbook measurement (`ab-run` #3, DESIGN.md §20: arms stock, playbook, playbookdata on Token Triumph,
Goblin Storm and Hail, Caesar, seed 20261110).

`2026-11-10-ab-mcmax/` is the CI check of desktop-strength Monte Carlo (`ab-run` #4, DESIGN.md §19: Tricky Terrain, arms stock, mcmax,
mcmaxdata, seed 20261120), the first run started by `runner/queue/ab-run.json`.

Dated `*-local/` directories hold 40- to 100-table checks played on a session's machine rather than in Actions, named by
deck and the arms they ran; the same format, smaller.

`2026-11-10-local/goblin-storm-playbook-v2-*.json` are Goblin Storm's playbook version 2 (cast rules, DESIGN.md §21) on the
same 40 tables with the attack aimed at the lowest life, the highest life and the biggest board; the three share one
stock arm, and each file's `note` and `attack_target` say which it is. The playbook file ships with the highest life.

`2026-11-10-ab-v3/` is the CI measurement of Goblin Storm's playbook version 2 (`ab-run` #5, DESIGN.md §21: cast rules and the
go-wide attack aimed at the highest life; arms stock and playbook, 200 tables, seed 20261140, snapshot 2026-11-10): 40 wins
against 18, the first difference in this directory whose interval excludes zero.

`2026-11-11-ab-v4/` is the leader-first attack alone on the two other go-wide decks (`ab-run` #6, DESIGN.md §22: Token Triumph and
Hail, Caesar under playbooks that hold an attack policy and nothing else, go-wide aimed at the highest life with the split; arms
stock and playbook, 200 tables each, seed 20261141, snapshot 2026-11-10): Token Triumph 39 wins against stock's 43, Hail, Caesar 32
against 34. Whom the seat attacks does not move either deck by itself. The stock arms are the baseline that the cast-rule
variants of both decks are paired with (same seed, playbook arm only).

`2026-11-11-ab-v5/goblin-storm.json` joins four candidates for Goblin Storm (`ab-run` #7, playbook arm only) with run #5's stock and
version-2 arms on the same 200 tables (`runner/ab.py join`, kind `ab-join`, DESIGN.md §22): the pressure attack wins 32 (damage per
loss 3) and 28 (2) where the shipped go-wide attack wins 40; two rules for a lost board on top of pressure, 28; Zada held until she
can be aimed at, on top of pressure, 39. Every candidate beats stock's 18; none beats the shipped file.

`2026-11-11-local/` are checks on the session's machine, each a join of arms that share one stock arm: Goblin Storm at 40 tables
under five attack settings and in 60 duels, Token Triumph's three cast-rule candidates in 60 duels, Hail, Caesar's two trigger-rule
candidates in 60 duels (`runner/ab.py --opponents 1`).

`2026-11-11-ab-v6/token-triumph.json` joins Token Triumph's three cast-rule candidates (`ab-run` #8, playbook arm only) with run #6's
stock and attack-only arms on the same 200 tables: the cast rules under the go-wide attack win 67 where stock wins 43 (+12.0 points,
47 discordant pairs against 23, exact test 0.006), under the pressure attack 60, with everything but the anthems cast after
combat 58. The first became the deck's shipped playbook (version 3).

`2026-11-11-ab-v7/hail-caesar.json` joins Hail, Caesar's four candidates (`ab-run` #9, playbook arm only) with run #6's stock and
attack-only arms on the same 200 tables: stock wins 34; the cast rules under the go-wide attack 41; with Caesar's attack trigger
taken every time 44, and 45 under the pressure attack; with the trigger taken only when there is a token to give up 51 (+8.5
points, 37 discordant pairs against 20, exact test 0.03). The last became the deck's shipped playbook (version 3), pending a
confirming run on new tables.

`2026-11-11-ab-v8/` holds `ab-run` #11, four requests played as one run. `goblin-storm.json`: the candidate with Zada held until she can
be aimed at, joined with run #5's arms on its tables (48 wins, version 2's 40, stock's 18; shipped as version 3 on a lean).
`token-triumph.json`: a follow-up to the shipped version on run #6's tables (66 against 67: nothing). `tricky-terrain.json`: the
deck's first playbook on 200 new tables with a stock arm of its own (seed 20261142): stock 30 wins, the playbook under go-wide 48
(+9.0 points, 33 discordant pairs against 15, exact test 0.013), 50 with key cards for the tutors, 37 under the pressure attack.

`2026-11-11-ab-v9/` holds `ab-run` #15. `hail-caesar.json` is the confirming run of Hail, Caesar's shipped playbook: 200 new games
(seed 20261143; 138 of the tables seat the same three opponents as a table of run #6, on other seats and shuffles, because the seeds
are two apart: DESIGN.md §22 finds nothing carried over): 42 wins against stock's 27, +7.5 points (37 discordant pairs against 22, exact test 0.07);
`hail-caesar-pooled.json` pools it with the tables that chose it (`ab.py pool`: 93 against 61 of 400, exact test 0.004).
`quick-draw.json` is Quick Draw's first candidate against stock (seed 20261144): 38 wins against 31, +3.5 points, exact test 0.42.
`science.json` (`ab-run` #14, seed 20261145) is Science!'s candidate against stock: 15 wins against 14.

`2026-11-11-ab-archive-check/goblin-storm.json` (`ab-run` #16, 40 tables, seed 20261146) is a check of the plumbing rather
than a measurement: the first run after `forge/fetch-forge.sh` learned to fetch a pinned snapshot from this repository's
release `forge-runtimes`. Both shards missed the Actions cache, downloaded the 11-10 archive, verified it and played: stock 4
wins of 40, Goblin Storm's shipped playbook (version 3) 8 (6 discordant pairs against 2). Fourteen of its tables seat the
opponents of a run #5 table (the seeds are six apart).

`2026-11-11-ab-v10/` holds `ab-run` #17, the confirming runs of the two shipped playbooks whose figures had come from the tables
that chose them, each against stock on 200 tables whose opponents the deck had not met (seeds ten and more from every earlier run of
the deck). `token-triumph.json` (seed 20261160): 56 wins against stock's 35, 28.0% against 17.5%, +10.5 points (38 discordant pairs
against 17, exact test 0.0065); it had been +12.0 where it was chosen. `goblin-storm.json` (seed 20261170): version 3 wins 48 against
stock's 18, 24.0% against 9.0%, +15.0 points (42 against 12, exact test 0.0001), the same count as on the tables that chose it over
version 2. `token-triumph-losses.json` and `goblin-storm-losses.json` are `runner/losses.py` on the same games (kind `ab-losses`):
for the seat under test in each arm, whether it was the first or the last out, its hand and board on its last own turn, who dealt
the last blow, the spells it aimed at opponents and the attackers it blocked (DESIGN.md §23). The per-game logs they were read
from are the run's shard artifacts (90 days).

`2026-11-11-local/four-bots-table.json` is not an A/B and not in the format above (kind `table-pair`): one table of the four decks
that have a shipped playbook, played on a session's machine on the same seeds (20261181 to 20261200) with every seat under its
playbook (20 games) and with every seat stock (17 games; three not played, and two of the 17 draws). The bots' games average 39.0
turns against 54.2 (9.75 rounds against 13.5 by turns over four; people 8.75). It measures how long a table of bots takes and says
nothing about who wins (DESIGN.md §23).

`2026-11-11-ab-v12/` (`ab-run` #19, seed 20261210, snapshot 2026-11-10): the first candidates judged at tables of bots. Each deck at 200
four-player tables whose three opponents are drawn from the four decks with a shipped playbook (`runner/leagues/bots-v1.json`), each
under it; the deck's own seat once under stock AI and once under its candidate. Counter Intelligence `charge` 20 wins against stock's 23
(-1.5 points, 95% -7 to +4, exact test 0.74); Deep Clue Sea `sleuth` 61 against 52 (+4.5, -4 to +13, 0.36); Food and Fellowship `eat` 29
against 28 (+0.5, -6 to +7, 1.0); Planeswalker Party `guff` 57 against 57 (0.0, -8 to +8). `planeswalker-party-guff-forgeattack.json` is
the same rules with Forge's own attack on the same tables, playbook arm only, and `planeswalker-party-join.json` the three arms side by
side (kind `ab-join`): 69 wins, +6.0 on stock (-2 to +14, 0.20) and +6.0 on the go-wide version (21 discordant pairs against 9, 0.043).
None of the four clearly beats its stock pilot; all four had gained one to three turns in goldfish (DESIGN.md §27).

`2026-11-11-ab-v11/` (`ab-run` #20, seed 20261200, snapshot 2026-11-10): the four shipped bots among bots. Each deck at 200 four-player
tables whose three opponents are the other three bot decks, each under its shipped playbook; the deck's own seat once under stock AI and
once under its shipped playbook. Goblin Storm 30 wins against its stock pilot's 11 (+9.5 points, 95% +4 to +15, exact test 0.0013);
Hail, Caesar 36 against 25 (+5.5, -1 to +12, 0.13); Token Triumph 83 against 75 (+4.0, -4 to +12, 0.42); Tricky Terrain 40 against 32
(+4.0, -4 to +12, 0.37). Every playbook is ahead of its stock pilot; only Goblin Storm's lead is clear of noise. Token Triumph wins
37.5% of these tables under stock AI as well: at this table the deck is strong whoever pilots it (DESIGN.md §27).

`2026-11-12-ab-v13/` (`ab-run` #21, seed 20261200): answer rules for the four shipped bots, playbook arm only on the tables of `ab-run` #20
(`2026-11-11-ab-v11/`). `<deck>-answers.json` is the run's rollup and `<deck>-join.json` the three arms on the same 200 tables (kind
`ab-join`: stock pilot, shipped playbook, answers). Hail, Caesar 55 wins against the shipped version's 36 (+9.5 points, 95% +5 to +14,
exact test 0.0003); Goblin Storm 38 against 30 (+4.0, +1 to +7, 0.039); Tricky Terrain 44 against 40 (+2.0, -3 to +7, 0.58); Token
Triumph 80 against 83 (-1.5, -6 to +3, 0.65). Hail, Caesar's and Goblin Storm's became version 4 of their shipped playbooks.

`2026-11-12-ab-v14/` (`ab-run` #22, seed 20261220): two candidates that had only met stock tables, at 200 tables of bots each, stock pilot
against candidate. Quick Draw `spells` 39 wins against 32 (+3.5 points, 95% -3 to +10, exact test 0.40); Science! `lab` 4 against 7
(-1.5, -4 to +1).

`2026-11-12-ab-v15/` (`ab-run` #23 to #25, seeds 20261210, 20261230 and 20261200; all queued before the pool's Hail, Caesar, Goblin
Storm and Tricky Terrain changed version, so they play the pool as it was): the attack question. A deck's rules with the go-wide attack
and with Forge's own attack on the same 200 tables of bots, beside the stock pilot. `<deck>-<name>.json` and `<deck>-<name>-forgeattack.json`
are the runs' rollups, `<deck>-join.json` the three arms side by side (kind `ab-join`; arms `stock`, `gowide`, `forgeattack`); for the
decks whose stock and go-wide arms were played earlier those arms come from `2026-11-11-ab-v12/` and `-v11/`. Wins of 200, stock pilot /
go-wide / Forge's attack: Counter Intelligence 23 / 20 / 22; Deep Clue Sea 52 / 61 / 76; Food and Fellowship 28 / 29 / 30; Planeswalker
Party 57 / 57 / 69 (in `-v12/`); Goblin Storm (version 3) 11 / 30 / 42; Token Triumph (version 3) 75 / 83 / 93; Hail, Caesar (version 3)
25 / 36 / 41; Tricky Terrain (version 5) 32 / 40 / 59; Elven Council 15 / 39 / 40; Wretched Ranks 35 / 31 / 40; Enduring Enchantments
62 / 61 / 62; Eldrazi Incursion 62 / 52 / 64; Limit Break (on the code with the equip check) 24 / 28 / 47. Thirteen decks, thirteen times
at least as many wins with Forge's attack: 501 / 567 / 685 of 2,600 tables (DESIGN.md §27 has the intervals and the exact tests).

`2026-11-12-ab-v16/` (`ab-run` #26, seed 20261240): the first round on the pool of twelve (`runner/leagues/bots-v2.json`). `<deck>.json`
is a deck at 200 tables whose three opponents are drawn from the other eleven bots, each under its shipped playbook, its own seat once
under stock AI and once under its shipped playbook. Wins of 200, stock pilot / shipped playbook: Goblin Storm 20 / 47 (+13.5 points,
exact test 0.0001); Token Triumph 43 / 65 (+11.0, 0.0032); Enduring Enchantments 40 / 62 (+11.0, 0.014); Hail, Caesar 28 / 45 (+8.5,
0.03); Deep Clue Sea 42 / 58 (+8.0, 0.076); Quick Draw 34 / 50 (+8.0, 0.052); Tricky Terrain 29 / 40 (+5.5, 0.20; 18 of the playbook
arm's games ran to the clock); Elven Council 18 / 27 (+4.5, 0.20); Limit Break 34 / 39 (+2.5, 0.60); Planeswalker Party 44 / 44;
Eldrazi Incursion 48 / 46 (-1.0, 0.89); Wretched Ranks 39 / 34 (-2.5, 0.58). All twelve: 419 / 557 of 2,400. Five side arms on the same
tables, playbook arm only, are the same rules with the go-wide attack (`goblin-storm-answers.json`, `hail-caesar-answers.json`,
`tricky-terrain-answers.json`, `token-triumph-gowide.json`, `quick-draw-spells.json`), and `<deck>-join.json` sets the three arms side by
side (kind `ab-join`; arms `stock`, `shipped`, `gowide`). Go-wide against the shipped version, which leaves the attack to Forge: Goblin
Storm 56 against 47 (+4.5, 30 discordant pairs against 21, exact test 0.26); Hail, Caesar 66 against 45 (+10.5, 36 against 15, 0.0046);
Tricky Terrain 58 against 40 (+9.0, 39 against 21, 0.027); Token Triumph 54 against 65 (-5.5, 17 against 28, 0.14); Quick Draw 43
against 50 (-3.5, 20 against 27, 0.38). DESIGN.md §28 reads them. The league of the same twelve (`league-run` #3, seed 20261250) is
`demo-data/runs/2026-11-12-bots-v2-snapshot-2026-11-10-s20261250-bots/`.

`2026-11-14-ab-v17/`: the owner's table and the pool's answer rules (DESIGN.md §30), nine Actions runs of 2026-11-14, all at tables
whose three opponents are drawn from the twelve bots of `bots-v2` under their shipped playbooks of 2026-11-13.

The first exam of the ten engine-only candidates for the owner's precons (`ab-run` #27 to #30; seeds 20261260, 20261280, 20261290):
`<deck>-<name>.json` has the stock pilot and the candidate with its go-wide attack, `<deck>-<name>-forgeattack.json` the same rules with
the attack left to Forge on the same tables (playbook arm only), and `<deck>-join.json` the three side by side (kind `ab-join`; arms
`stock`, `gowide`, `forgeattack`). Wins of 200 as stock / go-wide / Forge's attack: Blight Curse `wretch` 46 / 41 / 44; Veloci-Ramp-Tor
`stampede` 85 / 80 / 91; Mutant Menace `mothman` 46 / 55 / 63 (Forge's attack on stock +8.5 points, exact test 0.060); Squirreled Away
`acorns` 46 / 47 / 57; Revenant Recon `mirko` 47 / 55 / 53; Blood Rites `demons` 66 / 78 / 83 (+8.5, 0.089); Death Toll `winter`
37 / 59 / 51 (go-wide on stock +11.0, 95% +2 to +20, 0.018); Miracle Worker `veil` 64 / 55 / 59; Ahoy Mateys `crew` 36 / 52 / 62
(go-wide +8.0, 0.048; Forge's attack +13.0, +5 to +21, 0.002); Deadly Disguise `veil` 27 / 20 / 25. Over the 2,000 tables 500 / 542 /
588; between the two attacks 247 discordant tables against 201 for Forge's attack (exact test 0.033), no single deck clear of noise.
None of these candidates is shipped: every one casts its removal and its large threats far less than its stock pilot on the same
tables, and each deck ships from the exam of its second pass (`<deck>-answers.json`, `ab-run` #36 to #39, to be collected into a
directory of their own).

`hail-caesar.json` and `tricky-terrain.json` (`ab-run` #27, seed 20261270): versions 6 and 8, the go-wide attack back, against their
stock pilots on tables that did not choose the attack: Hail, Caesar 54 wins against 30 (+12.0, 95% +4 to +20, exact test 0.0032),
Tricky Terrain 48 against 34 (+7.0, -0 to +14, 0.081).

`<deck>-<name>-forge.json` and `<deck>-forge-join.json` (`ab-run` #34, seed 20261260, the tables of #27; arms `stock`, `gowide`,
`forgeattack`, `forge`): the trial of the `forge` rule, put in mechanically after the commander's rule of the first four go-wide
candidates. With the rule against without it: Blight Curse 52 against 41 (+5.5, exact test 0.18), Mutant Menace 53 against 55, Squirreled
Away 45 against 47, Ahoy Mateys 63 against 52 (+5.5, 0.18); 213 against 195 over the 800 tables (0.23).

The answer rules of the nine pool decks that had none (`ab-run` #31 to #33 and #35, seed 20261300): `<deck>.json` is the shipped
playbook of 2026-11-13 (playbook arm only), `<deck>-answers.json` the candidate on the same tables (`token-triumph-answers2.json` for
Token Triumph), `<deck>-join.json` the two side by side (arms `shipped` and `answers`, or `answers2`). Candidate against shipped, wins
of 200: Deep Clue Sea 71 against 67; Eldrazi Incursion 63 against 64; Elven Council 32 against 34; Enduring Enchantments 63 against 52
(+5.5, 0.16); Limit Break 51 against 44; Planeswalker Party 52 against 42 (+5.0, 0.13); Quick Draw 58 against 59; Token Triumph 65
against 57 (+4.0, 0.17); Wretched Ranks 38 against 27 (+5.5, 95% +0 to +11, 0.061). Summed 493 against 446 of 1,800 (166 discordant
tables against 119, exact test 0.0063), and the cards the new rules name cast in 77% of the games they were drawn against 34%
(`demo-data/playtest/2026-11-14/pool-answers/`). All nine shipped on 2026-11-14 as the next version of each deck; none has met its
stock pilot yet.

`2026-11-14-ab-v18/`: the second pass of the owner's ten precons (DESIGN.md §30; `ab-run` #36 to #39, seed 20261310, opponents drawn
from the twelve bots of `bots-v2` under their playbooks of 2026-11-13). `<deck>-answers.json` has the stock pilot and the second-pass
candidate with its go-wide attack, `<deck>-answers-forgeattack.json` the same rules with the attack left to Forge on the same tables
(playbook arm only), `<deck>-join.json` the three side by side (kind `ab-join`; arms `stock`, `gowide`, `forgeattack`). Wins of 200
as stock / go-wide / Forge's attack, and the arm that shipped against the stock pilot: Blight Curse 45 / 66 / 69 (Forge's attack
+12.0 points, 95% +4 to +20, exact test 0.0088); Veloci-Ramp-Tor 79 / 86 / 87 (+4.0, -5 to +13, 0.44); Mutant Menace 51 / 55 / 68
(+8.5, +1 to +16, 0.0498); Squirreled Away 49 / 54 / 56 (+3.5, -4 to +11, 0.44); Revenant Recon 60 / 59 / 70 (+5.0, -4 to +14,
0.31); Blood Rites 66 / 86 / 91 (+12.5, +4 to +21, 0.0046); Death Toll 43 / 63 / 65 (+11.0, +3 to +19, 0.0115); Miracle Worker
48 / 43 / 48 (level); Ahoy Mateys 37 / 72 / 64 (go-wide +17.5, +9 to +26, 0.0001); Deadly Disguise 20 / 22 / 29 (+4.5, -2 to +11,
0.21). Over the 2,000 tables 498 / 606 / 647, and 655 for the arm that shipped. All ten shipped on 2026-11-14 with the better of
their two attacks on these tables (Forge's for nine, go-wide for Ahoy Mateys), by a rule fixed before the runs were read: ahead of
the stock pilot, or behind by no more than two tables.

Two shard jobs of these runs were lost with their runners and their tables were played on the session's machine from the run's own
commit: one shard of five of Miracle Worker's Forge's-attack arm (every fifth table, 40 tables) and one shard of ten of
Veloci-Ramp-Tor's stock and go-wide arms (every tenth table, 20 tables in each). For those two decks the three files here were rolled
up from the Actions shards and the replayed shard together; `miracle-worker-answers-forgeattack-actions.json` (160 tables: 39 wins,
where the stock pilot won 42 of the same tables) and `veloci-ramp-tor-answers-actions.json` (180 tables: stock 69, go-wide 81) are
the runs' own rollups of the cut arms. Every other file is the run's own rollup (Blood Rites and Revenant Recon: rolled up from
`ab-run` #38's shard artifacts before its rollup job had run). The card check of each deck's three arms is in
`demo-data/playtest/2026-11-14/second-pass/`, the goldfish pairs of the shipped files in `demo-data/goldfish/2026-11-14/`.

`2026-11-15-ab-v19/`: the round of the twelve on the pool as it is since 2026-11-14 (DESIGN.md §32; `ab-run` #40, seed 20261320,
opponents drawn from the other eleven decks of `bots-v2` under their shipped playbooks). `<deck>.json` has the stock pilot and the
shipped playbook on the same 200 tables; the tables chose nothing. It is the first time the nine versions with answer rules of
2026-11-14 met their stock pilots. Wins of 200 as stock pilot / playbook: Hail, Caesar 28 / 59 (+15.5 points, 95% +9 to +22, exact
test under 0.0001); Eldrazi Incursion 34 / 59 (+12.5, +5 to +20, 0.0026); Planeswalker Party 42 / 65 (+11.5, +3 to +20, 0.011);
Goblin Storm 19 / 34 (+7.5, +1 to +14, 0.032); Deep Clue Sea 42 / 57 (+7.5, -0 to +15, 0.077); Tricky Terrain 33 / 47 (+7.0, -0 to
+14, 0.087); Token Triumph 45 / 58 (+6.5, -1 to +14, 0.11); Enduring Enchantments 45 / 58 (+6.5, -2 to +15, 0.17); Limit Break
29 / 37 (+4.0, -3 to +11, 0.31); Quick Draw 35 / 42 (+3.5, -4 to +11, 0.43); Elven Council 23 / 28 (+2.5, -4 to +9, 0.52); Wretched
Ranks 30 / 29 (-0.5, -7 to +6, 1.0). Over the 2,400 tables 405 / 573: 16.9% against 23.9% (423 tables only the playbook won
against 255 only the stock pilot won). By the rule fixed before the round was read (ahead or level stays) all twelve stay.

`2026-11-15-ab-v20/`: the round of the owner's ten at the owner's table (DESIGN.md §32; `ab-run` #42, seed 20261350, opponents drawn
from the other nine decks of `owners-table-v1` under their shipped playbooks). `<deck>.json` has the stock pilot and the shipped
playbook on the same 200 tables; the tables chose nothing, so this is the confirming run of the ten, at the table they are for. Wins
of 200 as stock pilot / playbook: Ahoy Mateys 34 / 65 (+15.5, 95% +7 to +24, exact test 0.0004); Death Toll 34 / 56 (+11.0, +3 to
+19, 0.0092); Mutant Menace 28 / 40 (+6.0, -1 to +13, 0.13); Blight Curse 41 / 53 (+6.0, -2 to +14, 0.19); Squirreled Away 27 / 36
(+4.5, -2 to +11, 0.25); Blood Rites 72 / 75 (+1.5, -7 to +10, 0.83); Miracle Worker 51 / 52 (+0.5, -8 to +9, 1.0); Veloci-Ramp-Tor
68 / 68; Deadly Disguise 20 / 18 (-1.0, -6 to +4, 0.86); Revenant Recon 64 / 48 (-8.0, -17 to +1, 0.093). Over the 2,000 tables
439 / 511: 22.0% against 25.6% (363 tables only the playbook won against 291 only the stock pilot won, exact test 0.0055). By the
same rule all ten stay; Revenant Recon is behind, inside noise, and goes first into the next pass. The exam each of the ten shipped
on is the row above (`2026-11-14-ab-v18/`): there the shipped arms were 157 tables ahead of the stock pilots over the ten decks, here
72, which is what choosing the better of two attacks on the tables that measured it costs, and another table.

`2026-11-15-ab-v21/`: the trial of the `forge` rule's wait option (DESIGN.md §32; `ab-run` #41, seed 20261340, opponents drawn from
`bots-v2` under their shipped playbooks, harness 0.3.3). `<deck>-<name>-forge.json` has the stock pilot and the first go-wide
candidate with a `forge` rule after its commander's rule; `<deck>-<name>-forgewait.json` the same file with `"wait": "main2"` on that
rule (playbook arm only); `<deck>-wait-join.json` the three side by side (kind `ab-join`; arms `stock`, `forge`, `forgewait`). Wins of
200 as stock / forge / forgewait: Blight Curse `wretch` 43 / 42 / 49 (the wait on the rule without it +3.5, 95% -4 to +11, exact test
0.42); Mutant Menace `mothman` 41 / 60 / 55 (-2.5, 0.50); Squirreled Away `acorns` 55 / 54 / 48 (-3.0, 0.44); Ahoy Mateys `crew`
32 / 63 / 59 (-2.0, 0.63). Over the 800 tables 171 / 219 / 211; the wait won 81 tables the rule without it lost and lost 89 it won
(exact test 0.59): no difference in wins. What it does to the cards is in `demo-data/playtest/2026-11-15/wait-trial/`: the cards no
rule names are cast as often as the stock pilot casts them again (72% of the games drawn against the stock pilot's 70% and the plain
`forge` rule's 62%), and the cards the rules below the `forge` rule name lose as much (70% against 76%). No shipped playbook takes
the option on this trial.

`2026-11-15-ab-v22/`: the third pass at the owner's table (DESIGN.md §33; `ab-run` #43, seed 20261360, opponents drawn from the other
nine decks of `owners-table-v1` under their shipped playbooks of 2026-11-14, harness 0.3.4). `<deck>.json` is the shipped playbook
(playbook arm only), `<deck>-<variant>.json` the candidate on the same tables, `<deck>-join.json` the two side by side (kind
`ab-join`; arms `shipped` and the variant's name). Candidate against shipped, wins of 200: Blight Curse `curve` 35 against 35;
Revenant Recon `curve` 56 against 55 (+0.5 points, 95% -5 to +6, exact test 1.0); Squirreled Away `pulse` 32 against 30 (+1.0, -2 to
+4, 0.75); Mutant Menace `atomize` 43 against 42 (+0.5, -2 to +3, 1.0); Blood Rites `newblood` 68 against 65 (+1.5, -2 to +5, 0.55);
Veloci-Ramp-Tor `raptor` 76 against 74 (+1.0, -4 to +6, 0.84). Summed 310 against 301 of 1,200 (57 tables only the candidate won
against 48). The rule fixed before the run asked for two things: level with or ahead of the shipped arm, which all six are, and the
change doing what it was for (`demo-data/playtest/2026-11-15/third-pass/check.txt`). The four that cast a card neither pilot had
cast do: Maelstrom Pulse in 49 of the 53 games it was drawn, Atomize in 26 of 30, New Blood in 47 of 49, Marauding Raptor in all 68;
they shipped on 2026-11-15 as the next version of each deck. The two `curve` candidates do not: the cards their decks cast less
than their stock pilots are cast 3.3 points more often (Blight Curse) and 0.9 points more often (Revenant Recon) where the rule asked
for ten; they did not ship. The aimed rules' counters, summed over the three candidates' 200 games each: 122 aimed casts, 101 at the
opponent that looked most dangerous, 21 at the next one that had something worth aiming at; none fizzled.

`2026-11-15-ab-v23/`: two follow-ups to the third pass (DESIGN.md §33; `ab-run` #44, seed 20261370, opponents drawn from the other
nine decks of `owners-table-v1` under their shipped playbooks of 2026-11-15, the four versions of that day among them). `<deck>.json`
is the shipped playbook (playbook arm only), `<deck>-<variant>.json` the candidate on the same tables, `<deck>-join.json` the two
side by side (arms `shipped` and the variant's name). Blight Curse `threats` (its removal and its large creatures above the engine
pieces): 39 wins of 200 against the shipped version's 37 (+1.0 points, 95% -5 to +7, exact test 0.87), and the nineteen cards
version 2 casts less than its stock pilot cast in 60.6% of the games they were drawn against 50.4% on the same tables, +10.1 points:
by the rule fixed before the run it shipped as version 3 on 2026-11-15. Revenant Recon `deluge` (Toxic Deluge by a rule, two
creatures named, no rule moved): 47 against 52 (-2.5 points, -7 to +2, 0.38), five tables behind where the rule allowed two; Toxic
Deluge was cast in 18 of the 52 games it was drawn. It did not ship. The card check is
`demo-data/playtest/2026-11-15/follow-ups/check.txt`.


`2026-11-20-ab-v24/`: the exam of `finish`, the first hook written for a counted mistake (DESIGN.md §34; `ab-run` #45, run id
44801095534, commit 772c943, harness 0.4.0, seed 20261380, opponents drawn from the other nine decks of `owners-table-v1` under
their shipped playbooks). `<deck>.json` is the shipped playbook (playbook arm only), `<deck>-finish.json` the same playbook with
`finish` on its attack on the same 200 tables, `<deck>-join.json` the two side by side (arms `shipped` and `finish`),
`reading.json` the rule applied deck by deck with the seat under test's sure kills in each arm (`runner/mistakes.py --deck`),
`first-difference.json` every table filed by the first event at which its two games differ (`docs/agents/first_difference.py`).
`finish` against shipped, wins of 200: Ahoy Mateys 63 against 60 (+1.5 points, 95% -3 to +6, exact test 0.69); Blight Curse 43
against 43; Blood Rites 70 against 76 (-3.0, -7 to +1, 0.24); Deadly Disguise 14 against 14; Death Toll 52 against 51 (+0.5, 1.0);
Miracle Worker 65 against 64 (+0.5, 1.0); Mutant Menace 41 against 47 (-3.0, -6 to -0, 0.070); Revenant Recon 44 against 43 (+0.5,
1.0); Squirreled Away 27 against 31 (-2.0, -4 to +0, 0.22); Veloci-Ramp-Tor 86 against 83 (+1.5, -3 to +6, 0.68). Summed 505 against
512 of 2,000 (56 tables only `finish` won against 63, exact test 0.58). The seat under test passed up 527 of the 1,558 turns on
which it was sure to kill an opponent under the shipped playbooks (34%) and 55 of 1,317 with `finish` (4%, 53 of them kills it
went for and did not get). By the rule fixed before the run seven candidates pass both halves and three are behind by more than
two tables (Blood Rites, Mutant Menace, Squirreled Away). None shipped, because of what the tables show when they are read by where
the two games first differ, a reading made after the result: 1,406 of the 2,000 pairs are the same game to the last event and 137
differ for a reason that is not the hook (10 against 10). Where the hook made the difference and the opponent it killed was the most
dangerous one alive (83 tables), `finish` alone won 14 and the shipped playbook alone 2 (exact test 0.0042); where it was a less
dangerous opponent while a more dangerous one lived (358 tables), 30 against 50 (0.033), and the seat was out of the game before
its own next turn on 91 of those tables where the shipped playbook's seat, from the same position, was on 59. The two halves
differ beyond chance (Fisher's exact test 0.0003). So the hook as it was built does two opposite things and the count of "kills
not taken" held two different things; the narrower hook that takes only the first kind goes to tables of its own.


`2026-11-21-ab-v25/`: eleven exams on the same 200 tables a deck (DESIGN.md §35; `ab-run` #46 to #56, run ids 44843287002, 44847661878, 44851801108, 44878980790, 44883447160, 44885953698, 44889581983, 44891801343, 44895074935, 44895619944 and 44928776328; harness 0.4.1 to 0.4.10, seed 20261390, opponents drawn from the other nine decks of `owners-table-v1` under the playbooks shipped on 2026-11-15). `<deck>.json` is the shipped playbook of that day (playbook arm only; #46), `<deck>-<name>.json` the same deck under a candidate, `<deck>-join.json` every arm of the deck on the same tables (`shipped` and each candidate, and each pair of them). The candidates: five hooks, each by itself on all ten decks (`leader`, #46; `aim`, #47; `block`, #48; `swing` and `open`, #49), two guard arms on top of `leader` (`leaderguard`, `leadertable`, #46), and nine candidates that are one deck's own rules (`blight-curse-covenant` and `blood-rites-pact`, #50; `deadly-disguise-kaust`, #51; `veloci-ramp-tor-run` and `mutant-menace-mutation`, #52; `blight-curse-counters`, #53; `blight-curse-engine`, #54; `mutant-menace-finisher`, #55; `miracle-worker-cap`, #56). `hook-exam.json` is what `docs/agents/hook_exam.py` read for nine pairs of arms (wins, the seat under test's mistakes and whom its attackers went at in each arm, the hooks' counters), `first-difference-<base>-<candidate>.json` every table of a pair filed by the first event at which its two games differ, `decks/deck-exam-*.json` the single-deck candidates beside their shipped arm (`docs/agents/deck_exam.py`). The shard artifacts were checked against their names, seed and start date before anything was read (`docs/agents/verify_shards.py`; one deck's base arm had been fetched from the wrong run and was fetched again), and the 88 rollups made from the shards agree with the official ones.
Wins of 2,000 over the ten decks: shipped 498, `leader` 516, `swing` 511, `open` 510, `aim` 497, `block` 497; `leaderguard` 519 and `leadertable` 518 beside `leader`'s 516. By the rules fixed before the runs all five hooks hold. `leader`: 32 tables only it won against 14 (exact test 0.011), 21 against 5 where the kill of the most dangerous opponent is the first difference, and that kill missed on 12 of 266 turns where the shipped arms missed it on 38 of 279. `swing`: 89 against 76 (0.35), 61.2% of the seat's attackers at the most dangerous opponent with three alive where 47.7% were. `open`: 131 against 119 (0.49), an opponent who cannot block attacked on 62% of the turns it could be where it was on 30%; 162 deaths tapped out against 143. `aim`: 22 against 23, and of the 159 casts that differ first 148 went at the most dangerous opponent. `block`: 10 against 11; on the 32 tables it changed first the seat was out that turn on 3 where it was on all 32, and won seven. Neither guard met its rule (out before its own next turn at most two thirds as often on the tables it changed: 12 against 15 of 42, 28 against 38 of 243), and no guard was to ship from this run; holding back did not cost wins. By deck each hook went into the next version unless its arm was behind the shipped arm by more than two tables: `leader` and `swing` for all ten, `aim` for nine (not Revenant Recon, 51 against 55), `block` for eight (not Blood Rites, 57 against 60, nor Miracle Worker, 40 against 43), `open` for six (Ahoy Mateys 71 against 60, Blight Curse 44 against 41, Blood Rites 77 against 60, Death Toll 53 against 52, Miracle Worker 41 against 43, Mutant Menace 44 against 40; not Deadly Disguise 20 against 28, Revenant Recon 52 against 55, Squirreled Away 35 against 40, Veloci-Ramp-Tor 73 against 79). The decks' own rules, wins of 200 beside the shipped arm: `covenant` 42 against 41 (Fire Covenant cast in 36 of the 56 games drawn, from none), `pact` 63 against 60 (Pact of the Serpent in 29 of 48, from none), `kaust` 29 against 28 (the ability used 210 times, from 12), `finisher` 40 against 40 (Biomass Mutation cast in 12 games, from 4), `engine` 43 against 41 (three abilities used 121 times, from none): all pass. `run` 79 against 79 with Kessig Wolf Run used by the rule 21 times where 40 were asked: it does not pass. The two candidates withdrawn before their runs, as measured: `mutation` 40 against 40, `counters` 44 against 41. `cap` (#56) 47 against 43 (five tables against one, exact test 0.22) with one game without a winner where the shipped arm left nine: it passes, and all eight tables the chain had broken finished (four of them won). What shipped from all this is in `playbook/bots.json` (each row's `version_tables` names the parts of its join) and in CLAUDE.md, The owner's table: every part was played by itself, no two together.


`2026-11-22-ab-v26/`: the confirming run of the next versions at the owner's table (DESIGN.md §36; `ab-run` #57, run id 44934245433, commit 473a1b1, harness 0.4.10; seed 20261410, tables that chose nothing). Each of the ten decks on the same 200 tables under the version it had until 2026-11-21 (`<deck>-before.json`), under its next version (`<deck>.json`: the hooks and the deck's own rules that had each passed by itself in `2026-11-21-ab-v25/`) and under the next version with the table guard (`<deck>-guard.json`); the opponents are drawn from the other nine under their next versions, so every seat has the hooks. `<deck>-join.json` lines the three arms up as `before`, `shipped` and `guard`. `hook-exam.json` (`docs/agents/hook_exam.py`) has each deck's wins, pairs, counted mistakes and hook counters; `first-difference-before-shipped.json` and `first-difference-shipped-guard.json` file every table by the first event at which its two games differ; `decks/deck-exam-*.json` are the five decks' own rules, version before beside next version (`docs/agents/deck_exam.py`). All 150 shard artifacts were fetched and checked against seed and pool (`docs/agents/verify_shards.py`); the rollups here are the run's own.
Wins of 2,000: the versions before 468, the next versions 499, with the guard 496. By the rules fixed before the run: the next versions stand (186 tables only they won against 155, exact test 0.10) and no deck goes back (none is behind with an exact test below 0.05; Blood Rites is ahead, 72 against 56, 0.033; Blight Curse is 42 against 48, 0.45). The hooks do together what each did alone: the sure kill of the most dangerous of several opponents missed on 12 of 341 turns where the versions before missed it on 42 of 282, and 11 tables against 1 where that kill is the first difference; 57.7% of the seat's attackers at that opponent with three alive, from 48.1%; an opponent who cannot block attacked on 66.8% of the turns it could be in the six decks with that hook, from 33.3%; 138 removal triggers moved; the blocks added 17 times in 1,600 games, and on the 8 tables they changed first the seat was out that turn on none where it was on 7. The guard holds: 38 tables against 41 beside the next versions (exact test 0.82) and 169 deaths with the seat's own creatures tapped against 193 (the rule asked for nine tenths or fewer); on the 290 tables it changed first the seat was out before its own next turn on 23 where it was on 44. The guard arm is each deck's following version, and all ten shipped on 2026-11-22. The decks' own rules in the combination: Fire Covenant cast in 33 of the 41 games it was held, Pact of the Serpent in 20 of 38, Kaust's ability used 155 times, three Blight Curse abilities 104 times, Biomass Mutation cast in 6 games of 40, each from none or nearly none; Miracle Worker's cap left no game without a winner where the uncapped version in the same seat left 8. Games without a winner: 6 of 2,000 under the next versions (two of them Blight Curse's chain with Hapatra), 16 under the versions before, 6 with the guard.


`2026-11-22-ab-v27/`: the hooks at the pool's tables (DESIGN.md §36 for the base arms, §38 for the exam; `ab-run` #58, run id 44934264368, commit 50fb281, harness 0.4.10, and `ab-run` #59, run id 44976505627, commit b12112e, harness 0.4.11; seed 20261400 on `runner/leagues/bots-v2.json`, opponents drawn from the other eleven under the playbooks shipped until 2026-11-22, none with a hook; 200 tables a deck, playbook arm only). `<deck>.json` is the deck under its shipped playbook (#58), `<deck>-hooks.json` with the four hooks that are not a matter of the deck (the leader's kill, the attack aimed, the removal triggers aimed, the blocks) and `<deck>-hooksopen.json` with free damage as well (#59); `<deck>-join.json` lines the three up on the same tables as `shipped`, `hooks` and `hooksopen` (`runner/ab.py join --against shipped`). `eldrazi-incursion-limit.json` is that deck's version 2 with its commander's trigger paid for at most three times a turn. `hook-exam.json`, the four first-difference files, `kill-force.json` and `decks/deck-exam-eldrazi-incursion-limit.json` are the exam files. All 37 entries' shards were fetched and checked against seed, date and pool; the rollups are the runs' own.
Wins of 2,400: shipped 597, with the hooks 645 (158 tables only the hooks won against 110, exact test 0.0040), with free damage too 665 (269 against 201, 0.0020). Read by the rules fixed before either run: the arm with free damage holds (an opponent who cannot block attacked on 61.0% of the turns from 29.8%); the arm with the four hooks alone does not, by the letter, on one clause of three (the sure kill of the most dangerous opponent missed on 6.3% of the turns it is there from 11.5%, where at most half was asked; its attackers at that opponent 63.5% from 51.4%). So seven decks whose arm with free damage won more tables than their arm without shipped that arm on 2026-11-22 (Goblin Storm, Deep Clue Sea, Limit Break, Quick Draw, Wretched Ranks, Enduring Enchantments, and Eldrazi Incursion with its limit) and five keep their playbooks (Token Triumph, Hail, Caesar, Tricky Terrain, Planeswalker Party, Elven Council). The same kill hook is in both arms, so the split is the rules' doing and not a finding about the five (262 wins of 1,000 with the hooks against 253 without); they get an exam of their own (`ab-run` #62). Free damage on top of the hooks is level over the twelve (205 tables against 185, 0.34), so the seven decks' lead with it (136 against 93) is the better of two on the tables that measured it.
`kill-force.json` is a reading after the result: the missed kills of the most dangerous opponent by what the declared attack was worth. Not gone for, or an attack the defender's best blocks stop: 48 turns of 433 shipped, 15 of 460 with the hooks, 15 of 459 with free damage too. Lethal as declared and the opponent survived (life gained or damage prevented in combat): 2, 14 and 13. The threshold had no room for the second kind.
`eldrazi-incursion-limit.json`: 76 wins against the shipped arm's 77 (9 tables against 10); one game without a winner where the shipped arm left four, and the four tables the chain had broken all finished; the limit reached 241 times on 94 tables. It passed its rule and is in the deck's version 3 together with the arm with free damage (two parts not played together before).
The 2,400 games of the shipped arms are also the pool's first count of mistakes (`demo-data/mistakes/2026-11-22/`): 31 games without a winner there, 14 of them the Eldrazi chain wherever that deck sat; 28 and 26 in the two candidate arms.


`2026-11-22-ab-v28/`: the six decks of the owner's table that lacked a hook (DESIGN.md §37; `ab-run` #60, run id 44977470125, commit c8cf4fa, harness 0.4.11; seed 20261410, the tables of #57). `<deck>-full.json` is the deck's guard arm of #57 plus what a rule of 2026-11-21 had left out of it (the blocks for Blood Rites and Miracle Worker; free damage for Deadly Disguise, Squirreled Away and Veloci-Ramp-Tor; free damage and the trigger aim for Revenant Recon); `<deck>-guard.json` is that guard arm, copied from `2026-11-22-ab-v26/`; `<deck>-join.json` lines up `before`, `shipped`, `guard` (all three from #57) and `full` on the same 200 tables (`runner/ab.py join --against guard`). `hook-exam.json` and `first-difference-guard-full.json` are the exam files. All 30 shard artifacts were fetched and checked against seed and pool; the rollups are the run's own.
Wins of 1,200: the guard arms 299, the new arms 318 (69 tables only the new arm won against 50, exact test 0.10); no deck behind. By the rule fixed before the run each hook also had to act: an opponent who cannot block is attacked on 60.5% of the turns it could be in the four decks that got free damage, from 34.4% (ten points were asked, deck by deck: 19.6 to 35.8); the blocks were added on 13 occasions in the two decks that got them, their deaths by a block not made went from 12 to none, and on the 14 tables where a block is the first difference the seat was out that turn on none where it was on 12. All six shipped on 2026-11-22 as their following versions, so every deck of the owner's table now has every hook.
`blight-curse-limit.json` (in `ab-run` #59, run id 44976505627, on the same tables) is Blight Curse's version 5 with Flourishing Defenses' token accepted at most thirty times in one turn; `blight-curse-guard.json` is its guard arm of #57 and `blight-curse-join.json` lines up `before`, `shipped`, `guard` and `limit`. 40 wins each, no table decided differently, 191 of the 200 pairs the same to the last event, the limit not reached once, no game without a winner. It passed its rule and shipped as version 6; these tables say only that the limit does no harm where the chain does not come up (DESIGN.md §38).


`2026-11-22-ab-v29/`: Blight Curse's second sample (DESIGN.md §37; `ab-run` #61, run id 44977958676, commit f615b1f, harness 0.4.11; seed 20261420, tables of its own at the owner's table, opponents the versions shipped in the night of 2026-11-22). `blight-curse-before.json` is version 3, `blight-curse-v4.json` version 4 (the hooks and its own new rules), `blight-curse.json` version 5 (with the guard, shipped); the join has them as `before`, `v4` and `shipped`. `hook-exam.json`, the two first-difference files and `deck-exam-blight-curse.json` are the exam files. Wins of 200: 38, 45 and 47. Version 5 beside version 3: 30 tables against 21 (exact test 0.26), where #57 had 18 against 26. The rule, fixed before the run, was on the two samples together because the deck was picked for being behind: 48 tables against 47 over 400. Level; version 5 stays.


`2026-11-22-ab-v30/`: the five pool decks that had no hook (DESIGN.md §40; `ab-run` #62, run id 45015552254, commit 71b465c, harness 0.4.11; seed 20261450 on `runner/leagues/bots-v2.json`, tables that chose nothing; opponents drawn from the other eleven under the playbooks shipped on 2026-11-22, seven with the hooks and free damage and five without a hook; 200 tables a deck, playbook arm only). `<deck>.json` is the deck under its shipped playbook, `<deck>-hooks.json` with the four hooks that are not a matter of the deck, `<deck>-hooksopen.json` with free damage as well (the files `ab-run` #59 played); `<deck>-join.json` lines the three up as `shipped`, `hooks` and `hooksopen`. `hook-exam.json`, the three first-difference files and `kill-force.json` are the exam files. All 75 shard artifacts were fetched and checked against seed, date and pool; the rollups are made from them (the run's own `ab-rollups` artifact had not been published when this was written; it was at 17:48 UTC, and compared at 19:35: the same fifteen rollups, entry for entry, `generated` aside).
Wins of 1,000: shipped 246, with the hooks 259 (53 tables only the hooks won against 40, exact test 0.21), with free damage too 261 (94 against 79, 0.29). Read by the rule fixed before the run, over the five decks together: the four hooks hold (the wins; 64.2% of the seat's attackers at the most dangerous opponent with three alive from 54.7%; the seat's own shortfall on that opponent's sure kill on 9 turns of 185 from 22 of 186), and free damage holds (beside the arm without it 142 tables against 163 over this sample and #59's together, exact test 0.25, 73 against 71 here; beside the shipped playbooks 94 against 79; an opponent who cannot block attacked on 58.9% of the turns from 32.6%). No deck's arm is behind its shipped arm beyond noise, so all five shipped the arm with free damage on 2026-11-22 (Token Triumph version 6, Hail, Caesar 7, Tricky Terrain 9, Planeswalker Party 3, Elven Council 3) and all twelve decks of the pool carry the five hooks. Planeswalker Party's arm with free damage is behind its arm without it in both samples (17 tables against 30 together, exact test 0.08): inside noise, and the deck to look at when the guard is read. Games without a winner 8, 4 and 6 of 1,000, none in a chain of Eldrazi Incursion's commander (its version 3 sat among the opponents for the first time).

`2026-11-22-ab-v31/`: the seven pool decks that shipped the hooks first, on tables that chose nothing, and the guard (DESIGN.md §40; `ab-run` #63, run id 45015581613, commit 985e544, harness 0.4.11; seed 20261450 on `runner/leagues/bots-v2.json`, the tables of `ab-run` #62; opponents drawn from the other eleven under the playbooks shipped when the run was queued, seven with the hooks and free damage and five without a hook; 200 tables a deck, playbook arm only). `<deck>-before.json` is the deck under the version before the hooks (the playbook `ab-run` #58 played), `<deck>.json` under the version shipped on 2026-11-22 (the hooks and free damage), `<deck>-guard.json` under that version with `"guard": "table"`; `<deck>-join.json` lines the three up as `before`, `shipped` and `guard`. `hook-exam.json` and the two first-difference files are the exam files. All 105 shard artifacts were fetched and checked against seed, date and pool; the rollups are made from them (the run's own `ab-rollups` artifact had not been published when this was written; it was at 21:56 UTC, and compared at 22:12: the same twenty-one rollups, entry for entry, `generated` aside).
Wins of 1,400: the versions before 352, the versions shipped 349 (139 tables only the shipped version won against 142, exact test 0.91), with the guard 347 (27 tables only the guard won against 29, exact test 0.89). Read by the rules fixed before the run, over the seven decks together. Rule 1: the versions shipped on 2026-11-22 stand (fewer tables, far inside noise), and no deck is behind its version before over its two samples together; these figures replace #59's in the decks' rows, where these decks' arms with the hooks and free damage had been 185 tables against 103 beside the playbooks before them, as the better of two arms on the tables that measured them and against opponents without a hook. Rule 2: the guard holds (the wins; and on the 175 tables where the seat's own attack is the first thing that differs the seat is out of the game before its own next turn on 18 with the guard where it was on 31, with 329 attackers sent where 549 were), and no deck's guard arm is behind beyond noise, so all seven shipped it on 2026-11-22 (Goblin Storm version 7; Deep Clue Sea, Limit Break, Quick Draw, Wretched Ranks, Eldrazi Incursion and Enduring Enchantments version 4). Counted for the seat under test (before, shipped, with the guard): the sure kill of the most dangerous of several opponents missed on 40 of 280 turns, 22 of 254 and 22 of 252 (not gone for at all: 29, 1 and 2); with three opponents alive 47.8%, 53.2% and 52.6% of its attackers at the most dangerous one; an opponent who cannot block attacked on 29.7%, 62.5% and 62.0% of the turns it could be; deaths by a block not made 11, none and none; with its own creatures tapped 100, 90 and 82; on a turn a commander's damage reached 21: 66, 61 and 62. Games without a winner 15, 8 and 11 of 1,400: Tricky Terrain's Scute Swarm 6, 4 and 8; Eldrazi Incursion's own arms 4 (one a draw at the end of a chain of its own), none and none.

`2026-11-22-ab-v32/`: rules for other players' turns at the owner's table (DESIGN.md §39, §40; `ab-run` #64, run id 45025122223, commit e06c416, harness 0.4.12; seed 20261460 on `runner/leagues/owners-table-v1.json`, tables that chose nothing; opponents drawn from the other nine under the versions shipped on 2026-11-22, every hook and the guard; 200 tables a deck, playbook arm only). `<deck>.json` is the deck under its shipped playbook, `<deck>-react.json` under `playbook/variants/<deck>-react.json` (its single-target instant removal held from Forge's AI and played on other players' turns); `<deck>-join.json` lines the two up as `shipped` and `react`. `react-exam.json` is `docs/agents/react_exam.py`'s reading (per card the games held and cast and the casts by when, the casts at an attacker one by one, what the casts hit, the rules' counters), `first-difference-shipped-react.json` the pairs by the first event that differs. All 100 shard artifacts were fetched and checked against seed, date and pool; the rollups are made from them, and are the same as the run's own `ab-rollups` artifact, entry for entry, `generated` aside.
Wins of 2,000: shipped 491, with the rules 497 (123 tables only the new versions won against 117, exact test 0.75). Read by the rule fixed before the run, over the ten decks together: the tables are not behind; the cards are still played (cast in 994 of the 1,182 card-games held, 84.1%, where at least 80% was asked; the shipped pilots 1,104 of 1,184, 93.2%); the rules act (951 of the cards' 997 casts on another player's turn, 95.4%, where at least half was asked; the shipped pilots 95 of 1,114, 8.5%). So the rules go in, and nine decks shipped their `react` arm on 2026-11-22 (Blight Curse, Veloci-Ramp-Tor, Blood Rites and Miracle Worker version 7; Squirreled Away and Revenant Recon version 8; Mutant Menace, Death Toll and Deadly Disguise version 6). Ahoy Mateys is left out by the rule's clause for one deck: behind its shipped arm on its own tables, 4 against 13, exact test 0.049 (its cards cast in 78 of 108 card-games held; Lethal Scheme in 35 of 58). What the end-step casts hit: 859 at an opponent's permanent, 37% a commander, 74% at the opponent that looked most dangerous with two or three alive (the shipped pilots' own-turn casts: 34% and 63%). Casts at a creature attacking the seat 92; an attack that would end the seat's game seen 108 times with a card held, answered 33 times, beyond one removal 45 times. The seat's deaths in combat 1,087 before and 1,093 with the rules (31 and 64 with one of the cards in hand). Two games without a winner in each arm, the same two tables; 51.4 and 49.3 hours of play.

`2026-11-22-ab-v33/`: the guard for the five pool decks of `ab-run` #62 (DESIGN.md §40; `ab-run` #65, run id 45050127604, commit bfb29bb, harness 0.4.12; seed 20261470 on `runner/leagues/bots-v2.json`, tables of its own that chose nothing; opponents drawn from the other eleven under the playbooks shipped on 2026-11-22 after #62, the five hooks in every one and the guard in none; 200 tables a deck, playbook arm only). `<deck>.json` is the deck under the version shipped then, `<deck>-guard.json` under that version with `"guard": "table"`; `<deck>-join.json` lines them up as `shipped` and `guard`. `hook-exam.json` and `first-difference-shipped-guard.json` are the exam files. All 50 shard artifacts were fetched and checked against seed, date and pool; the rollups are made from them, and are the same as the run's own `ab-rollups` artifact.
Wins of 1,000: without the guard 236, with it 241 (34 tables only the guard won against 29, exact test 0.61). By the rule fixed before the run (the guard had to hold for the seven decks of `ab-run` #63, which it did, and these five decks' tables had not to be behind) the guard goes into all five, which shipped it on 2026-11-22 (Token Triumph version 7, Hail, Caesar 8, Tricky Terrain 10, Planeswalker Party 4, Elven Council 4): every deck of the pool carries all six hooks. On the 216 tables where the seat's own attack is the first thing that differs the seat is out before its own next turn on 13 with the guard where it was on 25, with 538 attackers sent where 841 were; deaths with its own creatures tapped 73 against 92. The guard changed 290 of the 444 attacks it judged fatal, 114 of them Tricky Terrain's and 69 Hail, Caesar's, the two decks with a go-wide attack of their own. Planeswalker Party: 54 wins with the guard and 53 without. Games without a winner 11 and 10 of 1,000 (Tricky Terrain's Scute Swarm 2 and 5).

`2026-11-23-ab-v34/`: a commander's damage as a kill (DESIGN.md §41; `ab-run` #66, run id 45083908959, commit c37c68a, harness 0.4.13; seed 20261480, tables that chose nothing; Limit Break on `runner/leagues/bots-v2.json` and Mutant Menace on `runner/leagues/owners-table-v1.json`, the opponents under the playbooks shipped on 2026-11-22 evening; 200 tables a deck, playbook arm only). `<deck>.json` is the deck under the version shipped then (Limit Break 4, Mutant Menace 6), `<deck>-cmdr.json` under that version with `"finish_commander": true`; `<deck>-join.json` lines them up as `shipped` and `cmdr`. `hook-exam.json` and `first-difference-shipped-cmdr.json` are the exam files; `commander-kills.json` (`docs/agents/commander_kills.py`) lists, for the seat under test in each arm, every turn on which only its commander gave a sure kill of the most dangerous or the last opponent, and the tables whose two games differ first at an attack of the seat's, with the commander's kills on the table at that attack; `commander-kills-by-deck.json` is `runner/mistakes.py --by-deck` over the 800 games, the count for every deck that sat at these tables. All 20 shard artifacts were fetched and checked against seed, date and pool (each deck against its own); the rollups are made from them, and are the same as the run's own `ab-rollups` artifact.
Wins of 400: shipped 92, with the option 96 (6 tables only the option won against 2, exact test 0.29). Read by the rule fixed before the run, over the two decks together: the tables are not behind, and of the turns on which only a commander gave the seat a sure kill of the most dangerous or the last opponent, nobody was out on 1 of 32 with the option where it was 11 of 34 without (a smaller share was asked). Neither deck is behind and the option changed a declaration in both (6 and 5 turns), so both shipped their `cmdr` arm on 2026-11-23: Limit Break version 5 (47 wins against 46, 3 tables against 2) and Mutant Menace version 7 (49 against 46, 3 against 0, exact test 0.25). The eleven misses without the option: nothing sent at anybody on eight, the commander sent at a planeswalker or elsewhere on two, one attack answered; the one left with the option is that answered attack (Squirreled Away's held Putrefy on the attacking Mothman, the same turn in both arms). On the 13 tables where the two games differ first at an attack with a commander's sure kill on the table that opponent was out that turn every time with the option and never without (three times the version before killed a lesser opponent instead); those tables ended both won 3, neither 7, only the option 2, only the version before 1, and the other five discordant tables (4 against 1) differ first for a reason that is not the option's. Nine of the 13 are the kill hook's walk sending the commander; four, all Mutant Menace's, are the guard no longer taking back a commander's kill that Forge's own attack had declared. Among the other decks at these tables only Elven Council (3 turns in 98 seat-games) and Revenant Recon (4 in 132) have such kills of the most dangerous or the last opponent at all. One game of 800 without a winner (the clock).

`2026-11-23-ab-v35/`: two decks' own rules for other players' turns at the table as it is since 2026-11-23 (DESIGN.md §43; `ab-run` #67, run id 45103929228, commit f3cb795, harness 0.4.13; seed 20261500 on `runner/leagues/owners-table-v1.json`, tables that chose nothing; opponents drawn from the other nine under their shipped playbooks, so with those rules in eight of the nine; 200 tables a deck, playbook arm only). `<deck>-noreact.json` is the deck under its version before the rules (Squirreled Away 7, Deadly Disguise 5), `<deck>.json` under its shipped version (8 and 6); `<deck>-join.json` lines them up as `noreact` and `shipped`. `react-exam.json` is `docs/agents/react_exam.py` with the shipped arm as the candidate (the casts of the held cards in both arms), `first-difference-shipped-noreact.json` the pairs by the first event that differs (its candidate is the version before: read its columns the other way round), `received.json` the receiving seat in each arm. All 20 shard artifacts were fetched and checked against seed, date and pool; the rollups are made from them, and are the same as the run's own `ab-rollups` artifact.
Read by the rule fixed before the run (a deck goes back to its version before the rules only when the tables only its shipped version won are fewer than the tables only the version before won with the exact test below 0.05): neither goes back. Squirreled Away: 21 wins with the rules and 21 without (4 tables against 4); Putrefy cast in 38 of the 45 card-games it was held (43 of 47 without the rules), all 38 on another player's turn. Deadly Disguise: 12 wins with the rules and 20 without (4 tables against 12, exact test 0.077; two of the twelve are tables its shipped arm's game left without a winner, one on the clock and one a draw in Blight Curse's Snake chain); its three cards cast in 111 of 138 card-games held (116 of 136), all 114 casts on another player's turn; the mana for a card kept on 138 turns (Squirreled Away 49), and the seat a little behind in board and damage (4.0 nonland permanents at its own eighth turn against 4.1, 22.2 combat damage a game against 24.8). With `ab-run` #64's sample, where the opponents had no such rules, Deadly Disguise is 11 tables against 21 over 400 (exact test 0.11) and Squirreled Away 11 against 11. 236 of the 400 pairs are the same game to the last event. Two games of 800 without a winner, both in Deadly Disguise's shipped arm.

