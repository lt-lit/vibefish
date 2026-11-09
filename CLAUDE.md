# Vibefish — Claude Code context

Read `DESIGN.md` first. This file is the short version plus hard constraints.

## What this repo is
Commander deck playtesting engine built on Forge's headless `sim` mode. Engine only — decks, playbooks and results live in a separate data repo and are passed in by path. `demo-data/` holds the public pod results the dashboard shows.

## Hard constraints
- **Dashboard:** vanilla JS, no build step, no TypeScript, no frameworks. Must work on GitHub Pages and on a phone browser. It reads only the data contract in `DESIGN.md` §6 (`index.json`, `rollup.json`, `cards/scryfall-cache.json`).
- **Images:** never commit card image files. Hotlink `cards.scryfall.io` URLs from the cache only; `small` and `normal` only, never cropped art.
- **Scryfall API:** ≥100 ms between requests to `api.scryfall.com`; set `User-Agent: Vibefish/<version>` in scripts (`runner/scryfall.py` does); leave browser UA alone in page JS. Resolve names in batches via `cards/collection`.
- **Forge:** pinned to the tag in `forge/VERSION` with the checksum in `forge/SHA256SUMS`. Do not float to `latest` or `daily-snapshots` unless `FORGE_CHANNEL=snapshot` is explicitly set; a snapshot build that published runs depend on is pinned exactly with `FORGE_SNAPSHOT_BUILD=<build>` and its checksum recorded in `forge/SHA256SUMS` (the 2026-11-08 build is). The runtime is downloaded by `forge/fetch-forge.sh` into `forge/runtime/` and is never committed.
- **No Forge fork.** `controller/` compiles against the released Forge jar and uses public hooks (event bus, `PlayerControllerAi`). Patch Forge only if a hook is private, and record it in `DESIGN.md`.
- **No upstream filing.** Forge bugs seen in runs are noted in `docs/upstream.md` for our own reference only; this project does not file Forge issues or PRs, so never suggest it.
- **Per-deck bots, not a general bot.** Custom behaviour reaches a seat only through that seat's playbook and data, written for one specific deck (a precon or a deck from the user's meta). Shared behaviour modules are fine, but they stay inert unless a deck's playbook opts in with its own parameters, and seats without a playbook run stock Forge AI, untouched, as the baseline. We are not building a generalised bot: nothing is switched on for every deck regardless of context, and Forge's default AI is not rewritten. Phase 3 data (`playbook/precons/<id>.json`, DESIGN §19) reaches a seat through the harness `--data` and that seat's profile; Forge's role and combo lists are global for a game, so only lines about the deck's own cards go in.
- **Always pass a clock** to sim mode (`-c` / `--clock`). Forge's default is 120 s and declares longer games a draw; Commander games routinely exceed it. The harness also caps turns (`--turn-cap`, default 120).
- **Event schema:** changes to the JSONL events or `run.json` keep `runner/rollup.py` and `DESIGN.md` §6 in sync and bump `VERSION`.
- **License:** this repo is GPL v3 because `controller/` compiles against Forge. Don't vendor non-GPL-compatible code.
- **Naming:** project is "Vibefish". "MTG" / "Magic: The Gathering" appear only descriptively, never in the product name, repo name, or logos.
- **Benchmark pod** in `runner/benchmark-pod.json` is frozen. Do not edit it. The **precon league** in `runner/precon-league.json` (`league-v1`, 91 decks) is frozen too: a different deck list is a new league with a new name.
- **Human references** (`runner/reference/playgroup-commander.json`) are copied from Playgroup.gg's public pages by hand or from one saved page copy, with the retrieval date and the page's CC BY 4.0 licence noted (`runner/reference/transcribe-playgroup.py` reads a saved page file). Nothing in the pipeline fetches playgroup.gg.

