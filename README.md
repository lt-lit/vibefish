# Vibefish

Commander deck playtesting built on [Forge](https://github.com/Card-Forge/forge)'s headless sim mode.
Drop in a decklist, run hundreds of AI-vs-AI pod games, get consistency stats, matchup win rates and
replayable game logs. Over time the project grows deck-specific AI pilots ("playbooks") that an LLM
writes offline and the match loop executes cheaply.

This is the engine. Decks, playbooks and results for your own decks live in a separate data repository and
are passed in by path; `demo-data/` holds the public benchmark-pod results. Read [`DESIGN.md`](DESIGN.md)
for the full picture.

**Status (2026-11-20):** twenty-two precons have a per-deck bot: a playbook for one deck that says which card to cast
when and aimed at what, which of the deck's optional triggers to take, and when to use its board wipes and removal;
three of them also choose their own attacks, and everything else stays Forge's. Each has been set against the same
deck under Forge's stock AI at 200 four-player tables whose other three seats are bots too, on tables that chose
nothing: the twelve of the first pool won 573 of 2,400 tables to their stock pilots' 405 (four decks ahead beyond
noise, none behind), and the ten precons of one playgroup, at a table drawn from those ten, 511 of 2,000 to 439 (two
ahead beyond noise, three inside it, four level, one behind inside noise); together 24.6% of 4,400 tables against
19.2% (`DESIGN.md` §32). Those ten have also played a league among themselves, which is on the dashboard, and each has
a playtest report at that table (`demo-data/playtest/2026-11-15/owners-table/`): the report a list of your own gets
(`runner/decklist.py`, `runner/playbook.py adapt`, `runner/ab.py --deck-file`, `runner/playtest.py`; `DESIGN.md` §31).
What the bots still lack is the table itself: their attacks and most of their removal go where Forge's AI sends them,
at the widest board and the lowest life, and at the player who goes on to win less often than chance. The first piece
against that is in (`DESIGN.md` §33): a rule can aim a spell at the best permanent of the opponent that looks most
dangerous, and three bots use it since 2026-11-15 to cast removal that neither Forge's AI nor their earlier versions
ever cast. The bar from here on is play at the level of a person, and it is counted in mistakes that need no human to define (`runner/mistakes.py`, `DESIGN.md` §34: an opponent left alive whom the seat was sure to kill, a death by a block not made, a death with its own blockers tapped). The first count at scale, 2,000 games in which every seat is a bot, and the exam of the first fix corrected the first guess: a bot passes up a third of its sure kills, but nearly all of those are of a weaker player while a stronger one lives, and a bot made to take every kill won no more tables (505 against 512 of 2,000): it won them where the player it killed was the most dangerous one and lost them where it was not. What the count does show is how the bots die: one death in six in combat comes with the seat's own creatures tapped. Two narrower fixes are at the tables now: the sure kill taken only from the most dangerous opponent, and attackers kept home when the attack would leave the seat dead on board. The dashboard shows all twenty-two in one table. Underneath: the benchmark pod
(four bundled Commander precons) plays itself through a Java harness that records every game as a JSON event
stream; the dashboard shows per-deck win rates, mulligans, land drops, commander timing and the cards that never
get cast, with card images from Scryfall; Forge's Flat Monte Carlo AI has been A/B-tested against its heuristic AI
on the pod; and a precon league (91 bundled precons over random four-player tables) scores the sim's precon
ranking against the human win rates Playgroup.gg publishes for stock precons, a coarse comparison (those rates are
against unknown decks and noisy, `DESIGN.md` §26). `DESIGN.md` §21 to §31 have how the bots were built and measured.

**Dashboard:** https://lt-lit.github.io/vibefish/ — GitHub Pages serves the `testing` branch directly (Settings → Pages → Deploy from a branch → `testing`, root). The repository root redirects to `dashboard/`, which reads `../demo-data/`; `.nojekyll` keeps Pages from processing the files.

