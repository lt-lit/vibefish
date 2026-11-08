# Vibefish

Commander deck playtesting built on [Forge](https://github.com/Card-Forge/forge)'s headless sim mode.
Drop in a decklist, run hundreds of AI-vs-AI pod games, get consistency stats, matchup win rates and
replayable game logs. Over time the project grows deck-specific AI pilots ("playbooks") that an LLM
writes offline and the match loop executes cheaply.

This is the engine. Decks, playbooks and results for your own decks live in a separate data repository and
are passed in by path; `demo-data/` holds the public benchmark-pod results. Read [`DESIGN.md`](DESIGN.md)
for the full picture.

**Status:** Phase 1 complete. The benchmark pod (four bundled Commander precons) plays itself through a
Java harness that records every game as a JSON event stream; the dashboard shows per-deck win rates,
mulligans, land drops, commander timing and the cards that never get cast, with card images from Scryfall.

**Dashboard:** https://lt-lit.github.io/vibefish/ — deployed from the `testing` branch by `.github/workflows/pages.yml`. One-time repository setup by the owner: Settings → Pages → Build and deployment → Source: **GitHub Actions**; then Settings → Environments → `github-pages` → Deployment branches and tags → allow `testing` (GitHub creates that environment restricted to the default branch, and the workflow token can change neither setting). Until then, run the dashboard locally as below.

## Quick start

Requires Java 17+ (CI uses Temurin 21), `python3`, `curl`, `jq`, `tar`/`bzip2`.

```bash
forge/fetch-forge.sh                 # download the pinned Forge release, verify, assemble forge/runtime/
runner/run-pod.sh -n 8 -j 2 -s 42    # the pod plays 8 games in 2 shards → results/<run-id>/rollup.json
runner/publish.sh results/<run-id> demo-data   # add the run to the data the dashboard reads
python3 -m http.server 8000          # open http://localhost:8000/dashboard/?data=../demo-data
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
| `controller/` | Java harness compiled against the released Forge jar: `play` records games as JSONL events, `check` validates decks. |
| `runner/` | The frozen benchmark pod, sharded pod runner, rollup, Scryfall resolver, publish helper. |
| `dashboard/` | Vanilla JS static site for GitHub Pages. |
| `demo-data/` | Published pod runs and the card image cache the dashboard reads. |
| `playbook/` | Playbook schema, validator, examples (Phase 2+). |
| `.github/workflows/` | Smoke test, sharded pod runs, Pages deployment. |

## License and credits

Vibefish is licensed under the GNU General Public License v3 (see [`LICENSE`](LICENSE)) because it links against
Forge, which is GPL v3. Forge is developed by the Forge team at <https://github.com/Card-Forge/forge>.

Card data and images come from [Scryfall](https://scryfall.com) under their [API terms](https://scryfall.com/docs/api);
images are hotlinked, never stored or altered.

> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