## Commands
```
forge/fetch-forge.sh                                   # download + verify + assemble forge/runtime/ (once)
controller/build.sh                                    # javac → controller/out/vibefish-sim.jar (launcher does this automatically)
controller/vibefish-sim.sh check --deck-dir DIR "A.dck" "B.dck"             # unknown/unsupported/AI-flagged cards, conformance
controller/vibefish-sim.sh play --out results/x --deck-dir DIR \
    --deck a=A.dck --deck b=B.dck --deck c=C.dck --deck d=D.dck \
    --games 10 --seed 42 --clock 900 --turn-cap 120 [--profile Default ...]   # JSONL events + run.json
runner/run-pod.sh -n 20 -j 2 -s 42                     # benchmark pod, 2 shards → results/<run-id>/{shard-*,rollup.json}
FORGE_CHANNEL=snapshot FORGE_RUNTIME=$PWD/forge/runtime-snapshot forge/fetch-forge.sh   # daily snapshot, side by side
runner/make-arm-profiles.sh forge/runtime-snapshot     # Vibefish-MC / Vibefish-MCHard / Vibefish-Heuristic AI profiles
runner/run-pod.sh -R forge/runtime-snapshot -m on -p Vibefish-MC,Vibefish-MC,Vibefish-Heuristic,Vibefish-Heuristic -r -n 40 -j 2 -c 1800
                                                       # A/B: Flat Monte Carlo vs heuristic, profiles rotate across seats; rollup reports arms
runner/publish.sh results/<run-id> demo-data           # → demo-data/runs/<run-id>/, scorecard.json, index.json, card cache
runner/scorecard.py results/<run-id>/rollup.json       # sim vs Playgroup human references (runner/reference/playgroup-commander.json)
runner/goldfish.sh /abs/path/Deck.dck -n 8 -s 42        # deck vs three lands-only do-nothing decks → kill-turn distribution in goldfish.json
runner/status.py --port 8787                           # live progress page for runs in results/ (ETA, per-shard pace, interim wins by arm); dev tool, nothing written
runner/playstyle.py results/<run-id> [--by-profile]    # how the seats played, from the event logs: attack frequency/targets, combat damage per turn, mana use, closing speed; an ab.py run dir splits each arm into focus seat and opponents
runner/league.py schedule --seed 20261109 --cycles 25  # the precon league schedule: 91 precons, 22 tables a round, 2200 games, every deck in every seat once a cycle
FORGE_RUNTIME=$PWD/forge/runtime-snapshot runner/league.py play --seed 20261109 --cycles 25 --out results/league-x --shards 20 --shard 1 -j 2
                                                       # one shard of the league locally (110 one-game harness runs); league-run.yml plays all shards in Actions
runner/league.py rollup results/league-x               # per-deck win rates with Wilson intervals (kind: league); publish.sh and scorecard.py handle league runs
runner/deckdata.py generate --runtime forge/runtime-snapshot [--deck ID]   # Phase 3 data drafts: playbook/precons/<id>.json (Spellbook + card scripts); curated blocks survive
runner/deckdata.py forge-lines playbook/precons/token-triumph.json         # the KeyCards, role, combo and pair lines a seat will be given
controller/vibefish-sim.sh play ... --data token-triumph=playbook/precons/token-triumph.json --profile "" --profile Vibefish-token-triumph ...   # one seat with its data
controller/vibefish-sim.sh play ... --playbook token-triumph=playbook/precons/token-triumph.json   # one seat under its playbook (PlaybookController: attack policy, mulligan rule)
runner/ab.py play --deck token-triumph --games 40 --seed 20261110 --out results/ab-token-triumph --runtime forge/runtime-snapshot -j 2 [--arms stock,data,mc,mcdata,mcmax,mcmaxdata,playbook,playbookdata]
runner/ab.py rollup results/ab-token-triumph               # paired A/B: same tables with and without the deck's data; ab-run.yml shards it in Actions
python3 -m http.server 8000                            # then open http://localhost:8000/dashboard/?data=../demo-data
runner/pod-smoke.sh -n 3 -s 42                         # Phase 0 smoke test through Forge's own sim mode
```
Relative paths given to the launcher resolve against the directory you run it from. The harness jar is built per Forge jar under `controller/out/<jar-name>/`; the launcher rebuilds it when sources are newer, so do not run it against a runtime while a long run is using that runtime (the running JVM reads classes from the jar being overwritten). `--mc on|max|lite` switches Forge's Flat Monte Carlo AI on (2.0.16+ builds, no-op on 2.0.15); `--profile` once per seat, `--rotate-profiles` shifts the assignment every game. Bundled Commander precons: `forge/runtime/res/quest/commanderprecons/` (179 decks named `Name [SET] [YEAR].dck`). Forge needs Java 17+ (CI uses Temurin 21). Sim mode does not need card images.

