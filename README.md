# Vibefish

Commander deck playtesting built on [Forge](https://github.com/Card-Forge/forge)'s headless sim mode.
Drop in a decklist, run hundreds of AI-vs-AI pod games, get consistency stats, matchup win rates and
replayable game logs. Over time the project grows deck-specific AI pilots ("playbooks") that an LLM
writes offline and the match loop executes cheaply.

This is the engine. Decks, playbooks and results for your own decks live in a separate data repository and
are passed in by path; `demo-data/` holds the public benchmark-pod results. Read [`DESIGN.md`](DESIGN.md)
for the full picture.

**Status:** Phase 2 (measure) under way. The benchmark pod (four bundled Commander precons) plays itself through a
Java harness that records every game as a JSON event stream; the dashboard shows per-deck win rates,
mulligans, land drops, commander timing and the cards that never get cast, with card images from Scryfall.
Forge's Flat Monte Carlo AI has been A/B-tested against its heuristic AI on the pod, and a precon league
(91 bundled precons over random four-player tables) scores the sim's precon ranking against the human
win rates Playgroup.gg publishes for stock precons.

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
| `runner/` | The frozen benchmark pod and precon league, sharded pod and league runners, rollups, calibration scorecard with the Playgroup.gg references, goldfish runs, the paired A/B of one deck's bot at four-player tables or in duels (`ab.py`), the playbook draft tool (`playbook.py`), the bots table for the dashboard (`bots.py`), log readers (`playstyle.py`, `hands.py`), Scryfall resolver, publish helper. |
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
