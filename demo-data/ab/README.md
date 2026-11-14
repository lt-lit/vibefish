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

`2026-11-14-ab-v17/`: the owner's table (DESIGN.md §30), collected run by run as Actions finishes them; this paragraph grows with them.
The first exam of the ten engine-only candidates, each at 200 tables whose three opponents are drawn from the twelve bots of `bots-v2`
under their shipped playbooks of 2026-11-13: `<deck>-<name>.json` has the stock pilot and the candidate with its go-wide attack,
`<deck>-<name>-forgeattack.json` the same rules with the attack left to Forge on the same tables (playbook arm only), and
`<deck>-join.json` the three side by side (kind `ab-join`; arms `stock`, `gowide`, `forgeattack`). Collected so far (`ab-run` #29 and
#30, seed 20261290), wins of 200 as stock / go-wide / Forge's attack: Blood Rites `demons` 66 / 78 / 83 (go-wide +6.0 points, exact
test 0.22; Forge's attack +8.5, 95% -1 to +18, 0.089; between the two attacks 0.61); Revenant Recon `mirko` 47 / 55 / 53 (+4.0, 0.37;
+3.0, 0.52); Miracle Worker `veil` 64 / 55 / 59 (-4.5, 0.29; -2.5, 0.63). None of these candidates is shipped: every one of them casts
its removal and its large threats far less than its stock pilot on the same tables (§30), and each deck ships from the exam of its
second pass (`<deck>-answers.json`, `ab-run` #36 to #39).