## Forge sim mode notes
Four `-d` decks in plain mode = one 4-player game (confirmed Phase 0). **Never use `-t`/`-p` for Commander:** tournament mode pairs decks 1v1 at 20 life and ignores `-D` for named decks. `-D` must be absolute; quote names with spaces. Per-seat AI profiles: `-a` in sim mode, `--profile` in the harness (`res/ai/*.ai`). Forge's AI prints a `java.util.concurrent.TimeoutException` stack trace when its own decision timeout fires; harmless. Forge's user data is redirected into `forge/runtime/profile/` by the `forge.profile.properties` the fetch script writes.

## Branches
- `testing`: change control. Work lands here first and GitHub Pages serves this branch directly (branch deploy, root; `index.html` redirects to `dashboard/`, `.nojekyll` disables Jekyll), so the live dashboard shows what is being tested. `pod-run.yml` with publish on this branch commits `demo-data/` here.
- `main`: stable. Promoted from `testing` by fast-forward or merge when a milestone is accepted; never pushed to directly.
- `claude/*` and other feature branches: day-to-day work, pushed to their own branch, merged into `testing`.

## Workflows
- `phase0.yml`: Forge sim-mode smoke test on push to `forge/**`, `runner/**`.
- `pod-run.yml` (manual): 4 shards × N games, rollup, optional publish into `demo-data/` on the branch.
- `league-run.yml` (manual): the precon league in up to 20 shards (cycles, seed, Forge channel and snapshot build, profile, Monte Carlo as inputs), rollup and scorecard, optional publish of `rollup.json`, `scorecard.json` and `league.json` into `demo-data/` on the branch. Per-game data stays in the run's artifacts.
- `ab-run.yml` (manual): paired A/Bs of per-deck data for a list of decks (tables, arms, shards per deck), one rollup per deck as artifacts; nothing is committed.
- Pages: no workflow. The `testing` branch is served as-is; a push there is live within about a minute. Workflows that are `workflow_dispatch`-only (`pod-run.yml`) can only be started once they exist on the default branch.

## Key links
- Forge AI / sim flags: https://github.com/Card-Forge/forge/wiki/AI
- Forge sim mode source: https://github.com/Card-Forge/forge/blob/master/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java
- Forge game events: https://github.com/Card-Forge/forge/tree/master/forge-game/src/main/java/forge/game/event
- Forge releases: https://github.com/Card-Forge/forge/releases
- Forge card scripting (AILogic, RemAIDeck): https://github.com/Card-Forge/forge/wiki/Card-scripting-API
- Scryfall API: https://scryfall.com/docs/api
- WotC Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

## Session start checklist
- Check https://github.com/Card-Forge/forge/releases against `forge/VERSION`, and skim recent Card-Forge PRs touching `forge-ai/` (kevlahnota's Flat Monte Carlo series) for anything that changes the AI we measure. No scheduled jobs: this is done by hand.
- `git log --oneline -5 testing` and `demo-data/index.json` to see what the last session published.

