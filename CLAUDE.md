# Vibefish — Claude Code context

Read `DESIGN.md` first. This file is the short version plus hard constraints.

## What this repo is
Commander deck playtesting engine built on Forge's headless `sim` mode. Engine only — decks, playbooks and results live in a separate data repo and are passed in by path.

## Hard constraints
- **Dashboard:** vanilla JS, no build step, no TypeScript, no frameworks. Must work on GitHub Pages and on a phone browser.
- **Images:** never commit card image files. Hotlink `cards.scryfall.io` URLs from the cache only.
- **Scryfall API:** ≥100 ms between requests to `api.scryfall.com`; set `User-Agent: Vibefish/<version>` in scripts; leave browser UA alone in page JS. Never crop/alter images. Resolve names in batches via `cards/collection`.
- **Forge:** pinned to the tag in `forge/VERSION` with the checksum in `forge/SHA256SUMS`. Do not float to `latest` or `daily-snapshots` unless `FORGE_CHANNEL=snapshot` is explicitly set. The runtime is downloaded by `forge/fetch-forge.sh` into `forge/runtime/` and is never committed.
- **No Forge fork.** `controller/` compiles against the released Forge jar and uses public hooks (event bus, `PlayerControllerAi`). Patch Forge only if a hook is private, and record it in `DESIGN.md`.
- **Always pass `-c`** (clock) to sim mode. Forge's default is 120 s and declares longer games a draw; Commander games routinely exceed it.
- **License:** this repo is GPL v3 because `controller/` compiles against Forge. Don't vendor non-GPL-compatible code.
- **Naming:** project is "Vibefish". "MTG" / "Magic: The Gathering" appear only descriptively, never in the product name, repo name, or logos.
- **Benchmark pod** in `runner/benchmark-pod.json` is frozen. Do not edit it.

## Forge sim mode cheat sheet
```
forge/fetch-forge.sh                      # download + verify + assemble forge/runtime/ (once)
runner/pod-smoke.sh -n 3 -s 42            # benchmark pod plays 3 games; log + summary in results/
forge/forge.sh sim -f Commander -D /abs/deck/dir -d "A.dck" "B.dck" "C.dck" "D.dck" -n 10 -s 42 -c 900 [-q] [-a Default Reckless Default Cautious]
```
Flags: `-f` format, `-D` **absolute** deck dir, `-d` deck files (quote names with spaces; a name counts as a file if it ends in a dot plus three characters), `-n` games, `-s` RNG seed, `-c` clock in seconds before the game is called a draw, `-a` AI profile per seat in deck order (`res/ai/*.ai`), `-q` results only, `-m` best-of-M.

Four `-d` decks in plain mode = one 4-player game (confirmed Phase 0). **Never use `-t`/`-p` for Commander:** tournament mode pairs decks 1v1 at 20 life and ignores `-D` for named decks.

Output: stdout, plus `forge/runtime/profile/user/forge.log` (redirected from `~/.forge` by the `forge.profile.properties` the fetch script writes). Bundled Commander precons: `forge/runtime/res/quest/commanderprecons/`, 179 decks named `Name [SET] [YEAR].dck`. Forge needs Java 17+ (CI uses Temurin 21). Sim mode does not need card images.

## Key links
- Forge AI / sim flags: https://github.com/Card-Forge/forge/wiki/AI
- Forge sim mode source: https://github.com/Card-Forge/forge/blob/master/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java
- Forge releases: https://github.com/Card-Forge/forge/releases
- Forge card scripting (AILogic, RemAIDeck): https://github.com/Card-Forge/forge/wiki/Card-scripting-API
- Forge release/snapshot process: https://github.com/Card-Forge/forge/wiki/Snapshots-and-Releases
- Scryfall API: https://scryfall.com/docs/api
- WotC Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

## Phase 0 checklist — status 2026-11-08
- [x] 1. Pinned Forge downloaded; 2-player constructed sim completes (2 games, 5–11 s each).
- [x] 2. 4-deck Commander sim: four players in one game, 40 life, commander damage counted; 11/11 games completed.
- [x] 3. Log shape recorded in `DESIGN.md` §14; it drives the Phase 1 `JsonGameLogger`.
- [x] 4. Timing: 98 s/game average over 10 (median 66 s, range 44–247 s) plus ~11 s startup. Recorded in `DESIGN.md` §4.2.
- [x] 5. GitHub Actions on `ubuntu-latest`: `.github/workflows/phase0.yml` green on its first run (2026-11-08): 4-vCPU runner, Forge fetched and verified in 26 s, 3 pod games completed in 509 s (41 s, 85 s, 375 s), runtime cached at 66 MB compressed.

Phase 0 is complete. Phase 1 (harness, runner, rollup, dashboard) can start.

## Required README footer
> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