## Quick start

Requires Java 17+ (CI uses Temurin 21), `python3`, `curl`, `jq`, `tar`/`bzip2`.

```bash
forge/fetch-forge.sh                 # download the pinned Forge release, verify, assemble forge/runtime/
runner/run-pod.sh -n 8 -j 2 -s 42    # the pod plays 8 games in 2 shards → results/<run-id>/rollup.json
runner/publish.sh results/<run-id> demo-data   # add the run to the data the dashboard reads
python3 -m http.server 8000          # open http://localhost:8000/dashboard/?data=../demo-data
runner/league.py schedule --seed 20261109 --cycles 25          # the precon league: 91 precons, 2200 games
runner/league.py play --seed 20261109 --cycles 25 --out results/league --shards 20 --shard 1 -j 2
                                     # one shard of it locally; .github/workflows/league-run.yml plays them all
```

Playtest a list of your own at a table of the bots:

```bash
runner/decklist.py "My List.txt" --commander "Card Name" --runtime forge/runtime   # a list pasted from a deck site → "My List.dck", checked by Forge
runner/ab.py play --deck my-deck --deck-file "$PWD/My List.dck" --games 200 --seed 20261400 --out results/pt-my-deck \
  --arms stock --pool runner/leagues/bots-v2.json --opponent-playbooks -j 2        # the list in one seat, three bots under their playbooks in the others
runner/playtest.py results/pt-my-deck --md report.md                               # wins, who beats it, tempo, and what each card did
```

Validate and play any Commander decks through the harness directly:

```bash
controller/vibefish-sim.sh check --deck-dir /path/to/decks "My Deck.dck"
controller/vibefish-sim.sh play --out results/mine --deck-dir /path/to/decks \
  --deck mine="My Deck.dck" --deck a="Opponent A.dck" --deck b="Opponent B.dck" --deck c="Opponent C.dck" \
  --games 10 --seed 42 --clock 900 --turn-cap 120
```

## Branches

`testing` is where work lands first and is what GitHub Pages serves; `main` is promoted from `testing` when a milestone is accepted; feature branches merge into `testing`.

## Layout

| Path | What |
|---|---|
| `forge/` | Version pin, checksum, fetch and launch scripts. The runtime is downloaded, never committed. |
| `controller/` | Java harness compiled against the released Forge jar: `play` records games as JSONL events, `check` validates decks, and a seat given a playbook plays under it (`PlaybookController`: cast rules, attack policy, mulligan rule; everything else stays Forge's AI). |
| `runner/` | The frozen benchmark pod and precon league, sharded pod and league runners, rollups, calibration scorecard with the Playgroup.gg references, goldfish runs, the paired A/B of one deck's bot at four-player tables or in duels (`ab.py`), the playbook draft tool (`playbook.py`), the bots table for the dashboard (`bots.py`), log readers (`playstyle.py`, `hands.py`, `losses.py`, `cardplay.py`), Scryfall resolver, publish helper. |
| `dashboard/` | Vanilla JS static site for GitHub Pages. |
| `demo-data/` | Published pod runs and the card image cache the dashboard reads. |
| `playbook/` | One file per league precon: data for Forge's AI and, for the decks that have one, the playbook (which card to cast when and aimed at what, which optional triggers to take, how to attack); `variants/` holds candidate playbooks and drafts measured before one ships. Schema and how to write one in `playbook/README.md`. |
| `.github/workflows/` | Smoke test, sharded pod runs, sharded league runs, sharded paired A/Bs. Pages serves the `testing` branch directly. |

## License and credits

Vibefish is licensed under the GNU General Public License v3 (see [`LICENSE`](LICENSE)) because it links against
Forge, which is GPL v3. Forge is developed by the Forge team at <https://github.com/Card-Forge/forge>.

Card data and images come from [Scryfall](https://scryfall.com) under their [API terms](https://scryfall.com/docs/api);
images are hotlinked, never stored or altered.

> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
