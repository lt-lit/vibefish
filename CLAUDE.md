# Vibefish — Claude Code context

Read `DESIGN.md` first. This file is the short version plus hard constraints.

## What this repo is
Commander deck playtesting engine built on Forge's headless `sim` mode. Engine only — decks, playbooks and results live in a separate data repo and are passed in by path. `demo-data/` holds the public pod results the dashboard shows.

## Hard constraints
- **Dashboard:** vanilla JS, no build step, no TypeScript, no frameworks. Must work on GitHub Pages and on a phone browser. It reads only the data contract in `DESIGN.md` §6 (`index.json`, `rollup.json`, `cards/scryfall-cache.json`).
- **Images:** never commit card image files. Hotlink `cards.scryfall.io` URLs from the cache only; `small` and `normal` only, never cropped art.
- **Scryfall API:** ≥100 ms between requests to `api.scryfall.com`; set `User-Agent: Vibefish/<version>` in scripts (`runner/scryfall.py` does); leave browser UA alone in page JS. Resolve names in batches via `cards/collection`.
- **Forge:** pinned to the tag in `forge/VERSION` with the checksum in `forge/SHA256SUMS`. Do not float to `latest` or `daily-snapshots` unless `FORGE_CHANNEL=snapshot` is explicitly set. The runtime is downloaded by `forge/fetch-forge.sh` into `forge/runtime/` and is never committed.
- **No Forge fork.** `controller/` compiles against the released Forge jar and uses public hooks (event bus, `PlayerControllerAi`). Patch Forge only if a hook is private, and record it in `DESIGN.md`.
- **Always pass a clock** to sim mode (`-c` / `--clock`). Forge's default is 120 s and declares longer games a draw; Commander games routinely exceed it. The harness also caps turns (`--turn-cap`, default 120).
- **Event schema:** changes to the JSONL events or `run.json` keep `runner/rollup.py` and `DESIGN.md` §6 in sync and bump `VERSION`.
- **License:** this repo is GPL v3 because `controller/` compiles against Forge. Don't vendor non-GPL-compatible code.
- **Naming:** project is "Vibefish". "MTG" / "Magic: The Gathering" appear only descriptively, never in the product name, repo name, or logos.
- **Benchmark pod** in `runner/benchmark-pod.json` is frozen. Do not edit it.

## Commands
```
forge/fetch-forge.sh                                   # download + verify + assemble forge/runtime/ (once)
controller/build.sh                                    # javac → controller/out/vibefish-sim.jar (launcher does this automatically)
controller/vibefish-sim.sh check --deck-dir DIR "A.dck" "B.dck"             # unknown/unsupported/AI-flagged cards, conformance
controller/vibefish-sim.sh play --out results/x --deck-dir DIR \
    --deck a=A.dck --deck b=B.dck --deck c=C.dck --deck d=D.dck \
    --games 10 --seed 42 --clock 900 --turn-cap 120 [--profile Default ...]   # JSONL events + run.json
runner/run-pod.sh -n 20 -j 2 -s 42                     # benchmark pod, 2 shards → results/<run-id>/{shard-*,rollup.json}
runner/publish.sh results/<run-id> demo-data           # → demo-data/runs/<run-id>/, index.json, card cache
python3 -m http.server 8000                            # then open http://localhost:8000/dashboard/?data=../demo-data
runner/pod-smoke.sh -n 3 -s 42                         # Phase 0 smoke test through Forge's own sim mode
```
Relative paths given to the launcher resolve against the directory you run it from. Bundled Commander precons: `forge/runtime/res/quest/commanderprecons/` (179 decks named `Name [SET] [YEAR].dck`). Forge needs Java 17+ (CI uses Temurin 21). Sim mode does not need card images.

## Forge sim mode notes
Four `-d` decks in plain mode = one 4-player game (confirmed Phase 0). **Never use `-t`/`-p` for Commander:** tournament mode pairs decks 1v1 at 20 life and ignores `-D` for named decks. `-D` must be absolute; quote names with spaces. Per-seat AI profiles: `-a` in sim mode, `--profile` in the harness (`res/ai/*.ai`). Forge's AI prints a `java.util.concurrent.TimeoutException` stack trace when its own decision timeout fires; harmless. Forge's user data is redirected into `forge/runtime/profile/` by the `forge.profile.properties` the fetch script writes.

## Branches
- `testing`: change control. Work lands here first and GitHub Pages deploys from here, so the live dashboard shows what is being tested. `pod-run.yml` with publish on this branch commits `demo-data/` here.
- `main`: stable. Promoted from `testing` by fast-forward or merge when a milestone is accepted; never pushed to directly.
- `claude/*` and other feature branches: day-to-day work, pushed to their own branch, merged into `testing`.

## Workflows
- `phase0.yml`: Forge sim-mode smoke test on push to `forge/**`, `runner/**`.
- `pod-run.yml` (manual): 4 shards × N games, rollup, optional publish into `demo-data/` on the branch.
- `pages.yml`: deploys `dashboard/` + `demo-data/` (as `data/`) to GitHub Pages on push to `testing`. Requires Pages to be enabled once in repo settings with source "GitHub Actions"; the first run failed with "Create Pages site failed: Resource not accessible by integration" until that is done.

## Key links
- Forge AI / sim flags: https://github.com/Card-Forge/forge/wiki/AI
- Forge sim mode source: https://github.com/Card-Forge/forge/blob/master/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java
- Forge game events: https://github.com/Card-Forge/forge/tree/master/forge-game/src/main/java/forge/game/event
- Forge releases: https://github.com/Card-Forge/forge/releases
- Forge card scripting (AILogic, RemAIDeck): https://github.com/Card-Forge/forge/wiki/Card-scripting-API
- Scryfall API: https://scryfall.com/docs/api
- WotC Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

## Status
- Phase 0 (spike): done 2026-11-08 — `DESIGN.md` §14.
- Phase 1 (goldfish): done 2026-11-08 — harness, runner, rollup, resolver, dashboard, workflows; `DESIGN.md` §15.
- Phase 2 (pilot) is next: per-deck AI profile first, then `PlaybookController`; plus the manifest runner for the data repo.

## Required README footer
> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