## Status
- Phase 0 (spike): done 2026-11-08 — `DESIGN.md` §14.
- Phase 1 (goldfish): done 2026-11-08 — harness, runner, rollup, resolver, dashboard, workflows; `DESIGN.md` §15.
- Phase 2 (measure) is under way, re-cut after the prior-art survey (`DESIGN.md` §16); Monte Carlo A/Bs in §17: 40 games at Default budgets 55/45, 120 games at `--mc max` 57/43 (95% 48–65%), a lean, not a result, and Forge's question rather than ours; goldfish mode and the calibration scorecard exist. The measured gap to human play is combat, not casting (§17: bots attack on a third of their turns in rounds 5–8 and never gang up on the leader; first elimination at round 9, where human games end). The four-profile run (§17) found the profile knobs move aggression by a fraction of a creature per turn and leave the game's shape untouched (Default 25%, Reckless 22%, Cautious 30%, Experimental 23% of 60 games, all within noise; whole tables of Default and of Reckless on identical seeds both average 47 turns). Decision 2026-11-08: per-deck bots, not a general bot (hard constraint above); behaviour reaches a seat only through its deck's playbook, shared modules stay inert without one. The combat numbers are measurements in §17, not a work item. Decision 2026-11-09: the precon league first (§18): 91 Forge-bundled precons scored against Playgroup's 92-precon human table (`runner/precon-league.json`, `runner/league.py`, `league-run.yml`, league view on the dashboard). First full run published the same day (2,200 games, snapshot 2026-11-08, Monte Carlo off, 20 Actions shards in 3 h): Spearman 0.266 with the human ordering over 91 precons (0.281 over the 74 with 100+ human games), mean gap 8.1 points, sim spread 2.5x the human one; 17 of 25 human A/B-tier decks in the sim's top half. The misses cluster by archetype: creature, lifegain and ramp decks over-rated (Calling All Angels 62% vs 22%), planeswalkers, lands, tokens, artifacts and storm under-rated (Planeswalker Party human #1 vs sim #36, Token Triumph #8 vs #82, Goblin Storm 5%). Calibration unchanged from the pod (mulligan 23% vs 36%, 12.0 rounds vs 8.75). Same-seed games match across machines 86% of the time (the AI's wall-clock budgets). Phase 3 started the same day (§19): per-deck data for Forge's AI (key cards, roles, combos, deck plan, profile knobs) generated for all 91 league decks by `runner/deckdata.py`, curated for the four first bots (Token Triumph, Goblin Storm, Tricky Terrain, Hail, Caesar), fed per seat by the harness `--data`, measured by the paired A/B `runner/ab.py` / `ab-run.yml` (arms stock, data, mc, mcdata). First full A/B (four decks, 100 tables, arms stock/data/mc/mcdata, 1,600 games in Actions, `demo-data/ab/2026-11-09-ab-v1/`): no arm beats stock clearly; Tricky Terrain leans up with everything (+7 to +10 points, exact test 0.08 for mcdata), Token Triumph leans down with its data (−7), Goblin Storm stays at 5–9%, Hail, Caesar unchanged. The knobs barely change play (PLAY_AGGRO: attack turns 29% vs 31%), Monte Carlo at Default budgets plays the same game. Phase 3's exit criterion is not met by v1. Phase 4 started the same day (§20): `PlaybookController` (Forge's AI controller subclassed, installed per seat by `--playbook`) with a go-wide attack policy and a mulligan rule, parameters in the deck file's `playbook` object; Token Triumph, Goblin Storm and Hail, Caesar carry the go-wide playbook; measured by the `playbook` and `playbookdata` arms of `ab.py` / `ab-run.yml` (first A/Bs running), with the `mcmax` arms as the other open check (Tricky Terrain). Then the league again on the 2.0.16 release when it lands. The snapshot's plan-aware mulligan (`FLAT_MC_MULLIGAN`, default on) is already in every snapshot arm. Phase 3 feeds Forge's AI per-deck data (combo lines, card roles, key cards) instead of scripting lines ourselves. Check upstream Forge AI work (Card-Forge PRs by kevlahnota, `forge-ai/src/main/java/forge/ai/simulation`) before building any AI feature here.

## Required README footer
> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
