# Vibefish — Design Doc v0.2

*Commander deck playtesting for Magic: The Gathering, built on Forge's headless sim mode.*

Status: Phase 0 and Phase 1 complete (2026-11-08); Phase 2 next. Companion project to VibeTutor. Phase 0 findings are in §14, Phase 1 in §15.

---

## 1. What this is

Vibefish takes a Commander decklist, runs it through hundreds of AI-vs-AI games in Forge, and produces data a human (or VibeTutor) can act on: consistency stats, failure modes, matchup win rates, and replayable board states. Over time it grows deck-specific AI pilots ("playbooks") that play a given deck far better than Forge's stock AI, without an LLM making per-decision calls.

The core insight: **the LLM writes the pilot, it doesn't fly the plane.** Expensive reasoning happens once, offline, and ships as a cheap deterministic policy into the match loop.

## 2. Goals / non-goals

**Goals**
- One-command playtest: drop a `.dck` in, get a report out.
- Goldfish-grade consistency stats that are reliable even with a dumb pilot.
- A public GitHub Pages dashboard with real card images (via Scryfall) showing deck stats, matchup grids, and step-through board states.
- Deck-specific playbooks that encode mulligan rules, sequencing, and explicit combo lines.
- A feedback loop: LLM drafts playbook → sim → LLM reads losses → revises playbook.
- Clean handoff from VibeTutor: VibeTutor exports a list, Vibefish returns numbers VibeTutor can use in its next suggestion pass.

**Non-goals (for now)**
- A new rules engine. Forge is the engine.
- LLM-per-decision gameplay. Too slow, too expensive, too unreliable on board state.
- Multiplayer politics modeling. The AI won't negotiate; we accept that.
- Any hosting beyond GitHub + Cloudflare free tiers.

## 3. Architecture

Two public repos.

```
vibefish/                      (engine — this repo, GPL v3)
├── VERSION                    Vibefish version: stamped into results, used in the Scryfall User-Agent
├── forge/                     VERSION + SHA256SUMS pin, fetch-forge.sh, forge.sh (runtime downloaded, never committed)
├── controller/                Java compiled against the released Forge jar, no fork:
│   ├── src/vibefish/Sim.java              `play` (games → JSONL events + run.json) and `check` (deck validation)
│   ├── src/vibefish/JsonGameLogger.java   event-bus subscriber, turn snapshots, turn cap
│   ├── src/vibefish/PlaybookController.java   Forge's AI controller with a deck's playbook on top (Phase 4: cast rules, attack policy, mulligan rule)
│   ├── src/vibefish/VibefishLobbyPlayer.java  the lobby player that installs it for one seat; Playbook.java holds the parameters
│   ├── src/vibefish/DeckCheck.java
│   └── build.sh, vibefish-sim.sh          javac build, launcher
├── runner/                    benchmark-pod.json (frozen), run-pod.sh (sharded pod runs), rollup.py,
│                              precon-league.json (frozen, 91 precons), league.py (league schedule, play, rollup),
│                              deckdata.py (Phase 3 data generator), ab.py (paired A/B of one deck's data),
│                              reference/ (Playgroup.gg figures), scorecard.py, scryfall.py (name → image cache),
│                              publish.sh (run → data directory), goldfish.sh, playstyle.py, hands.py (one seat's cards and mana),
│                              losses.py (how an A/B's seat played the table and lost), cardplay.py (what a seat did
│                              with each card it drew, against people's per-card figures), status.py
├── playbook/                  README (data schema), precons/<id>.json per league deck (Phase 3 data: key cards, roles, combos,
│                              pairs, deck plan, profile overrides; generated + curated blocks), precons/spellbook/ provenance
├── dashboard/                 vanilla JS static site: index.html, app.js, style.css
├── demo-data/                 pod results + card cache the public dashboard reads (layout in §6)
├── .github/workflows/         phase0.yml (smoke), pod-run.yml (sharded pod runs), league-run.yml (sharded league runs), ab-run.yml
│                              (sharded paired A/Bs of per-deck data, artifacts only), pod and league with
│                              optional publish; Pages is a branch deploy of `testing`, no workflow
└── DESIGN.md

vibefish-data/                 (Andrew's decks — public, separate repo)
├── decks/*.dck
├── playbooks/*.json
├── results/<run-id>/*.json
├── cards/scryfall-cache.json  name → {scryfall_id, image_uris}
└── .github/workflows/sim.yml  checks out vibefish, runs, commits results
```

Separation of concerns: engine is generic and reusable by anyone; data repo is one person's decks. The dashboard can point at any data repo via `?data=` URL param.

### 3.1 Components

**Runner.** `runner/run-pod.sh` plays the benchmark pod through the harness in parallel shards (one JVM each, ~4 GB heap and ~1.5 cores while a game runs), resumes a shard after a wall-clock exit, and rolls the shards up; `-k` runs a single shard so CI uses one job per shard. `runner/rollup.py` (Python, stdlib) turns `run.json` plus event streams into `rollup.json` (§6) and maintains `index.json`. `runner/publish.sh` copies a finished run into a data directory with gzipped events, writes the calibration scorecard and resolves new card names. `runner/scorecard.py` compares a rollup with the human references in `runner/reference/playgroup-commander.json` (stock-precon win rates and their rank order, first-seat advantage, mulligan rate, lands in the kept hand, rounds per game); the dashboard shows it as a calibration card. The references are copied by hand from Playgroup.gg's public pages with the retrieval date, never scraped. Any other decks go straight through `vibefish.Sim play` (`--deck id=file.dck`); a manifest-driven runner for the data repo comes with Phase 2. `runner/goldfish.sh` plays one deck against three lands-only, commander-less "do-nothing" decks (`runner/goldfish/Goldfish-Plains.dck`) and reports the own-turn kill distribution, which isolates a deck's speed and consistency from table interaction; a precon goldfish game takes 10–20 s. `runner/playstyle.py` reads the event logs of finished runs and reports how the seats actually played, by arm or by AI profile: attack frequency, attackers and combat damage per own turn, defender choice against the weakest player and the biggest board, attackers received per deck, approximate mana use, idle turns, and closing speed (first elimination, kills by the eventual winner); it is the instrument behind §17's combat findings. `runner/hands.py` reads the same logs for one seat: a game turn by turn (the hand, every spell with its targets, every ability, the attacks), the cards the seat kept in hand on turns when its unspent mana would have paid for them, and the paired kill-turn comparison of two goldfish runs on the same seeds; it is the instrument a playbook's cast rules are written from (§21). `runner/losses.py` reads an A/B run for the seat under test, arm by arm: whether it was the first or the last out, its hand and board on its last turn, who dealt the last blow, how many spells it aimed at opponents and how many attackers it blocked (§23). `runner/league.py` plays the precon league (§18): a frozen list of 91 bundled precons (`runner/precon-league.json`) over random four-player tables with seats balanced, one harness process per game, sharded the same way, with its own rollup (per-deck win rates with Wilson intervals, `kind: league`) that `publish.sh` and the scorecard understand. Defaults: clock 900 s for pods and 1800 s for the league (Forge's own 120 s default declares longer Commander games a draw) and a turn cap of 120 Forge turns, i.e. 30 rounds of four.

**Forge integration (no fork).** Forge is consumed as a library. The released desktop jar goes on the classpath and `controller/` provides its own entry point that repeats sim mode's ~100 lines of setup (`FModel.initialize`, `RegisteredPlayer.forCommander`, `Match`, `Game`) and then does what sim mode cannot:
- subscribes a `JsonGameLogger` to the game's public event bus (`Game.subscribeToEvents`). Events are Java records carrying the data we need: zone changes with from/to zone, casts with host card and targets, turn began with number and owner, life changes, mulligans, land drops, attackers declared, game outcome with each player's `GameLossReason`;
- seeds `MyRandom` per game and records the seed;
- enforces a turn cap next to Forge's wall-clock cap;
- streams JSONL while the game runs, so a killed job still yields partial data.

Sim mode in 2.0.15 already has an RNG seed (`-s`), per-seat AI profiles (`-a`) and a clock (`-c`), so nothing is patched. If a needed hook ever turns out to be private, the fallback is a build-time patch, declared here.

Built in Phase 1 as `controller/src/vibefish/`. `Sim.play` boots Forge the way sim mode does (`GuiBase.setInterface(new GuiDesktop())`, `FModel.initialize`), registers seats with `RegisteredPlayer.forCommander`, seeds `MyRandom` per game, creates a fresh `Match` and `Game` per game, subscribes `JsonGameLogger`, and runs the game on a daemon thread under the clock. After a timeout the process exits with code 3 so the stuck game thread cannot affect later games; the runner resumes with `--start`. A capped or timed-out game is recorded as a draw with no winner, whatever Forge marks (its forced game-over flags every survivor as a winner). The logger reads live state from `Game` and `Player` at every turn start (hands, lands, life, zone sizes, commanders in the command zone) and infers the zone a spell was cast from by tracking zone changes. Forge's AI prints a `java.util.concurrent.TimeoutException` stack trace whenever its own per-decision timeout fires; that is noise, the game continues. Boot takes ~6 s; a 4-player precon game 30–140 s. Compile with `controller/build.sh` (javac, release 17, Gson and Guava come from the Forge jar), one build per Forge jar under `controller/out/`. For A/B runs the harness switches Forge's Flat Monte Carlo on per game (`--mc`, by reflection so it still compiles against 2.0.15), takes one AI profile per seat and rotates the assignment by one seat every game (`--rotate-profiles`), and records the profile per seat; `runner/make-arm-profiles.sh` writes the arm profiles (Monte Carlo on, Monte Carlo with Hard budgets, heuristic via `FLAT_MC_ENABLED=false`) and `runner/rollup.py` reports wins by arm with a Wilson 95% interval.

**PlaybookController.** Java class extending Forge's `PlayerControllerAi`, created by our own `LobbyPlayer` so Forge itself is untouched. On each decision point:
1. Check playbook for a matching rule → execute it.
2. Else fall through to stock Forge AI.

Built so far (§20, §21): the attack declaration, the mulligan, and since 0.3.0 the play itself (`chooseSpellAbilityToPlay`: which card to cast or ability to use, when, and aimed at what).

Phase 2 starts one level below this: a per-deck AI *profile*. Forge profiles are plain `key=value` files (`res/ai/*.ai`) with roughly 150 tunables — mulligan threshold, aggression, counterspell thresholds, named-card lists — and sim mode assigns one per seat. That is zero Java and measurable immediately. The controller then handles only what profiles cannot express: hold rules, card priority, scripted combo lines (Phase 3). Phase 4 evaluates Forge's own lookahead before we build any (§7).

**Playbook.** JSON, one per deck. Human-readable, LLM-writable. See §5.

**Scryfall resolver.** Workflow step: for every unique card name in decks + results, resolve once via the `cards/collection` endpoint (75 identifiers per POST, so a deck is two requests), ≥100 ms between calls, proper User-Agent; cache `scryfall_id` and `image_uris` in the data repo. Dashboard hotlinks `cards.scryfall.io` — no image files in git.

**Dashboard.** Vanilla JS, no build step, GitHub Pages. Reads JSON over `raw.githubusercontent.com` (or local path). Views: deck overview, run history, matchup grid, per-game timeline, board-state viewer, "cards that never got cast" list, playbook diff. Board states are reconstructed from the recorded event stream, never by re-simulating.

## 4. The pipeline

```
VibeTutor / Moxfield export
        │
        ▼
   convert → .dck ──► runner ──► Forge sim (4-player pod)
                                      │
                                      ▼
                             per-game JSON events
                                      │
                           ┌──────────┴──────────┐
                           ▼                     ▼
                     rollup stats           post-mortems
                           │                     │
                           ▼                     ▼
                      dashboard         LLM playbook revision
                                                 │
                                                 └──► playbook vN+1 → runner
```

### 4.1 Benchmark pod

Win rates are meaningless without a fixed opponent pool. The pod is four Forge-bundled Commander precons, chosen 2026-11-08 and frozen in `runner/benchmark-pod.json`:

| Seat id | Precon | Commander | Set | AI-flagged cards |
|---|---|---|---|---|
| `mutant-menace` | Mutant Menace | The Wise Mothman | PIP 2024 | 5 never / 5 random |
| `blight-curse` | Blight Curse | Auntie Ool, Cursewretch | ECC 2026 | 4 / 5 |
| `veloci-ramp-tor` | Veloci-Ramp-Tor | Pantlaza, Sun-Favored | LCC 2023 | 1 / 4 |
| `squirreled-away` | Squirreled Away | Hazel of the Rootbloom (Chatterfang, Squirrel General in the 99) | BLC 2024 | 4 / 2 |

"AI-flagged" counts cards Forge marks `AI:RemoveDeck:All` (the AI should never pilot them) and `AI:RemoveDeck:Random` (kept out of random decks only). The median bundled precon has 4 "never" cards, so the pod is typical.

The four precons play each other in one 4-player game. Expected win share is 25% each; the measured spread is the pod's own power calibration, and every stat in §6 is reported per deck from these games. "Mirror pods" (your decks vs. each other) stay a secondary view. If the pod ever changes, that is a new pod with a new name and history restarts.

### 4.2 Sample size

Four-player games have a 25% baseline. Expect to need ~200+ games per deck for win-rate signal; consistency stats (land drops, commander turn) stabilize much faster (~50 games).

Measured cost (Forge 2.0.15, stock AI, bundled precon pod, 4-core machine): **98 s per game** averaged over 10 games, median 66 s, range 44–247 s, plus ~11 s of JVM and card-database start per process. A game uses ~1.5 cores, so a 4-core runner plays two at once. 200 games is ~5.5 CPU-hours; sharded over ten Actions jobs of 20 games it finishes in under an hour, free on public repos.

## 5. Playbook schema (sketch)

```json
{
  "deck": "atraxa-superfriends",
  "version": 3,
  "mulligan": {
    "keep_if": ["lands >= 3 && lands <= 5", "has_ramp_or_draw"],
    "max_mulligans": 2
  },
  "priority": {
    "early":  ["Sol Ring", "Arcane Signet", "..."],
    "mid":    ["..."],
    "late":   ["..."]
  },
  "hold": [
    { "card": "Counterspell", "when": "any_opponent.mana >= 7" }
  ],
  "lines": [
    {
      "name": "Infinite turns",
      "requires": { "battlefield": ["A"], "hand": ["B"], "mana": 6 },
      "steps": ["cast B", "activate A target B", "respond C"]
    }
  ],
  "threats": {
    "commanders": { "Yuriko": "high", "Urza": "critical" }
  }
}
```

Conditions use a tiny expression language evaluated against a flat game-state view. Keep it boring and greppable. Open option (§13): reuse Forge's own card-script `Valid`/`Count$` syntax, which the AI already evaluates against live state, instead of inventing one.

The sketch above is the v0.1 intent. What exists is documented in `playbook/README.md`: `attack` and `mulligan` (§20) and the `cast` rules (§21: `play`, `activate` and `hold` with text conditions such as `creatures >= 3` and `controls Zada, Hedron Grinder`, and a `target` to aim at). `priority`, `hold` and `lines` of the sketch are all written as cast rules; `threats` is not built.

## 6. Results schema

Everything the harness writes is JSON.

**Event stream** — `games/game-NNN.events.jsonl`, one object per line; a 4-player game is roughly 700 lines and 130 KB (15–20 KB gzipped). Every line has `e` (type) and `t` (Forge's global turn number, 0 before turn 1). Seats are indices into the run's deck list.

| `e` | fields |
|---|---|
| `meta` | game, seed, vibefish, forge_version, turn_cap, clock_s |
| `game_start` | first_seat |
| `turn` | seat, own_turn, state[] per seat: alive, life, poison, hand (names), hand_lands, lands, bf, lib, gy, cmd (commanders still in the command zone) |
| `mulligan` | seat |
| `land` | seat, card, id |
| `cast` | seat, card, id, spell (false for activated and triggered abilities), commander, from (zone before the stack), ability (text, abilities only); since 0.3.0 copy (true for a copy of a spell, as Zada, storm and replicate make them: no card left a zone for it; in older logs a copy is a spell with `from` null), targets[] (names of the cards targeted, sub-abilities included) and target_seats[] |
| `resolve` | card, id, fizzled (spells only) |
| `zone` | seat (owner), card, id, from, to, token |
| `life` | seat, from, to |
| `damage` | seat, amount, combat, infect, source, source_seat, source_commander |
| `poison` | seat, from, amount, source_seat |
| `attack` | seat, attacks[] {attacker, defender, defender_seat, planeswalker} |
| `block` | seat, blocks[] {attacker, blockers[]}; an empty `blockers` list means unblocked (Forge lists an unblocked attacker as its own blocker; stripped since 0.1.1, so `block` events before 0.1.1 overstate blocking) |
| `lost` | seat, reason (Forge `GameLossReason`), life |
| `cap` | turn_cap (the game is declared a draw) |
| `outcome` | winner_name, lines (Forge's own outcome text) |
| `game_end` | winner (seat or null), reason, duration_ms, players[] {seat, won, lost, reason, turn_lost, life, poison, mulligans, turns_played} |

`game_end.reason` is Forge's `GameEndReason` (`AllOpponentsLost`, `WinsGameSpellEffect`, …) or a harness value: `TurnCap`, `Timeout`, `Exception`. Player `reason` is `LifeReachedZero`, `CommanderDamage`, `Poisoned`, `Milled`, `SpellEffect`, `OpponentWon`, `Conceded`, or `Draw` for a capped or timed-out game.

**Run summary** — `run.json` per shard: vibefish, forge_version, forge_build, format, seed_base, clock_s, turn_cap, games_requested, decks[] {seat, id, file, name, commanders, profile, main_count, commander_cards[], cards[] {name, count, type, cmc, land}, since 0.2.0 `data` {file, key_cards[], key_cards_applied, roles, combos, pairs, deck_plan} for a seat given `--data`, and `playbook` {file, version, attack {policy, target, min_attackers, safety_margin, max_reserve, spread}, mulligan, cast (0.3.0: the playbook's `cast` object as written), triggers (0.3.1: its `triggers` array as written, null when it has none)} for a seat given `--playbook`}, `ai_lists` {applied, roles, combos, pairs} (0.2.0, the lines added to Forge's AI lists for the run, null when none), games[] (the `game_end` fields plus index, seed, events path, first_seat, turns, and `playbook_stats`, the playbook's counters for the game: the `attack_*` and `mulligan*` counters, since 0.3.0 the `cast_*` ones and since 0.3.1 the `trigger_*` ones, all listed in `playbook/README.md`).

**Rollup** — `rollup.json` per run, from `runner/rollup.py`: run_id, forge_version, pod, games, completed_games, drawn_games, shards, seeds, clock_s, turn_cap, avg_game_turns, avg_game_seconds, decks[], `deck_stats[]` per seat (games, wins, losses, draws, win_rate, loss_reasons, avg_turns_played, mulligan_rate, avg_mulligans, opening_hand_lands_avg, land_drop_rate[12], lands_by_turn[12], hand_by_turn[12], life_by_turn[12], games_reaching_turn[12] — all indexed by the deck's own turn — commander {first_cast_turns, avg_first_cast_turn, never_cast_games, casts_per_game}, damage {dealt_per_game, taken_per_game, commander_dealt_per_game}, never_cast, drawn_never_cast, cards[] {name, count, type, cmc, land, drawn, cast, played, games_drawn, games_cast}), and `game_summaries[]`.

**League rollup** — `rollup.json` from `runner/league.py rollup` (§18) has the same top-level fields plus `kind: "league"`, `seats_per_game: 4`, `seat_win_rate[4]`, `profile`, and `league {name, decks, seed, cycles, rounds, tables_per_round, byes_per_cycle, games_scheduled, games_played, games_missing, games_per_deck_avg, chosen_on, chosen_with}`. `decks[]` is the league file's list; `deck_stats[]` is one entry per deck (sorted by win rate) with the per-seat fields above except `seat` and `cards`, plus `set`, `year`, `reference_name` (the Playgroup name), `win_rate_ci95` (95% Wilson), `games_by_seat[4]`, `wins_by_seat[4]`. `game_summaries[]` entries add `game` (schedule index), `cycle`, `round`, `seats[]` (deck ids in seat order), `winner_id`, and drop `profiles` and `mc_stats`; `winner` and `first_seat` stay seat indices. A league played with `league.py play --playbooks` also lists `playbooks`, the ids of the decks that sat under their shipped playbook (empty otherwise); the per-deck numbers have the same shape either way.

**Scorecard** — `scorecard.json` from `runner/scorecard.py`, next to the rollup: `metrics.precon_win_rate {rows[] {deck, id, sim_win_rate, sim_win_rate_ci95, sim_games, human_win_rate, human_games, human_tier, difference, sim_rank, human_rank}, decks_compared, spearman_rank_correlation, pearson_correlation, mean_abs_difference, sim_sd, human_sd, well_measured {min_human_games, decks_compared, spearman_rank_correlation, pearson_correlation}}`, `first_seat_win_rate {sim, sim_games, human, even, sim_by_seat, human_by_seat}`, `mulligans_taken`, `opening_hand_lands`, `rounds_per_game`.

**Data directory** — what the dashboard reads (`demo-data/` in this repo, the data repo later), written by `runner/publish.sh`:

```
index.json                      {"runs":[{id, generated, forge_version, pod, kind?, games, path}]}   kind "league" for league runs
cards/scryfall-cache.json       name → {id, set, collector_number, scryfall_uri, image_uris{small,normal}, …}
bots.json                       optional; {kind "bots", bots[] {deck, name, commanders, status, playbook, summary, human {win_rate, games},
                                tables {run, seed, stock {games, wins, win_rate, win_rate_ci95}, bot {...}, difference, difference_ci95,
                                bot_only, stock_only, exact_p, source} | null, goldfish {games, stock_kill_turn, bot_kill_turn, faster_by,
                                faster_by_ci95, source} | null}} from runner/bots.py and playbook/bots.json; shown above every run
runs/<run-id>/rollup.json
runs/<run-id>/scorecard.json
runs/<run-id>/shard-N/run.json                          pod runs only
runs/<run-id>/shard-N/games/game-NNN.events.jsonl.gz    pod runs only
runs/<run-id>/league.json                               league runs: seed, cycles, shards, runtime, deck ids, league_file (the schedule is derived)
```

Seeds: shard `j` of a pod run uses `seed + 100000·j`, and game `i` within a shard uses `shard_seed + i`, so any game can be replayed from its `meta` line; league game `i` uses `seed + i + 1` with the seats listed in its summary. Every file carries `forge_version`.

## 7. Roadmap

| Phase | Deliverable | Done when |
|---|---|---|
| 0 Spike | Forge runs 4-player Commander sim headless on a local machine and in Actions | **Done 2026-11-08** (§14): 12/12 local games and 3/3 Actions games completed |
| 1 Goldfish | Harness (JSON event logger, seeds, turn cap) + runner + rollup + first dashboard | **Done 2026-11-08** (§15): pod stats for four decks with card images at https://lt-lit.github.io/vibefish/ |
| 2 Measure | A/B of Forge's Flat Monte Carlo AI against the heuristic AI on the pod (snapshot channel), seat-balanced, with confidence intervals; goldfish mode; calibration scorecard against Playgroup's human data over a large precon round robin; per-deck AI profile experiments | A/B result and scorecard v1 (rank correlation over ≥ 24 precons) on the dashboard. A/Bs done (§17); the precon league that delivers the scorecard is built (§18, 91 precons), first full run pending |
| 3 Teach | Per-deck AI data generated from the list: Commander Spellbook + an LLM read produce Forge's combo lines, card roles and key cards | A data-fed deck beats the same deck without data in an A/B. Generator, data files for all 91 league decks, harness `--data`, paired A/B runner and workflow built 2026-11-09 (§19); four decks curated. **Not met:** over 200 tables a deck no data arm beat stock (§19), and key cards for the tutors added nothing on top of a playbook (§22) |
| 4 Pilot | PlaybookController only for what data cannot express (hold rules, sequencing); LLM post-mortem loop revising data and playbook from losses | Revision v2 beats v1 in an A/B. Controller built 2026-11-09 with a go-wide attack policy and a mulligan rule (§20); cast rules 2026-11-10 (§21): Goblin Storm's playbook v2 kills a goldfish table two turns sooner than stock and wins 40 of 200 tables in Actions against stock's 18 (+11 points, 95% +5 to +17): met for Goblin Storm. Trigger rules and the table tools 2026-11-11 (§22): **met for four decks**, with Token Triumph (+12 points where its rules were chosen, +10.5 on tables of its own), Hail, Caesar (+7.5 in a second run of new games) and Tricky Terrain (+9); Goblin Storm's version 3 on tables of its own: +15 (§23) |
| 5 Eval model | Small learned board evaluator trained on sim data | Stretch |

Phase 0 and 1 are the prototype. Phases 2–4 were re-cut after the prior-art survey (§16): Forge's own AI now carries the search and the deck knowledge, so Vibefish measures, feeds and calibrates it rather than replacing it. Follow upstream closely (Card-Forge PRs by kevlahnota and the `forge-ai/simulation` package) before building any AI feature here.

## 8. Decisions made

- **Engine:** Forge. Headless sim mode, Commander format flag, plain multi-deck mode for 4-player pods, GPL, near-complete card coverage.
- **Forge integration:** library-style harness compiled against the released jar; **no fork, no patches.** Decided after reading sim mode's source: the seed and per-seat profile flags exist, and the event bus gives structured data.
- **Forge version:** pinned to `forge-2.0.15` (checksum in `forge/SHA256SUMS`) for Phases 0–1. The next bump is the first exercise of the upgrade pipeline (§11).
- **Pilot strategy:** measure and feed Forge's AI before replacing any of it: A/B against upstream's Flat Monte Carlo, per-deck data files (combos, roles, key cards) generated from the list, profiles for tuning, and a PlaybookController only for what data cannot express. Track upstream AI work; nothing is contributed back (§8, no upstream filing).
- **Benchmark pod:** the four precons in §4.1, frozen.
- **Build tooling:** plain `javac` against the release jar, driven by a shell script. Maven only if the Java grows.
- **Repos:** engine and data split, both public.
- **Images:** Scryfall hotlinks only. No image files in any repo.
- **Dashboard stack:** vanilla JS, no build tools, GitHub Pages.
- **Compute:** local via Claude Code for iteration; GitHub Actions for batch runs, started by hand. No dedicated server, no scheduled jobs: Forge releases and upstream AI work are checked manually at the start of a session.
- **No upstream filing:** Vibefish is a personal project, not a Forge contributor. Forge bugs and AI quirks seen in runs go into `docs/upstream.md` for our own reference, so they are not re-diagnosed; nothing is filed or contributed back, and no plan depends on an upstream fix landing.
- **Per-deck bots, not a general bot (2026-11-08):** custom behaviour reaches a seat only through that seat's playbook and data, written for one deck (a precon or one of the user's own) in a known meta; a scripted bot has a chance of playing like a human only when it is built for one deck. Shared behaviour modules (threat model, blocker policy, hold rules) are allowed so playbooks do not copy each other, but they are inert unless a playbook opts in with its own parameters, and seats without a playbook run stock Forge AI, untouched, which keeps the baseline for same-deck A/Bs. Nothing is switched on for every deck regardless of context, and Forge's default AI is not rewritten.
- **Replays:** from the recorded event stream. Seeds are for reproducing a single game while debugging.
- **Name:** Vibefish. "MTG"/"Magic" stay out of the name and appear only descriptively.
- **Precon league (2026-11-09):** the yardstick for "plays precons like people" is Playgroup.gg's stock-precon table, the largest human reference there is (92 precons, 28,726 stock games, CC BY 4.0). `league-v1` is the 91 of those precons that Forge bundles, frozen like the pod; random four-player tables with seats balanced per cycle, one harness process per game, sharded in Actions. A league publishes its rollup, scorecard and league file, not per-game event streams (any game is reproducible from seed and seats on the same build). The first run uses the 2026-11-08 snapshot, pinned by checksum, with Forge's default AI and Monte Carlo off: the stock baseline a per-deck bot will be measured against. Human references are transcribed from a saved copy of the public page with the retrieval date; nothing in the pipeline fetches playgroup.gg.

## 9. Risks

- **Multiplayer sim stability.** *Resolved in Phase 0:* plain mode with four decks seats all four in one Commander game. Tournament mode (`-t`/`-p`) pairs decks 1v1 at 20 life and ignores the deck folder for named decks; never use it for Commander.
- **Forge's default clock.** `-c` defaults to 120 s and declares the game a draw; 4 of 15 Phase 0 games ran longer. The runner always sets it. Forge has no turn cap; the harness adds one.
- **Ordering nondeterminism.** The same seed replays the same game on the same machine, but the listing order of simultaneous events (declared attackers, their blocks) varies between runs, and across machines about one game in seven diverges because Forge's AI decides under wall-clock budgets (§18). Diffs and regression comparisons must be order-insensitive; the recorded log is the replay source.
- **Upstream AI churn.** Forge master (Oct–Nov 2026) added flat Monte Carlo, deck-plan detection, combo recognition and plan-aware mulligans. The first bump after 2.0.15 will move every baseline. Never average across `forge_version` (§11 step 4).
- **Forge release churn.** Monthly releases change card scripts and occasionally AI internals. Pin a release; bump deliberately.
- **`.dck` conversion edge cases.** Split/MDFC/adventure cards, set-specific names. The converter emits bare card names (Forge's pinned form is `Name|SET|artIndex`, not collector number); validate every deck with Forge's own conformance check and card database before running.
- **RemAIDeck cards.** Forge marks some cards AI-unplayable (`AI:RemoveDeck:All`, ~7% of scripts). Read the flags off Forge's card rules and report them per deck up front — the pilot will never cast them.
- **Stalled games.** Draw-go forever. Hard turn cap (e.g., 30 turn cycles) plus wall-clock timeout; record as a draw.
- **Signal vs. noise.** Stock AI misplays dominate win rates in Phase 1. Lean on consistency stats until Phase 2 improves the pilot.
- **Scryfall rate limits.** Resolve in the workflow, cache aggressively, never hammer from the browser.
- **Snapshot builds disappear.** Forge's `daily-snapshots` release is rebuilt every day and old tarballs are eventually dropped, so a run on a snapshot is reproducible only while its tarball exists. `FORGE_SNAPSHOT_BUILD` pins one build and `forge/SHA256SUMS` carries its checksum; a release tag is the durable baseline, so the league is re-run on each release bump (§11 step 3). Since 2026-11-11 a snapshot build that published runs depend on is also kept by us: `forge-archive.yml` packs its assembled runtime and attaches it to this repository's release `forge-runtimes`, `forge/SHA256SUMS` lists the archive, and `forge/fetch-forge.sh` fetches a pinned build from there once it is listed (§22). The 11-08 and 11-10 builds are archived.

## 10. Licensing and attribution

- Engine repo: GPL v3 (required — PlaybookController compiles against Forge).
- Playbooks and decks: data, licensed separately (CC0 or MIT in data repo).
- README footer: *"Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC."*
- Scryfall attribution per https://scryfall.com/docs/api. Never crop copyright/artist lines, never alter images.
- Forge: https://github.com/Card-Forge/forge — credit in README.

## 11. Keeping up with new sets

Forge does the hard part (scripting every new card). Vibefish's job is to track Forge without breaking.

**How Forge ships:** a tagged release per major set, named after the set (`forge-2.0.13` "Marvel Super Heroes", `forge-2.0.15` "Reality Fracture", etc.), roughly every 1–2 months, plus a rolling `daily-snapshots` pre-release on the same GitHub Releases page rebuilt every day. New-set card scripts land in snapshots during spoiler season, well before the tagged release. The release asset is a single `forge-installer-<version>.tar.bz2` (~283 MB) with no top-level directory; the snapshot asset carries a build date in its name and must be discovered through the releases API.

**Vibefish update cycle (manual, no scheduled jobs):**

1. **Watch.** At the start of a session, check `https://github.com/Card-Forge/forge/releases` (and the AI work on master) against `forge/VERSION`. New tag → a commit bumping `forge/VERSION` and `forge/SHA256SUMS` on a branch.
2. **Rebuild.** CI downloads the new release, verifies the checksum, and recompiles `controller/` against the new jar. Compile errors are the only "conflicts" now; Claude Code fixes them in the PR.
3. **Regress.** CI runs the frozen benchmark pod for 50 games on the new build and diffs rollup stats against the previous version. Forge AI changes shift baselines — a big swing means "investigate," not "ship."
4. **Stamp.** Every result file carries `forge_version`. The dashboard segments history by it so pre- and post-upgrade numbers never get averaged together.
5. **Merge.** PR merges, data repo picks up the new engine on its next run.

**Deck-side:** the runner validates every `.dck` against the pinned Forge card database before running. Cards Forge doesn't know yet fail fast with a list. For spoiler-season testing, a `FORGE_CHANNEL=snapshot` flag swaps in the daily snapshot instead of the pinned tag (results get stamped `snapshot-YYYY-MM-DD` and excluded from long-term history by default); `FORGE_SNAPSHOT_BUILD=2.0.16-SNAPSHOT-11.08` pins one snapshot build, verified against `forge/SHA256SUMS` when listed there.

**Scryfall side:** nothing scheduled. The resolver runs on demand for any card name not already in `cards/scryfall-cache.json`, so new cards get resolved the first time they appear in a deck or result. Once a quarter, re-resolve the whole cache to catch image upgrades (`lowres` → `highres_scan`).

**Benchmark pod:** frozen. New precons do not join it. If you ever must change it, that's a new benchmark with a new name, and history restarts.

**Playbooks:** unaffected by set releases. They only change when the deck changes or the post-mortem loop revises them.

## 12. References

**Forge**
- Repo: https://github.com/Card-Forge/forge
- Releases (tags + daily snapshot): https://github.com/Card-Forge/forge/releases
- Older release archive: https://releases.cardforge.org/forge/forge-gui-desktop/
- AI / sim mode flags: https://github.com/Card-Forge/forge/wiki/AI
- Sim mode source (all flags, tournament mode): https://github.com/Card-Forge/forge/blob/master/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java
- Game event bus and event records: https://github.com/Card-Forge/forge/tree/master/forge-game/src/main/java/forge/game/event
- AI profile properties: https://github.com/Card-Forge/forge/blob/master/forge-ai/src/main/java/forge/ai/AiProps.java
- Snapshots and release process: https://github.com/Card-Forge/forge/wiki/Snapshots-and-Releases
- Card scripting API (AILogic, RemAIDeck live here): https://github.com/Card-Forge/forge/wiki/Card-scripting-API
- User guide: https://github.com/Card-Forge/forge/wiki/User-Guide
- Simulation-based AI discussion (lookahead design + limits): https://www.slightlymagic.net/forum/viewtopic.php?p=190653
- AI personalities/profiles thread: https://www.slightlymagic.net/forum/viewtopic.php?p=112508
- AILogic / RemAIDeck explanation thread: https://www.slightlymagic.net/forum/viewtopic.php?p=215181
- Headless sim Q&A: https://slightlymagic.net/forum/viewtopic.php?p=210601

**Scryfall**
- API docs (rate limits, User-Agent, image rules): https://scryfall.com/docs/api
- Image hosting changes / hotlinking policy: https://scryfall.com/blog/category/api

**Wizards of the Coast**
- Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

**Infra**
- GitHub Actions usage limits: https://docs.github.com/en/actions/administering-github-actions/usage-limits-billing-and-administration
- GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

## 13. Open questions

- ~~Does Forge's tournament mode seat 4 players in one game, or pair them 1v1?~~ **Answered (Phase 0):** it pairs 1v1 at 20 life even with `-p 4`. Plain mode with four `-d` decks seats all four.
- ~~Can the Forge AI be given a per-player profile in sim mode, or is it global?~~ **Answered:** yes, `-a` takes one profile per seat in deck order (2.0.15).
- ~~How much of game state does Forge expose cleanly for the post-mortem serializer?~~ **Answered (Phase 1):** the event bus plus direct reads of `Game`/`Player` in the harness; hands are logged at every turn start (it is our own sim, nothing is hidden).
- ~~Playbook expression language: hand-roll, embed a tiny evaluator, or reuse Forge's `Valid`/`Count$` card-script syntax.~~ **Answered (2026-11-10, §21):** hand-rolled and deliberately tiny: a comparison of one named metric with a number, or `controls <card>`; a list of them is a conjunction, a second rule is the disjunction. Forge's `Valid` syntax stays the option if a deck needs to say more.
- ~~Squirreled Away: play it as shipped (Hazel of the Rootbloom) or swap the commander to Chatterfang?~~ **Answered:** as shipped, Hazel in the command zone. Chatterfang is the product's alternate commander and stays in the 99.

## 14. Phase 0 results (2026-11-08)

Forge 2.0.15 (release of 28 Sep 2026), Java 21, 4-core / 15 GB container. Scripts: `forge/fetch-forge.sh`, `runner/pod-smoke.sh`.

| Check | Result |
|---|---|
| 2-player constructed sim (two quest precons) | 2 games, 5 s and 11 s |
| 4-deck Commander sim, plain mode | 15 games (12 local, 3 in Actions), all completed; 40 life, commander-damage kills, winner by last standing, no exceptions |
| Tournament mode `-t RoundRobin -p 4 -f Commander` | pairs 1v1 at 20 life; not usable for Commander |
| Seeded determinism | same seed → same 55-turn game and winner; 14 of 3,782 log lines differ, all attacker/blocker listing order |
| Time per 4-player game | avg 98 s over 10, median 66 s, min 44 s, max 247 s; plus ~11 s startup per process. Actions runner: 41 s, 85 s, 375 s |
| Games over Forge's 120 s default clock | 4 of 15 (would have been draws) |
| Download / extract | 283 MB tarball, 13 s download, 30 s extract; trimmed runtime ~190 MB |
| GitHub Actions run | green on first run: `ubuntu-latest` (4 vCPU, 15 GB, Temurin 21); fetch + verify + extract 26 s; 3 pod games in 509 s wall; runtime cached at 66 MB compressed |

Log shape (stock text log, one game ≈ 3,800 lines): `Phase` (~37%), `Mana`, `Add To Stack` / `Resolve Stack`, `Zone Change` (graveyard/exile moves only), `Turn`, `Damage`, `Combat`, `Life`, `Land`, `Mulligan`, `Game Outcome`. Missing: draws, hand contents, the zone a spell was cast from. This is why Phase 1 logs from the event bus instead of parsing text.

Changes from v0.1: dropped the Forge fork/patch (§3.1, §8, §11); four-precon pod (§4.1); measured costs (§4.2); profiles-first pilot and upstream-lookahead evaluation (§3.1, §7); new risks and resolved questions (§9, §13); results schema gains `forge_version`, `seed`, `loss_reason` (§6).

## 15. Phase 1 results (2026-11-08)

Built and verified end to end on the same container as Phase 0, then in Actions.

| Piece | Verified |
|---|---|
| Harness `play` | 4-player games through the event bus: ~700 events / 130 KB per game, 30–140 s per game, boot ~6 s; turn cap, clock exit (code 3) and `--start` resume all exercised |
| Harness `check` | the four pod precons: 100 cards each, no unknown or unsupported cards, Commander-conformant; AI-flagged cards 5/4/1/4 |
| `run-pod.sh` | 2 shards × 2 games locally, resume path, `-k` single-shard mode |
| `rollup.py` | per-deck stats over shards; `index.json` upsert |
| `scryfall.py` | 300 names in 5 requests, split cards via front-face retry, rerun resolves nothing |
| Dashboard | light, dark and 390 px phone renders with no console errors or broken images; palette validated for four seats (light-mode contrast relief via direct labels and table views) |
| Workflows | `pod-run.yml` (4 shards + rollup + optional publish). Pages serves the `testing` branch directly: root `index.html` redirects to `dashboard/`, which reads `../demo-data/` |

Demo data: the first published run is `demo-data/runs/2026-11-08-pod-v1-forge-2.0.15-s20261108`: 20 games in 2 shards (seed 20261108), all 20 decided, no draws or exceptions, 47 turns and 114 s per game on average (16–595 s, two shards sharing 4 cores). Wins: Veloci-Ramp-Tor 8, Mutant Menace 6, Blight Curse 4, Squirreled Away 2; every loss was life reaching zero; commanders first cast on own turn 6–7 on average. The published run is 744 KB including gzipped event logs. `demo-data/index.json` lists later runs.

Branches: `testing` is the change-control branch and what GitHub Pages serves (branch deploy, root); `main` is promoted from it; feature branches (`claude/*`) merge into `testing`.

## 16. Prior art (surveyed 2026-11-08)

What already exists, and what Vibefish takes from it. Links are in §12 and inline.

**Pod simulation on Forge exists: Magic Bracket Simulator** ([repo](https://github.com/TytaniumDev/MagicBracketSimulator), [app](https://magic-bracket-simulator.web.app)). Four-deck Commander pods through stock sim mode (`sim -d d1 d2 d3 d4 -f Commander -n 4 -c 600`), a Firestore job queue with Flutter desktop workers, text-log parsing for winner and winning turn, per-seat win rates, per-card "impact" counters, Moxfield and Archidekt deck import. No licence file, so nothing is reusable as code. Lesson: the "simulate pods, show a leaderboard" part is not novel; Vibefish's value is the structured event log, consistency stats, calibration against human data, and the pilot work. We do not build a worker fleet.

**Forge's AI already has the hooks Phase 2–4 planned to build.** kevlahnota's Flat Monte Carlo series on master ([#12308](https://github.com/Card-Forge/forge/pull/12308) 23 Oct 2026, [#12467](https://github.com/Card-Forge/forge/pull/12467) DeckPlan + Sideboard Advisor, [#12490](https://github.com/Card-Forge/forge/pull/12490) CommanderPlan, then dredge and lands) adds: rollouts over the heuristic AI's top candidates with a time budget; archetype detection; `CommanderPlan` (commander strategies such as Voltron, tokens, aristocrats, spellslinger, counters, landfall, graveyard, artifacts, tribal, stax; known combos; commander damage as a clock); plan-aware mulligans (`OpeningHand`). All of it is data-driven: `res/lists/ai-card-roles.txt` (`role | Card | Card …`), `ai-combos.txt` (`win|lock | Name | slot | slot …`, 59 lines), `ai-commander-combos.txt` plus `commander-bracket-combos.txt` (two-card Commander combos, ~2,200 pairs), `.ai` profile knobs, and deck metadata `KeyCards=` (protected from discard). None of it is in 2.0.15. It also ships test tooling worth copying: `FlatMonteCarloBenchmark` (opt-in A/B between AI "arms", blocks of four games alternating deck and seat, fixed time budget, seeds; "64 games have a 95% interval of about ±12 points"), `StormGoldfishTest` (a deck against a do-nothing Plains deck, reporting the win turn, built on the same event-bus subscriptions as our logger), `SimAudit` (rollout fidelity) and scenario tests ("with three open Islands and nothing else to do the AI should cast Opt").

**Human reference data exists: Playgroup.gg.** From 770,000+ recorded Commander games: stock-precon win rates normalised to a 25% baseline ([precons](https://playgroup.gg/commander/precons); as of 8 Nov 2026 Mutant Menace 15.5%, Blight Curse 16.2%, Veloci-Ramp-Tor 24.6%, Squirreled Away 21.2%; top of the table Planeswalker Party 33.5%, Legends' Legacy 31.9%), the seat effect in 257,261 four-player games (seat 1 29.2%, seat 2 25.7%, seat 3 23.6%, seat 4 21.5%; [experiment](https://playgroup.gg/commander/turn-order/experiment)), opening-hand land distribution, mulligan rates (64% none, 24% one, 9% two, 3% more) and game length (8.75 rounds on average; [lands](https://playgroup.gg/commander/how-many-lands)). No public API; use as a manual reference.

**LLM-as-pilot has been tried and is weak.** [mage-bench](https://github.com/GregorStocks/mage-bench) (XMage fork, LLMs through MCP tools, 1v1 Elo plus four-pilot Commander round robins, blunder analysis "best-effort and currently pretty unreliable"; the author says frontier models "play pretty bad Magic"), Commander Bench (XMage fork, same idea), MTG Bench (no rules engine). Academic: Cowling, Ward and Powley 2012 (MCTS with ensemble determinization for Magic), MageZero (AlphaZero-style, deck-local, on XMage; ~18 s per full-depth game, ~20k self-play games per deck), MTG-Causal-RL 2026 (custom 56-card engine, 1v1 Standard). Magarena's Project Firemind (2014–2016) was a cloud AI deck-testing service; its users' complaints (mass removal misplayed, control decks) match Forge's known weaknesses. Confirms §1: the LLM writes the pilot, it does not fly the plane.

**Combo knowledge: Commander Spellbook.** REST API (`/find-my-combos`, `/variants/`, `/estimate-bracket`), bulk file `https://json.commanderspellbook.com/variants.json.gz` for anything large, ~80 requests/min, name the client in the User-Agent, credit and link back. Forge's own lists are small by comparison, and they are plain text files.

**Deck-building math references.** ScrollVault's 3.75-million-game goldfish Monte Carlo (cast-on-curve rate per mana value; midrange 36–37 lands, battlecruiser 38–40), Karsten's hypergeometric models (~38 lands for midrange by regression), Playgroup's 38–42 from real games. Our consistency stats should speak the same language: cast-on-curve rate, land drops by turn, opening-hand lands.

**Forge AI weaknesses on record.** A 2018 AI-vs-AI tournament study found the AI best with proactive creature decks (Merfolk, Affinity, Elves, Burn) and worst with control and graveyard-value decks; the wiki calls it "pretty bad for most combo decks". In multiplayer it attacks a random player among the highest threat scores (`AiAttackController.choosePreferredDefenderPlayer`), with no memory or politics.

**What this changes (proposed, not yet applied):**
1. Add a goldfish mode (deck versus three do-nothing decks) for cheap consistency stats, after Forge's storm goldfish test. *Done: `runner/goldfish.sh`.*
2. Adopt Forge's A/B discipline for every pilot claim: arms as AI profiles, blocks alternating seats, hundreds of games, confidence intervals.
3. A calibration scorecard against Playgroup: precon win-rate rank correlation over a large precon round robin, mulligan rate, opening-hand lands, rounds per game, seat advantage. This is the measurable form of "plays precons at a human level". *Done: `runner/scorecard.py`, shown on the dashboard; the large precon round robin is the league in §18.*
4. Phase 3 becomes data generation rather than a line executor: deck → Spellbook → Forge `ai-commander-combos` / `ai-combos` / `ai-card-roles` lines and `KeyCards`, fed to the Flat MC AI.
5. Benchmark the Flat MC AI on the pod now via `FORGE_CHANNEL=snapshot`, heuristic versus Monte Carlo, since nobody has published Commander numbers for it. *First run done, see §17.*

## 17. First A/B: Flat Monte Carlo vs heuristic AI on the pod (2026-11-08)

Run `ab1-pod-v1-snapshot-2026-11-08-mc-vs-heuristic` in `demo-data/`: Forge daily snapshot 2026-11-08 (2.0.16-SNAPSHOT), 40 games in 2 shards, two seats per arm per game with the arm assignment shifted one seat every game, so each deck played 20 games per arm.

| Arm | Game wins | Game win share (95%) | Per seat |
|---|---|---|---|
| Vibefish-MC (Flat Monte Carlo, Default budgets) | 22 of 40 | 55% (40–69%) | 27.5% |
| Vibefish-Heuristic (`FLAT_MC_ENABLED=false`) | 18 of 40 | 45% (31–60%) | 22.5% |

Even would be 50% each. A lean towards Monte Carlo, well inside the interval: by Forge's own benchmark rule of thumb (64 games ≈ ±12 points) this needs a few hundred games before it says anything. Per deck, Monte Carlo won more with Mutant Menace (10 vs 7) and Veloci-Ramp-Tor (9 vs 7), and nothing changed for Blight Curse (1 vs 1) or Squirreled Away (2 vs 3). Games averaged 46 turns and 57 s, no draws; the snapshot's rollouts failed and fell back to the heuristic choice 10 times in 40 games (a `RuntimeException` in the game copy, logged by Forge), recorded with seeds in `docs/upstream.md`. The harness now records Forge's own Monte Carlo statistics per game (`mc_stats` in `run.json`, summed into `mc_summary` in the rollup). A first look at one 30-turn game explains the small effect: 23 main-phase decisions, 16 settled by rollouts, 64 rollouts at about 650 ms each, 7 decisions abandoned as too slow, and only 1 override of the heuristic choice. With the Default budgets (450 ms per decision, 2 s per turn) a four-player board affords one or two rollouts per decision, so Monte Carlo mostly confirms the heuristic. At `--mc max` (desktop strength, no time budget) the same seat set-up changes the picture: one 36-turn game took 170 s instead of ~57, 26 decisions, 22 by rollouts, 110 rollouts at ~1.4 s each, and 9 overrides of the heuristic choice (35% of decisions, against 4% at Default budgets), with 16 rollout failures and 11 cards the copier could not simulate. So the Default-budget A/B above mostly measured the heuristic AI against itself; the arm that can differ is `--mc max`. Second run, `ab2` (`--mc max`, 120 games, seeds from 20261111, clock 1800 s, two shards, profiles rotating across seats): Monte Carlo 68 wins of 120 (56.7%, 95% 48–65%) against 52 for the heuristic (43.3%, 35–52%). Even would be 50%, which the interval still contains, so after 160 games the max-strength layer is a lean, not a result; confirming a 7-point edge would take about 400 games, and the question is Forge's rather than ours. Per deck (Monte Carlo vs heuristic wins of 60 seat-games each): Veloci-Ramp-Tor 31 vs 24, Blight Curse 14 vs 8, Squirreled Away 9 vs 5, Mutant Menace 14 vs 15. Games averaged 43 turns and 97 s (1.7× the heuristic-only pace), no draws. Forge's own statistics over the run: 6,855 main-phase decisions, 4,946 settled by rollouts, 2,042 overrides of the heuristic choice (30%), 33,582 rollouts at 977 ms average, 6,230 rollout failures (19% of rollouts) and 2,226 unsimulatable-card reports, so on this pod about one rollout in five falls back to the heuristic. Calibration for the run: any mulligan 25% (human 36%), 10.8 rounds per game (human 8.75), first seat 21.7% (human 29.2%), opening-hand lands mean 3.08 (human 2.91); Veloci-Ramp-Tor 45.8% against 24.6% with humans, Squirreled Away 11.7% against 21.1%. Recorded with seeds in `docs/upstream.md`: the rollout failures ("Couldn't map The Monarch", "Couldn't map Auntie Ool, Cursewretch", `origCard` null in `hasRemembered`).

**How they play (154 games read from the event logs: the baseline, `ab1` and the first 94 of `ab2`).** Casting is not the gap: from round 5 a seat spends 75–87% of its available mana on its own turn (mana value of spells cast over lands; abilities and X not counted) and is idle with 3+ lands and 3+ cards in hand on 6–13% of turns. Combat is. The heuristic arm attacks on 37% of its turns in rounds 5–8 with 0.6 attackers and 2.9 combat damage to players per turn, and 43% / 1.4 / 5.7 in rounds 9–12; the first elimination comes at player-turn 35 (round 9), which is about when human tables are finished (8.75 rounds). Once low, a player dies within one turn cycle and 74% of kills are the eventual winner's, so closing is not the problem; starting is. Two causes, both in Forge's `AiAttackController`: `notNeededAsBlockers` treats every opponent creature as a potential attacker next turn and keeps enough blockers to survive the sum of all three boards (relaxed only by the `PLAY_AGGRO` profile property, set only in Reckless); and `choosePreferredDefenderPlayer` sends every attacker at one opponent scored by board evaluation plus a bonus below 20 life. In the logs 100% of attack declarations are single-target; when the weakest player and the biggest board differ, 52% of attackers go at the biggest board, 41% at the weakest, 8% at the third; attackers received per 100 opponent-turns run from 19 for Veloci-Ramp-Tor (the deck that wins most) to 24 for Blight Curse (the deck that wins least), so the table never gangs up on the leader. Monte Carlo max shares the targeting and differs only in aggression (42% of turns, 1.0 attackers, 3.8 damage in rounds 5–8). Levers, cheapest first: the aggression profile knobs (a four-arm Default / Reckless / Cautious / Experimental run with Monte Carlo off), then an attack policy in a Vibefish controller through the public `declareAttackers` hook (blockers against the single most dangerous board, split attacks, defender weighted by who is winning); Phase 3 data does not touch combat. Logger note: Forge's blockers event lists an unblocked attacker as blocked by itself, and the `block` events of runs up to `ab2` copy that, so they overstate blocking; fixed in harness 0.1.1 (an empty `blockers` list now means unblocked).

**Four-profile run** (`prof1`, snapshot 2026-11-08, Monte Carlo off, 60 games, seeds from 20561111, one seat per profile, rotating): Default 15 wins (25.0%, 95% 16–37%), Reckless 13 (21.7%, 13–34%), Cautious 18 (30.0%, 20–43%), Experimental 14 (23.3%, 14–35%); even is 25% and nothing separates from it. Games averaged 45 turns and 79 s, no draws; first elimination at player-turn 36.5 and game end at 45.5, the same shape as every run before it. Reckless is measurably the most aggressive seat (attacks on 49% of its turns in rounds 5–8 with 0.9 attackers against Default's 42% and 0.7; 9.3 combat damage per turn in rounds 9–12 against 5.9) and sends 61% of its attackers at the biggest board when that differs from the weakest player (Default 48%), yet it does not win more. Experimental attacks least and spreads its attacks (46% at the lowest-life player, 46% at the highest). Casting is unchanged across profiles (85–86% of mana used in rounds 5–8). Conclusion: the profile knobs move aggression by a fraction of a creature per turn and leave the game's shape untouched. With one seat per profile this run cannot say what a whole table of one profile does to game length; that is the next cheap check (homogeneous tables, Default against Reckless, same seeds).

**Feasibility of the attack policy (read from Forge master, 2026-11-08).** `PlayerControllerAi.declareAttackers`, `declareBlockers` and `mulliganKeepHand` are public overridable methods, its constructor `PlayerControllerAi(Game, Player, LobbyPlayer)` is public, and `LobbyPlayerAi.createIngamePlayer` is public, so a Vibefish subclass of each replaces only the attack decision and keeps everything else Forge's, with no patch (§3.1). The harness would construct its own lobby player instead of `GamePlayerUtil.createAiPlayer`, a few lines.

**Mulligans are already moving upstream.** The snapshot carries a plan-aware opening-hand evaluator (`forge.ai.simulation.OpeningHand`), switched by the profile property `FLAT_MC_MULLIGAN` whose default is on and which does not depend on the Monte Carlo game flag, so every arm in the snapshot runs used it. That is why the mulligan rate rose from 17–20% on 2.0.15 to 24–25% in `ab2` and `prof1` (human 36%). Nothing to build there for now.

**Decision (2026-11-08): no global scripting; custom bots are per deck.** No attack-policy override, and nothing like it, as a global behaviour: Commander play is far more than one step, and a sweeping policy applied to every deck regardless of context misses the point. Custom behaviour, when it comes, is one deck's playbook and data attached to the seat playing that deck (§8), which is what Phases 3 and 4 already describe; the general bots stay Forge's. The combat and targeting numbers above are measurements, kept reproducible in `runner/playstyle.py`, not a work item. The next step is chosen with the whole game in view; the candidate is to widen the yardstick from four decks to many (the precon league against Playgroup's precon table, §16 item 3), so the sim is judged on outcomes across archetypes rather than on one behaviour. The two homogeneous-table runs started before this decision (`tbl-default`, `tbl-reckless`, 30 games each, same seeds) are recorded here as measurements. **Homogeneous tables** (`tbl-default`, `tbl-reckless`: 30 games each, identical seeds from 20861111, Monte Carlo off, every seat on one profile): the same length. The Default table averaged 47.2 turns (median 48), the Reckless table 46.8 (median 48); first elimination at player-turn 39 against 37, then 8 and 10 player-turns to the end. The Reckless table attacks on 47% of turns in rounds 9–12 against 40% and deals 5.2 combat damage per own turn against 4.3, and wall-clock drops from 71 s to 49 s a game, but the shape of the game is unchanged at 11–12 rounds against the human 8.75. Deck wins (Default table / Reckless table): Veloci-Ramp-Tor 13 / 12, Mutant Menace 8 / 7, Squirreled Away 7 / 5, Blight Curse 2 / 6. Taken with `prof1`: Forge's profile knobs do not change how long a table of stock bots takes to finish a game.

## 18. Precon league (2026-11-09)

**Why.** Phase 2's exit criterion (§7) is a calibration scorecard over at least 24 precons; the pod compares four, where a rank correlation is noise (0.2 to 0.8 across runs of the same bots). Playgroup.gg ranks 92 precons by stock win rate from 28,726 tracked games (page of 2026-11-09, CC BY 4.0), the largest human reference there is, so the league plays every Forge-bundled precon that Playgroup ranks and scores the sim's ordering against theirs. The 92 figures, with games, tier, set and face commander, are in `runner/reference/playgroup-commander.json`, transcribed by `runner/reference/transcribe-playgroup.py` from a saved copy of the page (the script never fetches; it is the provenance record and the tool for the next refresh).

**Decks.** `runner/precon-league.json`, `league-v1`, frozen: 91 of the 92 ranked precons are bundled with Forge (snapshot 2026-11-08 ships 184 Commander precons; 2.0.15 shipped 179). Matched by name, with three Forge spellings mapped by commander (Riveteers Rampage → `Riveteer Rampage`, Mind Flayarrgh → `Mind Flayarrrs`, The Hosts of Mordor → `The Host of Mordor`); Everyone's Invited (a Secret Lair deck) has no Forge file. Two decks ship with the other legend in the command zone (Sultai Arisen: Kotis rather than Teval; Temur Roar: Eshki rather than Ureni) and are played as shipped, like Squirreled Away. All 91 pass `vibefish-sim check`: no unknown or unsupported cards, Commander-conformant; cards Forge marks `AI:RemoveDeck:All` run from 0 to 8 per deck (median 2; Tricky Terrain has 8).

**Schedule** (`runner/league.py`, a pure function of the league file, the seed and the number of cycles). A cycle is four rounds: the 91 decks minus three byes (rotating through the list) are shuffled into four groups of 22; each round seats one deck from every group at each of 22 tables, and a group's seat shifts by one per round, so every deck sits in every seat exactly once per cycle and meets different opponents every round. 25 cycles = 100 rounds = 2,200 games, 96 to 100 per deck, 3,933 of the 4,095 possible pairings met. Game *i* has seed S+*i*+1 (the harness's own convention); shard *k* of *K* plays the games with (*i*−1) mod *K* = *k*−1, so a partial run still covers the league evenly, and a finished game is never replayed. Each game is one harness process (`play --games 1`), so the JVM and card-database boot (~11 s) is paid per game of 40 to 70 s. Sample size: at 100 games a precon's win rate carries a ±8-point interval, and the human table's own noise is comparable (48 to 868 stock games per matched precon), so the scorecard also reports the correlation over the precons with 100 or more human games.

**Scorecard and dashboard.** `runner/scorecard.py` reports Spearman and Pearson correlation over the matched precons, the mean absolute gap, the spread of win rates (sim SD against human SD), and the pod metrics (first-seat and per-seat win rates, mulligans, kept-hand lands, rounds per game). A league rollup (`kind: league`) gets its own dashboard view: headline tiles, a dot plot of sim against human win rate with the sim's 95% interval per precon, the calibration card, a sortable precon table with commander images, and the games table on demand.

**Build and compute.** First run on the 2026-11-08 snapshot, the build of every published A/B so far (`FORGE_SNAPSHOT_BUILD=2.0.16-SNAPSHOT-11.08`, checksum in `forge/SHA256SUMS`), Monte Carlo off, Default profile: the stock AI a per-deck bot will be measured against. Smoke on the 4-core container: games of 40 and 62 s plus boot, two at a time. `league-run.yml` plays up to 20 shards of 110 games, two games at a time per 4-core runner, about 1.5 h of wall clock, then rolls up, scores and optionally publishes. A league publishes `rollup.json`, `scorecard.json` and `league.json` only: 2,200 per-game `run.json` files and gzipped event streams would add about 80 MB per run to the repo for data the dashboard never reads; they stay in the workflow's artifacts for 90 days and in `results/` locally, and any game is reproducible from its seed and seats on the same build. `runner/status.py` does not read league runs yet. First-run lesson: two harness processes booting at the same moment in a runtime Forge has never started before race on creating Forge's profile directories (`cannot create profile directory`), so every CI shard of the first run lost its first game; the player now boots the first game alone and retries a game that dies within a minute of launch.

**Results (first full run, 2026-11-09).** `2026-11-09-league-v1-snapshot-2026-11-08-s20261109` in `demo-data/`: 2,200 games, 96 to 100 per deck, snapshot 2026-11-08, Default profile, Monte Carlo off. 2,175 decided (18 by a spell effect), 25 draws (17 on the 1800 s clock, 6 declared by Forge, 2 engine errors, see `docs/upstream.md`); 48 turns and 119 s per game on average (median 60 s, 90th percentile 224 s). Twenty Actions shards of 110 games took 2 h 59 min of wall clock; twelve shards lost their first game to the boot race above and those twelve games were replayed here before publishing, so the rollup is complete.

- **Ordering.** Spearman 0.266 (Pearson 0.246) between the sim's and Playgroup's win rates over 91 precons; 0.281 over the 74 precons with 100 or more human games. Mean absolute gap 8.1 points. Spread: sim SD 10.7 points against human 4.3, so Forge's AI exaggerates deck differences about 2.5 times. Coarse agreement is better than the fine ranking: 17 of the 25 human A- and B-tier precons sit in the sim's top half and 16 of the 20 D-tier precons in its bottom half.
- **Where it is wrong, by archetype.** Over-rated: Calling All Angels (sim 62.1% against 21.9% human), Scions & Spellcraft (56.8 / 21.4), Endless Punishment (55.8 / 23.8), Veloci-Ramp-Tor (53.0 / 24.6), Silverquill Influence (41.7 / 19.2), Blood Rites (39.4 / 19.0), Doom Prevails (34.4 / 16.3), Reign of Dragons (33.3 / 15.5): creature decks that win by attacking, lifegain and ramp. Under-rated: Planeswalker Party (human #1 at 33.5%, sim #36 at 26.0%), Legends' Legacy (#2, sim #34), Tricky Terrain (#5, sim #69 at 17.2%; it has 8 AI-never cards), Token Triumph (#8, sim #82 at 14.0%), Maestros Massacre (#10, sim #85 at 9.4%), Tinker Time (24.3 / 7.1), Goblin Storm (20.9 / 5.3): planeswalkers, lands, tokens and sacrifice, artifacts, storm, the archetypes Forge's AI is known to misplay (§16). The pod decks: Veloci-Ramp-Tor 53.0% against 24.6%, Mutant Menace 22.9% against 15.4%, Blight Curse 17.7% against 16.2%, Squirreled Away 18.0% against 21.1%.
- **Calibration.** First seat 26.7% (human 29.2%); by seat 27.0% / 24.4% / 25.0% / 23.6% against 29.2% / 25.7% / 23.6% / 21.5%; any mulligan 23.3% (36%); kept-hand lands 3.03 (2.91); 12.0 rounds per game (8.75). The same picture as the pod, now over 91 decks.
- **Reproducibility across machines.** Shard 1 was also played in this container on the same seeds and build: 95 of 110 games came out identical (winner, turns, final life totals) and 15 differed, all among the slower games (median 200 s against 62 s for the identical ones), where Forge's per-decision timeouts fire (140 timeout traces in that shard's log). The seed fixes the shuffles; the AI's wall-clock budgets do not, so a seed replays a game exactly only when the machine keeps the same pace. §9's "same seed replays the same game" holds for about 86% of games across machines.

**What it says.** The yardstick exists, and the stock AI orders precons with weak but real agreement with people, better at the tier level than deck by deck. Its misses cluster by archetype rather than scattering, which is the case for per-deck data and playbooks (Phases 3 and 4): the first per-deck bot should take one of the under-rated archetypes with a large human sample, Token Triumph (197 games) or Planeswalker Party (199), and be judged by the same league against the same reference. The league is re-run per Forge build; the next is the 2.0.16 release.

## 19. Phase 3: per-deck data for Forge's AI (2026-11-09)

**What Forge can be told, per deck, in this build (2.0.16 snapshot).** Read from the jar and the master source before building anything:

| Channel | Where it lives | Who reads it | Per seat? |
|---|---|---|---|
| `KeyCards` | deck metadata (`.dck` header, or `Deck.addKeyCard`) | tutors (`ChangeZoneAi.chooseCardToHiddenOriginChangeZone`: the first key card the search can find wins), discard and exile costs, Pithing Needle choices, the sideboard advisor; heuristic AI, no Monte Carlo needed | yes |
| card roles | `res/lists/ai-card-roles.txt`, given to `AiCardLists.configure(...)` by the front end | `ComboPlan.scan` detects combo kinds from them (GO_WIDE: two `overrun` finishers and 16 cheap bodies; STORM: two payoffs and eight rituals or cantrips; REANIMATOR, CHEAT_FATTY, PAIR, ...); a detected kind protects its pieces from discard costs, steers tutors to the missing piece, and tilts Monte Carlo playouts | global list, effective only for decks holding the cards |
| combos | `ai-combos.txt` (`ComboCatalog.configure`) and two-card pairs (`ai-commander-combos.txt`, `commander-bracket-combos.txt`) | `CommanderPlan` (combo terms, protected pieces, key cards for tutors), `AntiCombo` (opponents' removal targets) | global list, same caveat |
| deck plan | `FLAT_MC_DECK_PLAN` in the seat's `.ai` profile: `auto` or an archetype | `DeckPlan` tilts (life, risk, mana development, long playouts) in Monte Carlo rollouts; `tutorPicks` for RAMP and COMBO in the heuristic AI | yes |
| profile knobs | the seat's `.ai` profile (about 150 properties) | the heuristic AI throughout: `PLAY_AGGRO` (attack and blocker policy), `TOKEN_GENERATION_*`, `MIN_COUNT_FOR_STORM_SPELLS`, `HOLD_LAND_DROP_*`, counterspell and combat-trick chances, ... | yes |

`DeckPlan`, `ComboPlan` and `CommanderPlan` are consulted by the heuristic AI too (`AiController.deckPlan`, `ChangeZoneAi`, `ComputerUtil`, `DigAi`, `DiscardAi`, `PlayAi`, ...), not only by the Monte Carlo layer, so the data has an effect with Monte Carlo off; the deeper effects (planning the line, storm sequencing with `StormSolver`, combo assembly) need the seat on Monte Carlo. The list files are global state inside Forge for the length of a game; the harness gives Forge its shipped lines plus the data of the seats that have any, so the stock seats run the stock lists plus lines that only matter for cards they do not hold, and an opponent that recognises a visible combo piece aims removal at it, a bias against the data-fed seat. `AI:RemoveDeck:All` cards are unaffected by any of this.

**Design.** `runner/deckdata.py generate` drafts `playbook/precons/<id>.json` for every league deck from three sources: the decklist, Commander Spellbook's `find-my-combos` (one request per deck, trimmed answer kept as provenance under `playbook/precons/spellbook/`), and Forge's own card scripts (`res/cardsfolder/cardsfolder.zip`: oracle text, types, keywords). Rules turn those into Forge's vocabulary: storm payoffs, overrun finishers, reanimation spells and their targets, cheat spells and fatties, mass payoffs; combos entirely inside the deck become `ai-combos` lines (win or lock by what they produce) and two-card pairs; key cards are the combo pieces and finishers. A `curated` block written by hand overrides the generated one key by key and survives regeneration; the "LLM read" of §7 is that curation, done here for the four first bots with the deck in front of me. The harness (`--data id=file`) applies the effective data to its seat: `Deck.addKeyCard` for the key cards, `AiCardLists.configure` and `ComboCatalog.configure` for roles, pairs and combos (by reflection, so the harness still compiles against 2.0.15), and `DeckPlan`'s cache is cleared so the lines count for the game; `runner/ab.py` writes the seat's profile (`Default.ai` plus `deck_plan` and `profile` overrides) and passes it with `--profile`. Everything is recorded in `run.json` (`decks[].data`, `ai_lists`; harness 0.2.0). Precons rarely contain infinite combos: of the four first bots only Goblin Storm has one (Storm-Kiln Artist + Haze of Rage), so for precons the data is mostly key cards, roles, the archetype and the knobs; across the league the generator finds complete combos in a minority of decks.

**Measurement.** `runner/ab.py` plays the same tables and seeds once per arm: `stock` (the deck as shipped), `data` (the data file and the per-deck profile), `mc` (the seat on Flat Monte Carlo, opponents heuristic), `mcdata` (both). Each table seats the deck in rotation with three opponents drawn from the league; the rollup gives wins per arm with Wilson intervals and the paired difference with its interval. `ab-run.yml` shards it in Actions: four decks, 100 tables, four arms is 1,600 games. The exit criterion of §7 is a data arm that beats the stock arm; the yardstick of §18 says where the deck should end up (Token Triumph: 14% stock in the league, 26.5% with people).

**The four first bots** (chosen 2026-11-09 for the strength of the human reference and the size of the sim's shortfall, §18): Token Triumph (overrun finishers for the GO_WIDE plan, `PLAY_AGGRO`, token abilities always on, AGGRO plan), Goblin Storm (storm payoffs, Krenko and the engine Goblins first for the Goblin tutors, `MIN_COUNT_FOR_STORM_SPELLS=2`, COMBO plan; Forge's STORM detector wants eight rituals and the precon has six, so the plan itself does not fire without Monte Carlo), Tricky Terrain (LANDS plan forced, the Locus lands and landfall payoffs first for the land tutors, land drops in main 1), Hail, Caesar (`PLAY_AGGRO`, token abilities always on, AGGRO plan, the token engines as key cards). Each file's `curated.notes` says why.

**Pipeline checks (2026-11-09, this container).** Token Triumph, 12 paired tables (seed 20261110, arms stock and data): stock won 2 of 12, data 3 of 12, a difference of +8 points with an interval of about ±28, so no result yet; in the games it lost, the data seat died earlier (own turn 38 against 44), which is what an aggressive profile should do, and 10 of the 12 pairs diverged from their stock twin early in the game. Goblin Storm, 3 tables by four arms: every arm ran as intended, the per-deck profile and the data on the data seats, Forge's Monte Carlo statistics only on the mc seats, the opponents heuristic; at 3 tables the win counts mean nothing. The measurement is `ab-run.yml` with its defaults: the four decks, 100 tables, four arms, 1,600 games in 20 Actions jobs of 80.

**Results (first full A/B, 2026-11-09, `ab-run` in Actions: four decks, 100 tables each, four arms, 1,600 games, 20 jobs in 2 h 33 min, no failed game; rollups in `demo-data/ab/2026-11-09-ab-v1/`).** Win rate of the deck over the same 100 tables, by arm:

| Deck (human) | stock | data | mc | mcdata | data − stock (95%) | mc − stock | mcdata − stock |
|---|---|---|---|---|---|---|---|
| Token Triumph (26.5%) | 22% | 15% | 18% | 23% | −7 (−17 to +3) | −4 (−14 to +6) | +1 (−9 to +11) |
| Goblin Storm (20.9%) | 5% | 8% | 9% | 5% | +3 (−3 to +9) | +4 (−3 to +11) | 0 (−6 to +6) |
| Tricky Terrain (28.6%) | 11% | 18% | 19% | 21% | +7 (−3 to +17) | +8 (−1 to +17) | +10 (0 to +20) |
| Hail, Caesar (21.5%) | 21% | 17% | 19% | 13% | −4 (−14 to +6) | −2 (−13 to +9) | −8 (−18 to +2) |

No arm beats stock clearly. Tricky Terrain is the one deck where every arm points the same way (18 discordant pairs for mcdata against 8, an exact two-sided test at 0.08), which fits what its data does: a forced LANDS plan and the land tutors steered to the Locus lands; Token Triumph leans the other way with its data (10 against 17), and Goblin Storm stays at 5 to 9% whatever it is given. The event logs say why the knobs do so little: with `PLAY_AGGRO` on, Token Triumph attacked on 29% of its turns against 31% stock, with the same number of attackers, the same tokens per game and the same commander timing; Hail, Caesar 31% against 30%; Monte Carlo at Default budgets played the same game (`mc` within two points of stock on every measure). Goblin Storm's data doubled its damage per turn (4.9 against 2.4) and did not win more. Stock rates here differ from the league's (Token Triumph 22% against 14%, Tricky Terrain 11% against 18%) by the noise of 100 games and the different opponent draw, a reminder that ±9 points is the resolution of a 100-table arm.

**What it says.** The channels Forge exposes for per-deck knowledge change how a seat plays only at the margin for these precons, so the §7 exit criterion for Phase 3 is not met by v1, and the data part of a per-deck bot is not where the win rate is. The levers that remain are ours: Phase 4's `PlaybookController` through the public `declareAttackers`, `declareBlockers` and `mulliganKeepHand` hooks (§17 found combat, not casting, to be the gap, and a per-deck attack policy is what the 2026-11-08 decision allows), and Forge's Monte Carlo at desktop strength (`mcmax` arms, added to `runner/ab.py`), which changed a third of the AI's decisions in §17 and was not in this run. Tricky Terrain is the deck to try first with either, since it is the one that moved.

**Monte Carlo at desktop strength: a local check (2026-11-10).** Tricky Terrain, 40 tables (seed 20261112, snapshot 2026-11-08, two games at a time on the session's machine), arms `stock`, `mcmax` and `mcmaxdata`: stock 6 of 40, mcmax 10 of 40, mcmaxdata 10 of 40, +10 points each (95% −7 to +27), 8 discordant pairs against 4 either way (an exact two-sided test at 0.39), and no game identical to its stock twin. The same lean as the CI arms, held through the first 20 tables and the second 20 alike, and still not a result. The event logs (`runner/playstyle.py`) show what the budget buys. The Monte Carlo seat idles half as often: on 12% of its turns in rounds 5–8 against the stock seat's 27%, and 10% against 20% in rounds 9–12 (a turn with three lands and three cards in hand and nothing cast); it spends more of its mana (0.79 against 0.69 mana value per land in rounds 5–8, 0.69 against 0.59 after), attacks on about the same share of turns, and closes big when it closes (13.2 attackers a turn from round 13 on in the games that get there, against 2.3). With its data as well it sends 70% of its attackers at the lowest-life player where stock sends 47%, as the data's LANDS plan and roles intend. Three stock games and one `mcmax` game ran to the 1,800 s clock and count as draws. Cost: a median game of 187 s (`mcmax`) and 169 s (`mcmaxdata`) against 179 s stock, means of 311 s and 321 s against 355 s, so desktop-strength Monte Carlo costs nothing extra on these tables and is affordable in Actions. The 100-table CI run of these arms follows. Rollup: `demo-data/ab/2026-11-10-local/tricky-terrain-mcmax.json`.

**Monte Carlo at desktop strength in CI (2026-11-10, `ab-run` #4: Tricky Terrain, 100 tables, seed 20261120, arms `stock`, `mcmax` and `mcmaxdata`, ten shards of 29 to 105 minutes, 1 h 45 min in all, no failed game; the first run started by a pushed `runner/queue/ab-run.json` rather than a click; rollup in `demo-data/ab/2026-11-10-ab-mcmax/tricky-terrain.json`).** Stock 21 of 100, mcmax 18, mcmaxdata 21: −3 points (95% −12 to +6, 10 discordant pairs against 13, an exact test at 0.68) and 0 (−10 to +10, 14 against 14). The local lean is gone: over the 140 tables of the local check and this run together, mcmax 28 against stock 27, mcmaxdata 31 against 27. The seat plays as the local check said it would. It idles less (13% of its turns in rounds 5–8 against 21%, 27% against 44% in the first four), spends more of its mana (0.82 against 0.73 mana value per land in rounds 5–8), attacks a little more often and closes with more attackers (5.6 a turn from round 13 on against 4.7), and none of it is more wins. Two games in each arm ran to the 1,800 s clock. On Actions runners the budget is not free: a median game of 128 s against 78 s stock, means 234 s against 177 s, so an `mcmax` arm costs about 1.6 times a stock one there. That makes three levers measured at 100 tables or more, Phase 3's data channels (above), desktop-strength Monte Carlo (here) and the go-wide playbook (§20), of which only the playbook, on the one deck written for it, has moved its deck. Desktop-strength Monte Carlo is not a lever for this deck.

**The v1 arms with a second seed (2026-11-10, `ab-run` #2: the same four decks, 100 new tables each, seed 20261110, 1,600 games, 20 jobs in 4 h 18 min, no failed game; rollups in `demo-data/ab/2026-11-10-ab-v1b/`, pooled with v1 by `runner/ab.py pool` in `demo-data/ab/2026-11-10-ab-v1-pooled/`).** The run was clicked for the playbook arms and went out with the defaults, so it is v1 again on new tables: consecutive seeds share opponent trios for 69 of the 100 tables, in different seats and with different shuffles, and no game is a replay. Win rate by arm over the new 100 tables, then the paired difference over all 200 with the discordant pairs (arm only : stock only) and an exact two-sided test:

| Deck | stock | data | mc | mcdata | 200 tables: data − stock (95%) | mc − stock | mcdata − stock |
|---|---|---|---|---|---|---|---|
| Token Triumph | 21% | 24% | 17% | 25% | −2 (−9 to +5), 26:30, 0.69 | −4 (−11 to +3), 21:29, 0.32 | +2.5 (−4 to +9), 28:23, 0.58 |
| Goblin Storm | 12% | 10% | 12% | 7% | +0.5 (−4 to +5), 13:12, 1.0 | +2 (−4 to +8), 18:14, 0.60 | −2.5 (−7 to +2), 8:13, 0.38 |
| Tricky Terrain | 14% | 18% | 15% | 19% | +5.5 (−2 to +13), 32:21, 0.17 | +4.5 (−2 to +11), 29:20, 0.25 | +7.5 (0 to +15), 35:20, 0.06 |
| Hail, Caesar | 12% | 9% | 15% | 14% | −3.5 (−10 to +3), 16:23, 0.34 | +0.5 (−7 to +8), 28:27, 1.0 | −3 (−10 to +4), 23:29, 0.49 |

The second seed is a better test of v1 than v1 was of itself. Three of its four leans reversed on the new tables: Token Triumph's data arm went from −7 to +3, Hail, Caesar's mcdata from −8 to +2, Goblin Storm's mc from +4 to 0, and the stock rates themselves moved by up to nine points between seeds (Hail, Caesar 21% to 12%, Goblin Storm 5% to 12%), which is what ±9 points of resolution looks like in practice. Pooled, every difference for those three decks lies within four points of zero, with intervals of about ±7. Tricky Terrain is the exception, as in v1, and a weaker one: +4, +1 and +5 on the new tables against +7, +8 and +10 before, +5.5, +4.5 and +7.5 pooled, the `mcdata` arm at 35 discordant pairs against 20 (exact test 0.06). The event logs of the new tables repeat v1's story. The data seat attacks on the same share of its turns as stock (Tricky Terrain 35% against 36% in rounds 5–8, Token Triumph 37% against 41%), spends its mana the same way (within a few hundredths of a mana value per land in every round bucket) and idles as often; `mc` at Default budgets is stock with different targets (Tricky Terrain's `mc` seat sends 52% of its attackers at the highest-life opponent where stock sends 16%, and wins the same number of games). Tricky Terrain's data does one visible thing: in rounds 9–12 its seat deals more combat damage with fewer attackers (7.1 a turn from 2.5, against 4.6 from 2.9) and from round 13 on attacks with 5.2 creatures a turn against 2.5, and it is attacked slightly less in return (22 attackers received per 100 opponent turns against 24). Seven of the stock seat's 100 new games ran to the 1,800 s clock, against three for `mcdata`; the five Tricky Terrain shards took 136 to 258 minutes where no other deck's took more than 126, which is this deck's games, not the arms. Phase 3's verdict stands at 200 tables: the data channels are worth nothing measurable for three decks and five to eight points for the one deck whose plan Forge's planner can be told about, and that lean is still short of a result. The playbook measurement is still the next click.

## 20. Phase 4: the playbook controller (2026-11-09)

**Why now.** §19's A/B says the knowledge Forge accepts per deck does not change how these precons play, and §17 says the gap to human play is combat: the stock AI attacks on a third of its turns, keeps blockers against the sum of all three boards and never gangs up. The 2026-11-08 decision allows exactly a per-deck answer: behaviour that reaches one seat through its playbook, with the other seats stock.

**Mechanism.** `vibefish.PlaybookController extends forge.ai.PlayerControllerAi`, installed by `vibefish.VibefishLobbyPlayer extends forge.ai.LobbyPlayerAi` (which overrides the public `createIngamePlayer` to attach it) for the seat the harness is given `--playbook id=file` for. Forge is untouched: the controller's constructor, `declareAttackers`, `declareBlockers` and `mulliganKeepHand` are public, and whatever the playbook does not cover, or declines, is `super`'s, that is Forge's AI with the seat's profile, data and Monte Carlo setting as before. The playbook is the `playbook` object of the deck's data file (`playbook/README.md`); the harness records it in `run.json` and the policy's counters per game.

**Version 1 policies.** `go_wide` (attack): pick the opponent to attack (lowest life, or weakest board), take every creature that can attack it without an attack tax, keep home the toughest ones, at most `max_reserve`, until the strongest single opponent's possible attack next turn is below our life minus `safety_margin`, and declare the rest; with fewer than `min_attackers` able to go, or an illegal declaration, Forge decides. It is the §17 diagnosis turned into a rule: blockers against one board, not three, and an attack every turn the board allows. `mulligan` (optional): keep a hand with a land count in a range, never below a mulligan count. Blocks, casting, targets and everything else stay Forge's in v1. In the first game played with it, the policy took 5 of 11 attack decisions and sent 26 attackers while keeping 7 home.

**Measurement.** The paired A/B of §19 with two more arms: `playbook` (the controller on the focus seat, stock otherwise) and `playbookdata` (controller plus the deck's data and profile). Token Triumph, Goblin Storm and Hail, Caesar carry the go-wide playbook; Tricky Terrain, a lands deck, has none yet.

**Results.** A local check first, 100 tables (seed 20261113, snapshot 2026-11-08, Token Triumph, arms `stock` and `playbook`, two games at a time on the session's machine): stock 18 of 100, playbook 23 of 100, +5 points (95% −3 to +13), 11 discordant pairs against 6 (an exact two-sided test at 0.33), 21 games identical. The first 20 tables had given the same +5; at 100 the interval has narrowed and still includes zero. The event logs of the same tables (`runner/playstyle.py`, which reads A/B runs and splits each arm into the deck under test and its three stock opponents) show the policy doing what it was written to do. In rounds 5–8 the playbook seat attacks on 57% of its turns with 2.2 attackers and 5.3 combat damage a turn, the stock seat on 38% with 1.4 and 4.1; in rounds 9–12, 53% / 2.9 / 7.1 against 33% / 2.2 / 7.8; from round 13 on, 60% / 3.9 / 9.4 against 32% / 3.1 / 7.6. 96% of its attackers go at the lowest-life opponent (stock 59%), and when the weakest player and the biggest board are different people it sends 95% at the weakest, where stock sends 64% at the leader. Two things the first 20 tables had suggested did not survive 100: the playbook seat is attacked exactly as much in return (36 attackers received per 100 opponent turns, against 36 for stock) and is eliminated at the same point (game turn 43 either way). Mana use and idle turns are unchanged, as they should be: only combat is the playbook's. The policy made 353 of 786 attack declarations (45%) and left the rest to Forge; of the fallbacks the harness counted (the 80 tables played after the counters were added), 342 of 345 were for want of three attackers and 3 were declarations Forge rejected. More combat, aimed better, is not yet more wins for this deck: a lean of five points, the same size as the lean its data gave the other way in v1 (§19), and not a result. Rollup: `demo-data/ab/2026-11-10-local/token-triumph-playbook.json`.

The CI measurement (2026-11-10, `ab-run` #3: Token Triumph, Goblin Storm and Hail, Caesar, 100 tables each, arms `stock`, `playbook` and `playbookdata`, seed 20261110, 15 shards in 1 h 34 min; Tricky Terrain was in the run by default and has no playbook, so its five shards failed as expected and only its stock arm played; rollups in `demo-data/ab/2026-11-10-ab-v2/`). Win rate over the same 100 tables by arm, with the paired difference, the discordant pairs (arm only : stock only) and an exact two-sided test:

| Deck | stock | playbook | playbookdata | playbook − stock (95%) | playbookdata − stock |
|---|---|---|---|---|---|
| Token Triumph | 20% | 28% | 20% | +8 (−2 to +18), 18:10, 0.19 | 0 (−10 to +10), 14:14, 1.0 |
| Goblin Storm | 9% | 8% | 8% | −1 (−9 to +7), 8:9, 1.0 | −1 (−9 to +7), 7:8, 1.0 |
| Hail, Caesar | 12% | 15% | 9% | +3 (−4 to +10), 8:5, 0.58 | −3 (−11 to +5), 6:9, 0.61 |

The policy does the same thing on every deck. The seat attacks on half to three fifths of its turns from round 5 on where stock attacks on a third to two fifths (Token Triumph 58% against 41% in rounds 5–8 and 61% against 40% in rounds 9–12, Goblin Storm 54% against 35% and 53% against 30%, Hail, Caesar 52% against 41% and 51% against 35%), with half again as many attackers, and sends nine in ten of them at the weakest player where stock sends six in ten at the leader; it is attacked no more in return, and its mana use and idle turns are stock's. The policy made 31% to 45% of the seats' attack declarations and left the rest to Forge, nearly all for want of three attackers; Forge rejected between 0.4% and 2.7% of its declarations (`attack_invalid`), which fell back to Forge's own at no visible cost. The wins follow only for Token Triumph, the one deck of the three built to go wide: +8 points here and +5 on the local 100 tables with another seed (above), together 51 of 200 against 38 of 200, +6.5 points, 29 discordant pairs against 16 (an exact test at 0.07). Goblin Storm, which wins by storming rather than attacking, is unmoved at 8 to 9%, and Hail, Caesar is within noise either way. The deck's data on top of the playbook (`playbookdata`) takes Token Triumph's gain away (0 points, 14 against 14) and three points from Hail, Caesar, the same downward pull the data showed on its own in §19, so the two do not stack. Tricky Terrain's stock arm replayed run #2's stock tables (the same seed) and won 12 of 100 against 14 before, the same-seed agreement §18 measured. So the go-wide playbook is worth six to eight points for the deck it was written for and nothing for the other two, after 300 CI tables and 100 local ones: the second lean of that size, after Tricky Terrain's data in §19, and like it short of a result at the §7 bar.

## 21. Cast rules: the first per-deck pilot (2026-11-10)

**Why.** Three levers had been measured at 100 tables or more (§19 data channels, §19 desktop-strength Monte Carlo, §20 the go-wide attack) and the largest effect was a lean of six to eight points on one deck. All three left the same decision to Forge: which card to play, when, and aimed at what. §17 had set that decision aside ("casting is not the gap"), on the evidence of the four pod decks, creature decks the stock AI plays well. This section checks it on the decks the league says the sim under-rates (§18), finds that for them casting is the gap, and takes the decision over per deck.

**The build.** Everything here was played on the daily snapshot of 2026-11-10 (`2.0.16-SNAPSHOT-11.10`, tarball sha256 `e72f5dd7cc0d30cb06866dd362ac0b3fea7b5a528217f94d7fc64597958c1ffc`), because the 2026-11-08 build that §17 to §20 were played on was no longer downloadable on 2026-11-10: Forge's `daily-snapshots` release keeps only its newest tarball (the 11-08 and 11-09 files answer 404, §9). Every comparison below is paired on its own build, so nothing here is compared with an 11-08 number, and `forge/SHA256SUMS` is deliberately untouched: the Actions cache that still holds the 11-08 runtime is keyed on that file.

**The diagnosis, in goldfish.** A deck against three do-nothing opponents has no reason to hold anything back, so what the seat leaves uncast is the pilot's doing. Stock AI, Goblin Storm, 100 games (seeds 9001 to 9100; `runner/hands.py held`): from its third turn on the seat leaves 2.5 of its 5.4 lands' worth of mana unspent (47%), ends 56% of its turns holding a card the unspent mana would have paid for and casts nothing at all on 20% of them. The deck is Zada, Hedron Grinder: a spell that targets only Zada is copied for every other creature, so a one-mana "target creature gains haste, draw a card" draws a card per Goblin. The stock seat cast 112 of the deck's seven such spells, 90 of them with Zada on the battlefield, and aimed 33 of those at Zada. Krenko, Mob Boss ("tap: create a Goblin for each Goblin you control") was cast in 22 games and never activated: the stock AI attacks with him (two activations in the other hundred games). Its first opponent died on turn 8.8 and the third on turn 11.4, and 5 of its 936 attacks went at more than one player. A first block of 100 games (seeds 7001 to 7100) reads the same: 45% of the mana unspent, 24 of 65 aimed at Zada, the third opponent dead on turn 11.4. Token Triumph, 12 games, the same picture at smaller scale: 2.4 of 6.0 lands unspent (40%). So §17's finding holds for the pod's creature decks and not for the decks with an engine.

**Cards the stock AI will not play.** `AI:RemoveDeck:All` is not only a deck-building hint. With Monte Carlo off, `AiController.getSpellAbilityToPlay` removes the spells of flagged cards from its candidates before choosing (read from the jar's bytecode in both 2.0.15 and the snapshot, `docs/upstream.md`), so a stock seat never casts them. For Goblin Storm that is Goblin Bombardment, Faithless Looting and Past in Flames, none of them cast in 96 league games; for Token Triumph, Nullmage Shepherd, Dauntless Escort and Slate of Ancestry. Across the league 86 of the 91 decks have at least one card they drew and never once cast in about 100 games (3.6 on average); the five with none (Calling All Angels, Veloci-Ramp-Tor, Reign of Dragons, Animated Army, Exit from Exile) are over-rated against the human table by 20 points on average, where the average deck is over by 4 (the human table is normalised to a lower mean).

**Mechanism.** `PlaybookController` overrides `chooseSpellAbilityToPlay`, the method Forge calls every time a player has priority. Like the attack hook it is public, as are the pieces the override needs (`ComputerUtilAbility.getAvailableLandsToPlay` and `getOriginalAndAltCostAbilities`, `AiController.canPlaySa`, `ComputerUtilCost.canPayCost`, `SpellAbility.setSkip`), so Forge is still unpatched and the harness still compiles against 2.0.15. A playbook's `cast` object is an ordered list of rules (`playbook/README.md` has the reference):

- `play`: cast the first listed card that is in hand or the command zone and affordable, when the rule's conditions hold; with `target`, pointed at one permanent of ours and nothing else. Forge's opinion of the card is not asked, which is also how a flagged card gets cast. A spell that needs targets and has no `target` is cast only if Forge's own logic for it agrees, since that logic picks them.
- `activate`: the same for an activated ability of a permanent of ours.
- `hold`: Forge may not make the play until the rule's conditions hold; a `play` or `activate` rule still may, which is how "only at Zada" is written.

Conditions are text, one comparison each (`creatures >= 3`, `storm >= 4`, `type:Goblin >= 4`, `library >= 40`, `controls Zada, Hedron Grinder`); a list is a conjunction and a second rule is the disjunction. The rules are read on the seat's own main phases with an empty stack, after Forge has made its land drop; whatever no rule covers is Forge's choice, as before. A rule that names a card that is not in the deck, or a condition that does not parse, stops the harness before the first game.

Three things in it are not obvious. A hold is enforced with Forge's own `skip` flag, which drops an ability from one decision; Forge clears the flags it honoured at the start of its next decision, so with two held plays the flags could alternate and one of them always got through, until `forgeChoice` learned to spend one unflagged call to reset Forge's memory (found in the counters as `cast_hold_stuck`, and gone since). A `play` rule casts one card name once a turn unless it says `times`: the first draft recast Haze of Rage with buyback for as long as Storm-Kiln Artist's Treasures paid for it, which is the deck's infinite combo and also 44 casts and 946 copies into a turn that would not end. And the stock AI does the same thing on its own (five of the 200 stock goldfish games spent four to nine minutes in that loop, 360 casts of Haze of Rage in one block of a hundred, `docs/upstream.md`), which is why Haze of Rage is held for its rule only.

**The instruments.** `runner/hands.py` reads the event logs for one seat: `game` prints a game turn by turn (the hand, every spell with its target, the abilities, the attacks), `held` lists the cards kept on turns when the unspent mana would have paid for them, `compare` pairs two goldfish runs on the same seeds. `runner/goldfish.sh -P` plays the deck under its playbook. The logger now marks a copy of a spell (`copy`: they were being counted as cards cast) and records a cast's targets (0.3.0, §6). Goldfish is what makes the loop fast: 100 games take eight minutes on one core and a half, and the paired difference of two runs on the same seeds has a standard deviation of 1.7 turns for Goblin Storm, so 100 pairs resolve a third of a turn. It is blind to anything an opponent does. The measure of that is Token Triumph's attack-only playbook (§20), worth six to eight points at tables: 10.32 turns against stock's 10.38 over the same 40 goldfish seeds, 23 games identical. Goldfish says whether the seat runs its own deck; tables say whether that wins.

**Goblin Storm's playbook, version 2** (`playbook/precons/goblin-storm.json`, twenty rules; its `notes` say why for each). Aim the seven single-target spells at Zada in the first main phase once she has two other creatures, the ones that draw first and the pump last, and hold them otherwise. Tap Krenko every turn before combat. Deploy the permanents in a fixed order of worth, whatever Forge thinks of them. Keep Battle Hymn and Brightstone Ritual for a turn with a hand to spend them on. Cast Haze of Rage before an attack of five or more, six times at most. Put Skullclamp on a 1/1 token after combat while no lord keeps it alive, tap Idol of Oblivion when a token was made, and do not feed tokens to Fountainport. Attack with the go-wide policy and its new `spread` option: what the first defender does not need to die goes at the next one (aimed at the lowest life while the rules were written, at the highest life since the tables below).

The rules were written from twelve games (seeds 4201 to 4212) and corrected from the first hundred. Two corrections are worth keeping. The first complete draft lost a game by drawing its own library: with forty creatures on the table, Fists of Flame at Zada drew forty cards. The draw rules now stop above twelve creatures or under forty cards. And "cheap token makers first, to have more bodies for the copies" read well and played badly: it spent the mana that Krenko needed, and came out. A land-count mulligan (keep three to five) was tried on the same hundred seeds and changed nothing, 9.61 turns against 9.56 with 98 mulligans against 21, so the mulligan stays Forge's.

**Results: goldfish.** Kill turn is the deck's own turn on which the last of the three opponents died; every run is 100 games (twelve in the first row) and every difference is paired on the same seeds (`demo-data/goldfish/2026-11-10-goblin-storm/`). The first three rows were played with the attack aimed at the lowest life, the target the rules were written with.

| Seeds | What they were used for | Stock | Playbook v2 | Stock − playbook (95%) | Playbook faster / same / slower |
|---|---|---|---|---|---|
| 4201–4212 | the twelve games the rules were written from | 11.50 | 8.33 | +3.17 (+1.85 to +4.48) | 12 / 0 / 0 |
| 7001–7100 | first check; four of its games were read to correct the rules | 11.42 | 9.24 | +2.18 (+1.86 to +2.50) | 92 / 6 / 2 |
| 9001–9100 | not looked at before the rules were final | 11.40 | 9.27 | +2.13 (+1.81 to +2.45) | 84 / 14 / 2 |
| 9001–9100 | the same, with the attack aimed as the file now ships (highest life, below) | 11.40 | 9.25 | +2.15 (+1.84 to +2.46) | 85 / 13 / 2 |

The twelve tuning games flatter the rules, as they should; the untouched block is the number: 9.27 turns against 11.40, a little over two turns faster, with every game of both runs won. What the seat does differently on those hundred seeds: it leaves 1.7 of 5.0 lands unspent a turn (34%) where stock leaves 2.5 of 5.4 (47%); it casts 174 of the single-target spells, 172 with Zada on the battlefield and 159 aimed at her, for 903 copies where stock got 229; Zada is on the battlefield on turn 4.9 instead of 5.3; Krenko is activated 45 times in the 23 games he is cast, against never; 165 of its 711 attacks are split between opponents, against 5 of 936; it casts the flagged Faithless Looting 21 times. Its first opponent is dead on turn 7.2 instead of 8.8. The hundred games take 641 s of game time against stock's 2,231 s, most of the difference being the four stock games in the Haze of Rage loop.

What is still in the hand at the end of a turn is mostly removal with nothing to aim at in a goldfish (Vandalblast, Goblin Negotiation, Chaos Warp), Grapeshot, and Great Train Heist, whose extra combat the rules do not use yet. The attack split was the last quarter of a turn: the first version of `spread` sent the attackers left over from a dead opponent back at the dead opponent unless the next one could be killed too, a bug found by reading the code, not the numbers.

**Results: tables.** The paired A/B of §19, arms `stock` and `playbook`, 40 tables on this session's machine (seed 20261130, two games at a time; rollups in `demo-data/ab/2026-11-10-local/goblin-storm-playbook-v2-*.json`). The run in Actions that §7's bar calls for could not be dispatched from the session (the integration may not start workflows), so it goes through `runner/queue/ab-run.json` on `testing`: 200 tables, seed 20261140, on the same 11-10 build while its tarball can still be fetched.

First the playbook as the goldfish runs had left it, attacking the lowest life:

| Goblin Storm (people: 20.9%) | wins of 40 | win rate (95%) |
|---|---|---|
| stock | 4 | 10.0% (4 to 23%) |
| playbook v2, attack at the lowest life | 5 | 12.5% (5 to 26%) |

Difference +2.5 points (95% −10 to +15), four discordant pairs against three. No jump, and not for want of the seat doing its job. Over the same 40 tables it deals 56 damage to players a game where stock deals 24 (median 42 against 16), attacks on 71% of its turns in rounds 5 to 8 with 3.9 attackers where stock attacks on 46% with 1.0, and kills 1.05 opponents a game against 0.57: at least one in 27 games against 18, two or more in 10 against 4. It takes the same damage (50 a game against 48), is attacked as often and dies on the same turn (its own eleventh). What changes is who is left. Stock dies first of the four in 10 of its 36 losses; the playbook seat in 3 of 35, and in 19 of them it was one of the last two. The opponent that finishes it is the one with the highest life in 29 of the 35 (stock: 18 of 36). Aiming at the lowest life is the fastest way to a dead opponent, which is why a goldfish cannot tell the targets apart; at a table it removes the two players who were also attacking the leader and leaves the seat alone with the opponent nobody touched.

So `go_wide` got two more targets, `highest_life` and `biggest_board` (the most power on the battlefield), and the same 40 tables were played again with each, sharing the stock arm:

| attack aimed at | wins of 40 | against stock (95%) | discordant pairs | damage dealt / taken a game | opponents killed a game |
|---|---|---|---|---|---|
| (stock) | 4 | | | 24 / 48 | 0.57 |
| the lowest life | 5 | +2.5 (−10 to +15) | 4 : 3 | 56 / 50 | 1.05 |
| the highest life | 9 | +12.5 (−5 to +30) | 9 : 4 | 63 / 42 | 0.88 |
| the biggest board | 8 | +10.0 (−7 to +27) | 8 : 4 | 48 / 48 | 0.53 |

Aimed at the highest life the seat kills fewer opponents itself, takes less damage, and wins nine games, 22.5%, which is where people have the deck. It is also 40 tables, an interval that includes zero (an exact test on nine against four gives 0.27), and a hypothesis tested on the tables that suggested it; only one of the 40 tables was won under all three targets, which is how much a four-player game moves when anything in it changes. In goldfish the target is free: 9.25 turns against 9.27 on the untouched block, 86 games of the hundred identical. The file ships with `highest_life`, so the queued 200 tables test it on tables it has not seen.

**The confirming run (2026-11-10, `ab-run` #5 on `testing`, started by the queue file: 200 tables Goblin Storm had not seen, seed 20261140, arms `stock` and `playbook`, the 11-10 build, 20 shards, 42 minutes, no failed game; rollup in `demo-data/ab/2026-11-10-ab-v3/goblin-storm.json`).**

| Goblin Storm (people: 20.9%) | wins of 200 | win rate (95%) |
|---|---|---|
| stock | 18 | 9.0% (5.8 to 13.8%) |
| playbook v2 (cast rules, attack at the highest life) | 40 | 20.0% (15.1 to 26.1%) |

Paired difference +11.0 points (95% +4.7 to +17.3); 33 tables won only under the playbook against 11 won only by stock, an exact two-sided test at 0.001. This is the first difference in the project whose interval excludes zero, on tables and seeds the playbook was not written on, and it puts the deck where people have it. The playbook seat wins from every seat (9, 13, 10 and 8 of 50) and its games are shorter (87 s against 110 s on the runners). §7's bar for Phases 3 and 4, a per-deck bot that beats the same deck without it in an A/B, is met for Goblin Storm.

**What it says.** Taking the cast decision over does what none of the knobs did: the seat plays its deck. That is measured twice over on seeds the rules had not seen, two turns of kill speed, and it shows in every table statistic that counts what the seat does (damage, attacks, kills). Whether it wins is a second question with a slower instrument, and the first answer was no, for a reason the logs gave within the hour: a pilot tuned to kill a goldfish kills the wrong player first. The loop for a per-deck bot is therefore two loops: goldfish for the engine (minutes, a third of a turn), tables for everything an opponent does (an hour for 40, thirteen points), and the second needs its own reading of the logs, which `runner/hands.py` and `runner/playstyle.py` now give for an A/B run.

**Next.** (1) The table half of the playbook, in the order the logs suggest: conditions on the opponents' side (their creatures, their power, who is attacking us), so that a rule can say "Blasphemous Act when we are behind on board", which the seat died holding; then blocks and what to keep home, which is still Forge's. (2) What the rules leave unused in Goblin Storm: Great Train Heist's extra combat, Past in Flames, the sacrifice outlets, tutor targets. (3) The same loop on Token Triumph, which has an attack policy and no cast rules, then Tricky Terrain with its eight flagged cards.

## 22. The table half: pressure, duels, triggers, variants (2026-11-11)

**Why.** §21 ended with a pilot that runs its deck and a list of what it could not see. The 31 tables Goblin Storm's version 2 lost of the 40 local ones said what that costs. The seat dies on its own turn 11 with five non-land permanents left; in 28 of the 31 it takes its whole remaining life in one round from one opponent. It loses 9.2 of its own permanents a game on its own turns where stock loses 4.0: the go-wide policy counts attackers, not blockers, and walks 1/1s into creatures that eat them. And it dies holding the cards for a lost board (Empty the Warrens, Grapeshot, the rituals, Past in Flames, Blasphemous Act), because every rule it has is about its own side. Four things followed, each opt-in per deck through its playbook.

**The pressure attack (`"policy": "pressure"`).** The seat attacks when the attack pays. After the reserve is set aside as before, the defenders are sorted by the playbook's `target`. First the kills: an opponent that dies even if each of its blockers stops the biggest attacker it can is attacked with just enough. Then the swing: against each defender the attackers no untapped blocker can kill go for free, and the ones a blocker can kill go only as a crowd, if the damage the crowd gets through is at least `damage_per_loss` (default 3) for every attacker a blocker can take, and never if all of them would die; the defender with the best damage through minus `damage_per_loss` a loss is chosen, a later one in the target order only when it beats an earlier one by a fifth. What stays home after that goes wherever nothing can kill it. Whether a blocker kills an attacker is Forge's own arithmetic (`ComputerUtilCombat.canDestroyAttacker`, `CombatUtil.canBlock`), asked pair by pair and remembered for the declaration. If the plan is empty and the rules of the game demand an attack (a creature that must attack), the declaration goes back to Forge; an empty one is otherwise legal and means the seat keeps its creatures. In goldfish the policy is the go-wide one with the split (nothing blocks); the difference is all at tables.

**The opponents in the conditions.** A rule can now see the other side: `opp_creatures`, `opp_power` and `opp_life` (the largest among the opponents still in), `threat` (the most damage one opponent could attack us with next turn), our own `power`, `main` (1 or 2, the main phase we are in), a named group of cards in hand (`hand:<group>`), and the right-hand side of a comparison may be another metric (`opp_power > power`). That is enough to write "Blasphemous Act when we are behind on board" and "Zada only with a spell to aim at her".

**Duels (`runner/ab.py --opponents 1`).** Between goldfish, which is blind to everything an opponent does, and the four-player tables, where a 40-table check costs an hour and resolves thirteen points, sits the duel: the same paired design against one league deck, the focus deck going first and second in turn. A game takes ten seconds instead of ninety, stock wins a third to a half of them instead of a tenth to a fifth, so the same number of games says more, and what it measures is the part goldfish cannot: blockers, removal, the race. It is blind to table politics (who gets ganged up on), which is what the tables are still for. Sixty duels take ten minutes on the session's machine.

**Variants (`playbook/variants/`, `deck@variant`, `runner/ab.py join`).** A candidate playbook lives in `playbook/variants/<deck>-<name>.json` and is played with `--data` locally or as `deck@name` in the `ab-run` deck list, so several candidates are measured on the same tables without any of them being the shipped file. A candidate needs only its own arm when the tables have been played before: run with `arms: playbook` on the seed of an earlier run, and `ab.py join` lines the games up with that run's stock arm table by table, every arm paired with the first and with any `--against` arm, with an exact test on the discordant pairs. A 200-table candidate costs ten shard jobs of ten to twenty-five minutes.

**Trigger rules (`"triggers"`).** The third kind of decision after "what to cast" and "how to attack": the optional triggers of the deck's own cards. Hail, Caesar's commander reads "whenever you attack, you may sacrifice another creature; when you do, choose two" of two attacking Soldiers, a card, and a burn equal to the tokens we control. Forge asks its AI whether to take an optional trigger (`PlayerControllerAi.confirmTrigger`), the AI asks the sub-ability's logic whether it would play it as a spell, and for Caesar the answer is no on more than four attacks in five (he is paid for on 47 of 264 in forty stock goldfish games). `PlaybookController.confirmTrigger` lets a rule answer instead: `{"accept": ["Caesar, Legion's Emperor"]}`, or with `when` conditions, or `decline`; no rule, Forge answers as before. What an accepted trigger costs and does stays Forge's (it sacrifices its lowest-rated creature and picked the Soldiers and the burn every time). With `-Dvibefish.trace=true` the shard log names every optional trigger Forge turned down on a playbook seat.

**Landfall first and X (`"before_land"`, `"x"`).** The cast rules run after the turn's land drop, because every rule wants the mana. A landfall deck wants the opposite for its payoffs, so a play or activate rule marked `before_land` is also tried before the land is played. And a rule can pay X: `"x": "max"` (or a cap) with `x_min` casts an untargeted X spell for what the mana left pays for, through Forge's own count (`ComputerUtilCost.setMaxXValue`); without it X spells stay with Forge's logic, which kept Hydroid Krasis, Finale of Revelation and Nissa in Tricky Terrain's hand with the mana for them unspent.

**Drafts (`runner/playbook.py draft`).** A first set of cast rules read off Forge's card scripts: cheap mana and land ramp first, the commander, team pumps only before combat with attackers (held otherwise), engines, creatures dearest first, card draw last; instants, aimed spells, X and storm spells, auras, equipment, sweepers and cards whose script already says when (`NeedsToPlay`) stay Forge's, and the draft lists them, the cards Forge's AI never casts by itself, and the deck's optional triggers. It writes a variant file and never a shipped playbook.

**Where it ends (2026-11-11): four decks with a bot.** Each row is one deck in the seat at 200 four-player tables in Actions, the other three seats stock, played once by stock Forge AI and once under the deck's shipped playbook; the dashboard shows the same table (`demo-data/bots.json`).

| Deck | People | Stock AI | Shipped playbook | Difference (95%) | Which tables |
|---|---|---|---|---|---|
| Goblin Storm | 20.9% | 9.0% | 24.0% (version 3) | +15.0 (+8 to +22), exact test 0.0001 | not seen before (`ab-run` #17, §23); the same 48 wins against 18 as on the tables that chose it over version 2 (`ab-run` #11), and version 2 won 20.0% against 9.0% on tables of its own (`ab-run` #5) |
| Token Triumph | 26.5% | 17.5% | 28.0% | +10.5 (+3 to +18), 0.0065 | not seen before (`ab-run` #17, §23); 33.5% against 21.5% on run #6's tables, where it was the best of three candidates (`ab-run` #8) |
| Hail, Caesar | 21.5% | 13.5% | 21.0% | +7.5 (+0 to +15), 0.07 | a second run of new games (`ab-run` #15; 138 of its 200 opponent trios recur from the tables that chose it, which carried nothing over); 25.5% against 17.0% where it was chosen |
| Tricky Terrain | 28.6% | 15.0% | 24.0% | +9.0 (+2 to +16), 0.013 | new tables, the main candidate (`ab-run` #11) |

Two further decks have candidates that did not earn a place: Quick Draw (+3.5 points, exact test 0.42) and Science! (+0.5). The sections below are how each of these came about. Two of these rows first rested on tables that also chose the file (Token Triumph's whole figure, Goblin Storm's version 3); both shipped files were then played against stock on tables of their own (`ab-run` #17: 200 tables each, seeds 20261160 and 20261170, ten and more from every earlier run of the deck), and the table above now carries those figures: every row is from tables that did not choose the file (§23).

**Results: whom the seat attacks is not a lever by itself (`ab-run` #6, 200 tables each, seed 20261141, the 11-10 build; `demo-data/ab/2026-11-11-ab-v4/`).** Token Triumph and Hail, Caesar under playbooks that hold an attack policy and nothing else (go-wide, the highest life first, the split):

| Deck | stock | attack-only playbook | difference (95%) | discordant |
|---|---|---|---|---|
| Token Triumph | 43 (21.5%) | 39 (19.5%) | −2.0 (−7.7 to +3.7) | 15 to 19 |
| Hail, Caesar | 34 (17.0%) | 32 (16.0%) | −1.0 (−6.9 to +4.9) | 17 to 19 |

Nothing, on either deck. With §20's lean for Token Triumph under the lowest-life version (+6.5 over 200 tables, exact test 0.07) this closes the attack order as a lever for these two: what moved Goblin Storm was the cast rules, with the attack order deciding how much of it reached the table. The two stock arms are the baseline the cast-rule candidates of both decks are paired with.

**Results: Goblin Storm's candidates (`ab-run` #7 joined with #5 on its 200 tables, seed 20261140; `demo-data/ab/2026-11-11-ab-v5/goblin-storm.json`).**

| Arm | wins of 200 | against stock (discordant, exact test) | against the shipped v2 |
|---|---|---|---|
| stock | 18 (9.0%) | | |
| shipped v2: cast rules, go-wide at the highest life | 40 (20.0%) | +11.0 (33 to 11, 0.001) | |
| pressure, `damage_per_loss` 3 | 32 (16.0%) | +7.0 (27 to 13, 0.04) | −4.0 (19 to 27, 0.30) |
| pressure, `damage_per_loss` 2 | 28 (14.0%) | +5.0 (23 to 13, 0.13) | −6.0 (17 to 29, 0.10) |
| pressure 3 and two rules for a lost board | 28 (14.0%) | +5.0 (22 to 12, 0.12) | −6.0 (17 to 29, 0.10) |
| pressure 3 and Zada held until she can be aimed at | 39 (19.5%) | +10.5 (35 to 14, 0.004) | −0.5 (24 to 25, 1.0) |

Every candidate beats stock and none beats the shipped file, which stays. The pressure attack had looked better where it was written: 11 wins against go-wide's 9 on the 40 local tables (stock 4) and 24 against 21 in 60 duels (stock 16; `demo-data/ab/2026-11-11-local/`). On 200 tables it is four points worse, and the seat that keeps its creatures home is out of the game three turns sooner than the one that swings (game turn 38 against 41), not later. The two rules for a lost board (Empty the Warrens and Blasphemous Act when behind) cost four wins where they were meant to save games. Holding Zada until she can be cast and aimed at in the same turn is the one change that helped, seven wins on top of pressure; `goblin-storm@zadawide` put it on the shipped attack (`ab-run` #11, the same 200 tables; `demo-data/ab/2026-11-11-ab-v8/goblin-storm.json`): 48 wins where version 2 won 40 and stock 18, +15.0 points against stock (40 tables to 10, exact test below 0.0001) and +4.0 against version 2 (24 to 16, exact test 0.27). The hold has now been worth seven wins under one attack and eight under the other, neither difference significant by itself; it ships as version 3 because both point the same way and nothing says it costs anything. These tables have chosen among six candidates by now, so 24.0% is flattered by the choosing: 20.0% is still the figure from tables the rules had not seen.

**Results: Token Triumph's cast rules** (`playbook/variants/token-triumph-cast*.json`: the mana creatures, Emmara at once, the two auras that give her a tap ability aimed at her and the Elf Warrior ability one of them grants used every first main phase, the anthems, Overrun only before combat with five attackers, the card draw with a library guard, the three cards Forge's AI never casts). Goldfish on seeds 5001 to 5040: stock 10.38 turns, the attack-only playbook 10.32, the cast rules 9.05 under go-wide (+1.32, 95% +1.02 to +1.63), 9.12 under pressure, 9.40 with everything but the anthems cast after combat. Sixty duels (seed 20261151): stock 33, the cast rules under go-wide 40 (10 to 3, exact test 0.09), under pressure 33 of 59, cast after combat 38.

At the tables (`ab-run` #8 joined with #6 on its 200 tables, seed 20261141; `demo-data/ab/2026-11-11-ab-v6/token-triumph.json`):

| Token Triumph (people: 26.5%) | wins of 200 | against stock (discordant, exact test) |
|---|---|---|
| stock | 43 (21.5%) | |
| attack-only playbook (version 2) | 39 (19.5%) | −2.0 (15 to 19, 0.61) |
| cast rules, go-wide at the highest life | 67 (33.5%) | +12.0, 95% +4 to +20 (47 to 23, 0.006) |
| cast rules, pressure attack | 60 (30.0%) | +8.5 (42 to 25, 0.05) |
| cast rules, everything but the anthems after combat, pressure | 58 (29.0%) | +7.5 (40 to 25, 0.08) |

The second difference in the project whose interval excludes zero, on tables the rules were not written on, and the same shape as Goblin Storm's: the attack policy alone does nothing, the cast rules under it are worth twelve points, and go-wide again beats pressure (by seven wins here, eight there). The go-wide version is now the deck's shipped playbook (version 3). It overshoots the human figure where Goblin Storm landed on it; one seat playing its deck properly among three stock seats is not the table people play at. A follow-up (`token-triumph@cast2`: Mentor of the Meek's pay-one-draw trigger taken, and the token makers the seat left idle used as mana sinks after combat) wins 66 on the same tables against the shipped version's 67: nothing, as in goldfish, where the seat turned out to have spent that mana already.

**Results: Hail, Caesar's rules** (`playbook/variants/hail-caesar-*.json`: the rocks, Caesar as soon as there is another creature, Heroic Reinforcements only before combat with three attackers, Wasteland Raider only when the opponents have creatures to give up, the engines and anthems with Marshal's Anthem among them, the creatures; and the trigger rule). Goldfish on seeds 6001 to 6040:

| Hail, Caesar | kill turn | stock − it (95%) |
|---|---|---|
| stock | 12.47 | |
| cast rules, pressure attack | 11.45 | +1.02 (+0.60 to +1.45) |
| and Caesar's trigger taken with a token to give up | 10.82 | +1.65 (+1.17 to +2.13) |
| and Caesar's trigger taken every time | 10.10 | +2.38 (+1.94 to +2.81), faster on 39 seeds of 40 |

The trigger rule is worth as much as all the cast rules together. Sixty duels (seed 20261152): stock 22, the trigger every time 31 (+15.0 points, 12 to 3, exact test 0.035), only with a token 33 (13 to 2, 0.007).

At the tables (`ab-run` #9 joined with #6 on its 200 tables, seed 20261141; `demo-data/ab/2026-11-11-ab-v7/hail-caesar.json`):

| Hail, Caesar (people: 21.5%) | wins of 200 | against stock (discordant, exact test) |
|---|---|---|
| stock | 34 (17.0%) | |
| attack-only playbook (version 2) | 32 (16.0%) | −1.0 (17 to 19, 0.87) |
| cast rules, go-wide | 41 (20.5%) | +3.5 (29 to 22, 0.40) |
| and Caesar's trigger every time | 44 (22.0%) | +5.0 (32 to 22, 0.22) |
| and Caesar's trigger only with a token to give up | 51 (25.5%) | +8.5, 95% +1 to +16 (37 to 20, 0.03) |
| trigger every time, pressure attack | 45 (22.5%) | +5.5 (34 to 23, 0.18) |

Every candidate beats stock and the order is the one the pieces suggest: the cast rules, then the trigger, then the trigger without spending real creatures on it (fifteen tables won only with the token condition against eight only without). The goldfish order was the other way round for the last step (taking the trigger every time is 0.6 turns faster against no opponents), which is goldfish being blind to what a board is worth when someone attacks it. The best candidate is now the deck's shipped playbook (version 3). It is the best of four on these tables, so its interval is flattered by the choosing, and it was played again on tables it had not seen, as Goblin Storm's was.

The confirming run (`ab-run` #15, 200 new games, seed 20261143; `demo-data/ab/2026-11-11-ab-v9/hail-caesar.json`): stock 27 wins (13.5%), the shipped playbook 42 (21.0%), +7.5 points (95% +0 to +15; 37 tables won only under the playbook against 22 only by stock, exact test 0.07). The size holds in the second run (+8.5 where it was chosen, +7.5 where it was not) and the interval of the second run alone just reaches zero; over the 400 tables together it is 93 wins against 61, +8.0 points (95% +3 to +13, 74 to 42, exact test 0.004; `hail-caesar-pooled.json`), with the first half of those chosen. The playbook seat sits where people have the deck (21.5%).

The second run's tables are new games but not all new opponents, which was seen only afterwards (2026-11-11). `ab.py` draws the opponents of table i with seed × 31 + i, and the seed was two from run #6's, so 138 of the 200 tables seat the same three opponents as a table of run #6, in other seats and on other shuffles. Nothing carried over that can be measured: over those 138 pairs of tables the two runs' outcomes are unrelated (stock won 24 of them in each run and both on 4, where chance gives 4.2; the playbook 38 and 29, both on 9, chance 8.0; the paired differences correlate at −0.14), and the playbook's gain in the second run is, if anything, on the 62 tables whose opponents were its own (13 wins against stock's 3) more than on the 138 (29 against 24). So the run stands as a confirmation, with that said beside it. From here on a deck's runs are kept ten seeds apart, which no two 200-table runs closer than seven are, and `runner/ab.py play` says so when `demo-data/ab/` holds a run of the deck on a nearby seed. The other confirming runs are clear of it: Goblin Storm's (seed 20261140) is ten from the 40 local tables that chose its attack target, Tricky Terrain's (20261142) had no four-player candidate tables before it.

**Results: Tricky Terrain's candidate** (`playbook/variants/tricky-terrain-lands.json`: Omo at once, the land finders, the landfall payoffs before the land, the ramp, the big creatures on curve, the X spells as mana sinks, Seer's Sundial's trigger with a small hand). Stock casts its three-mana commander on turn six in the first game read and sits on three six-drops with seven lands. Goldfish on seeds 8001 to 8040 (`demo-data/goldfish/2026-11-11/`): stock 13.39 turns over the 33 games it finishes (six of the other seven reach the turn cap of twenty rounds without a kill, one the clock), the candidate 10.64 over 39 (the fortieth reaches the turn cap), and on the 32 seeds both finish it is 2.94 turns faster (95% +2.29 to +3.58), faster on every one. The rules that pay X fired 23 times in the forty games and moved nine kill turns by a turn one way or the other (+0.13 on the mean, 95% −0.17 to +0.43); the Sundial rule fired once and moved nothing. In goldfish the gain is the commander, the curve and the landfall order; what the X spells and the cards are worth is a question for the tables. Version 4 added the deck's two-land combo as its first rule (Thespian's Stage becomes a copy of Dark Depths, the copy is sacrificed for Marit Lage; Forge's AI had the Stage in play for 75 turns of forty games and never used it) and version 5 a removal rule (Pongify and Beast Within when an opponent threatens seven or more); neither moves a goldfish kill turn.

Duels say something goldfish cannot (60 duels, seed 20261153; `demo-data/ab/2026-11-11-local/tricky-terrain-duels.json`): stock wins 17, the candidate under the pressure attack 18 (version 3) and 17 (version 5), and under the go-wide attack 20. Three turns of goldfish speed bought nothing one on one. Under pressure the seat used more of its mana than stock (idle turns 6% against 23%) and still dealt 25 damage a game where it deals 120 to three goldfish: the policy held back more attackers than it sent (860 against 700), and a ramp deck that does not swing loses the race it was already losing. It lost with its answers in hand (Curse of the Swine, Beast Within, Oblivion Stone, Summary Dismissal: all cards Forge's AI never casts), and the removal rule fired fifteen times in sixty games without changing a result. The go-wide version went to the tables as the main candidate.

At the tables (`ab-run` #11, 200 new tables, seed 20261142; `demo-data/ab/2026-11-11-ab-v8/tricky-terrain.json`):

| Tricky Terrain (people: 28.6%) | wins of 200 | against stock (discordant, exact test) |
|---|---|---|
| stock | 30 (15.0%) | |
| playbook, go-wide | 48 (24.0%) | +9.0, 95% +2 to +16 (33 to 15, 0.013) |
| the same with key cards for the tutors (playbookdata) | 50 (25.0%) | +10.0 (43 to 23, 0.019) |
| the same rules, pressure attack | 37 (18.5%) | +3.5 (30 to 23, 0.41) |

The fourth deck with a result, and the duels were wrong about it: a ramp deck that loses one on one wins at a table where the first eight turns are not all aimed at it. The playbook is now the deck's shipped one (its first). Putting Dark Depths and Thespian's Stage first among the cards the tutors fetch adds two wins, which is nothing (36 tables to 34); the deck's data file is left as it was. Pressure loses to go-wide for the third deck running (eleven wins here). Twenty-seven of the 800 games were draws (the clock or the turn cap), four of them stock's, and some of this deck's games crawl: the last shard of this run played for three hours. Why has not been looked into; in a Token Triumph duel that crawled the same way the stock opponent's every decision was timing out on a wide board (`docs/upstream.md`).

**Which deck next: an audit, and Quick Draw.** The four first bots were picked by hand. The next ones are picked by what stock Forge leaves undone: twelve stock goldfish games a deck, read with `hands.py held` (mana unspent, cards kept) and the new `hands.py abilities` (the deck's permanents with an activated ability, read from Forge's scripts: turns in play against times used), over the decks the league under-rates most against people. Tinker Time (7% against 24%, the widest gap) plays its cards and uses its abilities in goldfish and its draft gains half a turn: whatever the stock AI gets wrong there is not visible without opponents. Maestros Massacre is a reactive deck that goldfishes in fifteen turns holding spells with nothing to aim at. Science! leaves three free tap abilities unused for sixty turns and declines its energy triggers 233 times in forty games, yet rules for all of that are worth a third of a turn (12.03 against 12.38, 95% −0.13 to +0.83): the energy runs out, not the willingness. At the tables the same file wins 15 where stock wins 14 (`ab-run` #14, 200 tables, seed 20261145; `demo-data/ab/2026-11-11-ab-v9/science.json`): a deck people win 17% with stays at 7%, and what is wrong with the stock AI's Science! is not what the audit can see. Quick Draw (Stella Lee; 18.8% against 25.9%) leaves 47% of its mana unspent and casts nothing on a quarter of its turns, sitting on its cantrips. Its candidate (`playbook/variants/quick-draw-spells.json`: the spell payoffs first, then every cheap spell the mana allows, Windfall and Epic Experiment, which Forge's AI never casts) kills in 11.72 turns against stock's 13.72 on seeds 1001 to 1040, 1.97 turns faster on the 38 both finish (95% +1.38 to +2.56); the draft alone gets 0.97. At the tables it is a lean and no more (`ab-run` #15, 200 tables, seed 20261144; `demo-data/ab/2026-11-11-ab-v9/quick-draw.json`): 38 wins against stock's 31, 19.0% against 15.5%, +3.5 points (95% −4 to +11, 31 tables to 24, exact test 0.42), after a lean of the same size in 60 duels (17 against 14). Two turns of goldfish speed bought Goblin Storm eleven points and Quick Draw three and a half; why the speed did not carry over has not been read from its games yet. It stays a candidate.

**The bots on the dashboard (`runner/bots.py`, `demo-data/bots.json`).** `playbook/bots.json` lists the decks that have a bot or a candidate and which measurement files are theirs; `runner/bots.py` copies the numbers out of those files (the paired table result from an `ab.py` rollup or join, the goldfish pair, the human win rate) into `demo-data/bots.json`, and the dashboard shows them as one table above every run: people, stock AI, with playbook, the difference with its interval, goldfish turns, status. A plain table in the existing style; the file is optional and the page is unchanged without it.

**A durable copy of the Forge builds (2026-11-11).** Forge's `daily-snapshots` release holds one tarball at a time: a build is there until the next snapshot replaces it. Every result since §21 is on the 11-10 snapshot, which on 2026-11-11 was still upstream's current tarball (no 11-11 build had been published by 16:16 UTC) and will go with the next one; the 11-08 build of the league and §17 to §20 was already gone from upstream and existed only in the Actions cache, which is dropped after a week without use. `forge-archive.yml` (started by `runner/queue/forge-archive.json`) takes a build's runtime as `forge/fetch-forge.sh` assembled it, from the cache or from upstream while the tarball is still there, packs it without Forge's profile directory and without the AI profiles our own runners add, and attaches it to the release `forge-runtimes` of this repository with its checksum and a note of the build; the release notes carry Forge's licence terms and where its source is. `forge/SHA256SUMS` lists the two archives (and now the 11-10 installer tarball's checksum, which had been left out to keep the cache key), and `forge/fetch-forge.sh` fetches a pinned `FORGE_SNAPSHOT_BUILD` from the archive when it is listed, verified. A fresh fetch of the 11-10 archive is file for file the runtime the results were played on, and replays the same goldfish games. In Actions the first run after the change (`ab-run` #16, Goblin Storm, 40 tables, seed 20261146; `demo-data/ab/2026-11-11-ab-archive-check/`) missed the cache on both shards, as a changed checksum file makes it, downloaded the archive, verified it and played within two seconds of starting (stock 4 wins of 40, the shipped playbook 8). An archive on the release is not replaced by running the workflow again: published runs are pinned to its checksum and a second pack of the same build need not be byte-identical, so the workflow keeps what is there unless the request says `replace`. The archive is for reproducing published runs, not for staying on old builds: a new snapshot is adopted as before, archived the day it is first used for a published run, and the league is re-run on the 2.0.16 release when it lands.

**The league can seat the bots (`runner/league.py play --playbooks`, the `playbooks` input of `league-run.yml`).** A deck with a shipped playbook is played under it in whatever seat the schedule gives it; every other seat is stock, untouched. Nothing is switched on by default, the run id of such a run ends in `-bots`, and its rollup names the decks. With three shipped playbooks among 91 decks a league run would move three rows of the table and little else, so it has not been run; it is the instrument for the day the bots are many.

**Results: a draft is not a bot.** The mechanical drafts in goldfish, each on its deck's seeds above, cast rules only and Forge's own attack:

| Deck | stock − draft (95%) | draft − the deck's hand-written rules |
|---|---|---|
| Goblin Storm | 0.00 (−0.42 to +0.42) | +2.00 (+1.46 to +2.54) |
| Token Triumph | +0.05 (−0.35 to +0.46), two games unfinished | +1.21 (+0.84 to +1.58) |
| Hail, Caesar | +0.23 (−0.28 to +0.73) | +2.15 (+1.79 to +2.51) |
| Tricky Terrain (27 games) | +1.18 (+0.26 to +2.11) | |
| Quick Draw | +0.97 (+0.44 to +1.51) | +1.10 (+0.60 to +1.60) |
| Science! | −0.23 (−0.67 to +0.22) | |
| Tinker Time | +0.53 (+0.23 to +0.82) | |

On the three decks whose engine is one card the draft is worth nothing; where stock does not cast its cards at all (Tricky Terrain, Quick Draw) it is worth a turn, half or less of what the deck's own rules are. The gain is not in "cast your mana, your commander and your creatures in a sensible order"; it is in the lines one deck has and no other: aim at Zada, tap Emmara, pay Caesar, Omo before anything and the payoff before the land. That is the case for per-deck bots made with a measurement, and it rules out the shortcut of drafting 91 playbooks: the draft tool saves the typing and lists what needs a reader (the cards Forge's AI will never cast, the optional triggers), no more.

**What it says.** (1) The order is: the deck's own engine first (goldfish finds it in minutes), then tables; attack policy alone moved nothing on three decks, and the cast rules moved two of them by eleven and twelve points and the third, with its trigger rule, by eight and a half; Tricky Terrain, which never had an attack-only version, gained nine. (2) Small samples lie about small differences in both directions. Forty tables and sixty duels were right that every candidate beats stock and wrong about which candidate is best; candidates are compared at 200 tables on shared seeds, which `deck@variant` and `join` make cheap, and local runs are for bugs and for effects of ten points and more. (3) A duel is not a small table: the pressure attack led go-wide in duels and trailed it at four players. One reading, not yet checked in the logs, is that keeping creatures home wins a race against one opponent and does nothing about the two the seat was not racing. (4) Rules written from a post-mortem of losses are hypotheses like any other: the lost-board rules read well and cost wins. (5) Goldfish says whether the seat runs its deck, not what that is worth: three turns faster was worth nine points to Tricky Terrain, two turns eleven to Goblin Storm and three and a half to Quick Draw, and of the two versions of Hail, Caesar's trigger rule the one that is 0.6 turns slower in goldfish was the better one at the tables. Every candidate still has to sit the exam.

**Next.** (1) More decks, chosen by the audit and judged at the tables: the method (goldfish for the engine, `held`, `abilities` and the trigger trace for what stock leaves undone, a candidate file, 200 tables against stock) takes a deck from nothing to a verdict in a few hours, most of it waiting for Actions, and it has said yes four times and no twice. (2) What the rules still cannot do, in the order the losses suggest: answer a threat (Tricky Terrain died holding Beast Within, Curse of the Swine and Oblivion Stone, cards Forge's AI never casts, and a rule that casts two of them at the target Forge picks changed nothing), choose the modes and the targets of a trigger the rule accepts, respond with a spell on the stack (Stella Lee's copy), block. (3) The pressure attack has lost to go-wide on three decks at the tables and holds back more than it sends; it stays in the code as an option no shipped playbook uses, and wants either its accounting fixed (it assumes every blocker that can kill an attacker will, and prices each loss at three damage, a 1/1 token the same as a real creature) or removing. (4) Read Quick Draw's and Science!'s table games for why goldfish speed did not carry over. (5) A league run with the bots seated (`league.py play --playbooks`) once enough decks have one for it to move more than four rows.

## 23. Where the four bots stand (2026-11-11)

**The confirming runs (`ab-run` #17: Token Triumph's version 3 on seed 20261160 and Goblin Storm's version 3 on seed 20261170, each against stock on 200 tables whose opponents the deck had not met; the 11-10 build from this repository's archive; 20 shards, 1 h 18 min: thirteen shards were done within 40 minutes and the last took 78; no game missing; rollups in `demo-data/ab/2026-11-11-ab-v10/`).**

| Deck (people) | stock | shipped playbook | difference (95%) | discordant pairs, exact test | on the tables that chose it |
|---|---|---|---|---|---|
| Token Triumph (26.5%) | 35 wins (17.5%, 13 to 23%) | 56 (28.0%, 22 to 35%) | +10.5 (+3 to +18) | 38 to 17, 0.0065 | 67 against 43, +12.0 |
| Goblin Storm (20.9%) | 18 wins (9.0%, 6 to 14%) | 48 (24.0%, 19 to 30%) | +15.0 (+8 to +22) | 42 to 12, 0.0001 | 48 against 18, +15.0 |

Both hold. Token Triumph gives back a point and a half of the twelve it had where it was the best of three, which is what choosing costs. Goblin Storm's version 3 repeats its count to the game: the Zada hold shipped on a lean (eight wins over version 2 on shared tables, exact test 0.27), and has now been seen at 24.0% on tables of its own where version 2 had 20.0% on its own. Those two runs are on different tables, so they are not paired, and the step from version 2 to version 3 is still a lean. Seven of the 800 games were draws (five on the 1,800 s clock, two declared by Forge). With these, every row of §22's table is from tables that did not choose the file. Over the four decks the playbook seat is within 0.5 to 4.6 points of people's figure for the deck (mean gap 2.4), where the stock seat on the same tables is 8 to 14 points under it (mean 10.6); each of the eight figures carries an interval of four to seven points either way, and people's figure is the deck against whatever the rest of the table played (`runner/reference/playgroup-commander.json`), not against three stock seats.

**How the seat plays the table, and how it loses (`runner/losses.py`, new with this section; the 800 games of run #17; `demo-data/ab/2026-11-11-ab-v10/*-losses.json`).** `hands.py` and `playstyle.py` say whether a seat runs its deck. This reads the same logs for what the seat does about the other three players.

| The seat under test, a game | Token Triumph, stock | playbook | Goblin Storm, stock | playbook |
|---|---|---|---|---|
| damage dealt to players; opponents it killed | 49; 0.58 | 63; 0.78 | 30; 0.47 | 54; 0.73 |
| own creatures lost on its own turns | 1.8 | 3.9 | 6.1 | 9.2 |
| spells aimed at an opponent or an opponent's card | 0.86 | 0.90 | 0.96 | 0.77 |
| attackers sent at the seat; share it blocked | 15.9; 19% | 15.4; 16% | 13.1; 21% | 11.9; 15% |
| games with a mulligan | 22% | 22% | 18% | 18% |
| losses: first out / second / third | 73 / 56 / 35 | 73 / 30 / 41 | 51 / 51 / 78 | 32 / 41 / 79 |
| last own turn of a loss: life; nonland cards in hand, castable | 11; 2.3, 2.0 | 14; 2.9, 2.6 | 13; 2.9, 2.8 | 13; 3.4, 3.2 |
| damage from then until it died; one opponent's share | 30; 95% | 31; 95% | 34; 96% | 34; 99% |

The rules made 79% of Token Triumph's spell casts and 65% of Goblin Storm's, and the attack policy 44% and 38% of their attack declarations (the rest go to Forge for want of three attackers). What that buys is the first row, and it costs the second: the seat deals 30% to 80% more damage, kills more opponents, and loses one and a half to two times as many of its own creatures on its own turns. Every row below those is Forge's, and reads the same in both arms or a little worse under the playbook. The seat aims under one spell a game at anything an opponent has. It blocks one attacker in six, fewer than stock, its creatures being tapped. It mulligans exactly as often as Forge does (people take one in 36% of games). And it loses the way stock loses: within a turn cycle, to one opponent (in 88% of Token Triumph's losses under the playbook and 97% of Goblin Storm's, one opponent deals four fifths of the last blow), from 13 or 14 life, holding three cards its lands would have paid for (85% and 92% of losses with at least one). For Goblin Storm those cards are its own finishers rather than answers: Grapeshot (in 42 of its 152 losses), Goblin Bombardment (30), Haze of Rage (28), Empty the Warrens (27), Battle Hymn (24), Great Train Heist (23). For Token Triumph: Harvest Season (25 of 144), White Sun's Zenith (24), Ajani, Caller of the Pride (17), Overrun (17), Citywide Bust (14). The two decks differ in when they go: Goblin Storm's seat is out first in 32 of its 152 losses where stock is in 51 of 180, and is the last one beside the winner in 79; Token Triumph's is out first exactly as often as stock (73 games each).

One more thing the tables show that goldfish does not. Under the playbook Goblin Storm leaves 35% of its lands' mana unspent at these tables and stock 36% (`hands.py held`; in goldfish it was 34% against 47%), and ends 43% of its turns holding a card that mana would have paid for, in both arms. One reading, not checked in the logs: the holds keep the one-mana spells for a Zada the table has killed (they turn down seven or eight of Forge's choices a game). Token Triumph leaves 34% against stock's 39%.

So what a bot is today is one deck's own plan, played; everything that concerns the other three players is stock Forge.

**The four bots at one table (a local check; `demo-data/ab/2026-11-11-local/four-bots-table.json`).** No run before this one seated more than one bot. One table of the four decks that have a shipped playbook (seat order Goblin Storm, Token Triumph, Hail, Caesar, Tricky Terrain; seeds 20261181 to 20261200; the 11-10 build on the session's machine, two games at a time), played once with every seat under its playbook and once with every seat stock:

| | games | game turns (95%) | rounds (turns over four) | the winner's own turns | first player out, game turn | decided | seconds a game, median |
|---|---|---|---|---|---|---|---|
| four bots | 20 | 39.0 (35.8 to 42.2) | 9.75 | 11.1 | 33 | 20 | 28 |
| the same seats, stock | 17 | 54.2 (46.5 to 61.9) | 13.5 | 16.0 | 42 | 15 | 118 |

On the 17 seeds both arms played, the bots' game is 16.2 turns shorter (95% 9 to 23) and shorter on 16 of them; half of the bots' games are over within nine rounds. People's games last 8.75 rounds and the stock league's 12.0 by the scorecard's turns over four (§18). One bot among three stock seats takes half a round off a game (46.2 turns to 43.5 for Goblin Storm above, 46.6 to 44.6 for Token Triumph); four take off four. So the length of a sim game follows the pilots, not the decks, and a table of bots plays a game one to two and a half rounds longer than people's where the same seats under stock play five to seven longer. The range is the measure's: a table shrinks as players go out, so turns over four understates rounds everywhere this document uses it, and the winner's own turn count (11.1 here) is the stricter figure.

What it does not say. Twenty games of one table say nothing about who wins (Token Triumph 8, Hail, Caesar 6, Goblin Storm 3, Tricky Terrain 3; people have them at 26.5, 21.5, 20.9 and 28.6%). Every one of the four aims at the highest life (83% of their attackers went there, and 5% at the weakest player when that was someone other than the biggest board), a target chosen against stock opponents (§21) and never tested against seats that do the same. All four win by attacking, so a table of them is a race and nothing else. And the stock arm is short: two of its 17 games were draws (one on the clock, one declared by Forge), an eighth was stopped by hand after eleven minutes on one turn, and the bots' second shard was stopped in its first game with Tricky Terrain's Scute Swarm past a thousand copies (`docs/upstream.md`). Four go-wide decks make boards on which Forge's AI crawls under any pilot; the bots mostly end the game before that.

**Forge 2.0.16 is out, and it is the build these results are on.** The release ("Star Trek Release", tag `forge-2.0.16`) was published on 2026-11-11; its `build.txt` says 01:23 that day, seven hours after the 11-10 snapshot's 18:15. Compared entry by entry with the archived 11-10 runtime: 23 of the jar's 19,256 entries differ, thirteen of them build metadata, nine GUI and tutorial classes, and one game class, `forge.game.card.CardFactory`, where a copied spell now has `castFromPlayEffect` cleared. No class under `forge/ai` differs (361 in each). Under `res/` two card scripts differ (Kirk, Commanding Officer and Lotus Ring, which no league deck holds) and one language file; the AI profiles, the AI lists and the 184 precon files are identical. The harness compiles against the release jar unchanged. Because the one game change is in copies of spells, which is Goblin Storm's engine, twenty of its published goldfish games were replayed on the release (seeds 9001 to 9012 under the shipped playbook, 9002 to 9009 stock, `demo-data/goldfish/2026-11-11/goblin-storm-v3-seeds-9001-9100.json`): all twenty match the 11-10 games in length and kill turn. For this pair of builds, then, moving the pin is not the baseline change §9 warns of: the bots' results carry over. The pin has not moved yet: `forge/VERSION` still says 2.0.15 (installer `forge-installer-2.0.16.tar.bz2`, 301,074,823 bytes, sha256 `feb1338c2f4a8c62e9289b6270caa7fcc38f2441d5ec4d7cff237c2c1a3b15d0`).

**The league does not need replaying (corrected the same day).** This section first said that what the release still owed was the league, whose published run is two builds back, on the 11-08 snapshot (§18). The owner asked what a second all-stock league would show that the first had not, and the answer in the data is nothing. Between 11-08 and 11-10 the AI did change (141 jar entries differ, 32 of them under `forge/ai`, `AiController` and `PlayerControllerAi` among them), but stock play at the tables did not move. The four decks whose stock arms were played on both builds (`demo-data/ab/`, every four-player run, a repeated seed counted once):

| Deck, stock AI among three stock league decks | 11-08 build | 11-10 build | in the league (11-08) |
|---|---|---|---|
| Goblin Storm | 17 of 200, 8.5% | 44 of 480, 9.2% | 5 of 96 |
| Token Triumph | 61 of 300, 20.3% | 78 of 400, 19.5% | 14 of 100 |
| Hail, Caesar | 33 of 200, 16.5% | 61 of 400, 15.2% | 14 of 96 |
| Tricky Terrain | 52 of 340, 15.3% | 30 of 200, 15.0% | 18 of 100 |

A stock table takes as long on either: 49.0 game turns over those 1,040 games on 11-08, 48.3 over the 1,880 stock-arm games on 11-10 (Quick Draw's and Science!'s included), 48.0 in the league. So the published league still describes the build in use, and every new deck's A/B brings its own stock arm on the current build, which is the baseline that deck is judged against. Nor is the 91-deck league the instrument for the bots while they are few: `league.py play --playbooks` changes the pilot of the decks that have a playbook and nothing else, so with four bots five tables in six seat none (C(87,4)/C(91,4) = 0.83) and replay what is already known. The instrument for "how do the bots do among bots" is a league of the bot decks alone. `runner/league.py` takes any list of four or more decks (`--league`; a dry run of the four bot decks schedules 200 games in 50 cycles, each deck in every seat 50 times, every seat under its playbook), but `league-run.yml` reads only the 91-deck file, so that run has no way to start in Actions yet.

**A tool that had stopped working.** `runner/playstyle.py` on a pod or league run (anything but an A/B directory) recursed until Python stopped it: the helper that labels a seat called itself where it should have called `arm_of`, since the commit that taught it A/B runs. Fixed here; the A/B path, the only one used since, was not affected.

**What it says.** (1) The four bots are confirmed: each wins 7.5 to 15 points more than stock on tables that did not choose its file, and each sits within five points of where people have the deck, at a table of three stock seats. (2) That is the whole of the claim. The rules play the deck's own plan; the numbers that would show a seat reading the table (spells aimed at opponents, blocks, mulligans, how it dies and what it dies holding) are stock's, unchanged. §22's list of what the rules cannot do is the list of what the bots do not do. (3) A table of bots is a different game from a table with one: four rounds shorter, and decided by who races best. Nothing chosen against stock opponents has been tested there, and no deck's win rate among bots has been measured at all, in Actions or anywhere. That measurement, several bots at one table judged against people's ordering of the same decks, is the one the bots exist for.

## 24. Bots among bots (2026-11-11)

**Why.** Until here a bot was judged at tables of three stock seats (§19 to §23). The owner's objection, the day §23 was written: the bots are not for beating a table of stock AI. The aim is a pilot that plays its deck as a competent person would; stock opponents do not punish what people punish, a seat can hardly play like a person against them, and a result at their table says little about whether it does. §23 had already found the other half of that: at stock tables the playbook seats aim no more spells at opponents than stock, block no more and die in one swing holding castable cards, and none of it costs them a win. From here on bots are judged among bots.

**The instruments.**
- `league-run` takes a league file and starts from `runner/queue/league-run.json` (it read only the 91-deck list and needed a click). `runner/leagues/bots-v1.json` is the four decks with a shipped playbook as one table, frozen; a fifth bot makes `bots-v2`. With `playbooks` every seat is under its playbook. `league.json` records the league file, so the rollup and `publish.sh` find the list.
- `runner/ab.py --pool FILE --opponent-playbooks` (the `pool` and `opponent_playbooks` fields of `ab-run`): the paired A/B as before, the deck under stock AI and under its playbook on the same tables, with the three opponents drawn from the pool and each under its shipped playbook. The stock arm stays as the control: the same deck in the same seat, without which there is no saying what the rules did.
- `runner/playstyle.py` reads league runs and has `--by-deck`: tempo, placing from first out to winner, kills and damage for each deck.
- A limit met on the way: `playbook_stats` are one static map in `PlaybookController`, summed over every playbook seat of a game, and the rule numbers of different playbooks collide. At a table of bots the counters say nothing about one seat. Not fixed here (it changes `run.json`).

**No human data for this exact table.** The reference has each precon's win rate with its stock list against whatever else sat at the table (§16): nothing head to head, nothing by pod. Playgroup's page for a precon (Tricky Terrain's, read by hand on 2026-11-11) shows the set ranking, the decklist and what people change, and no matchups; four precons from four products of 2022 to 2026 will seldom have met anyway. So the yardstick for this table is derived, each deck's figure rescaled so that the four sum to 100%, which assumes that strength against the field carries over to this pod: Tricky Terrain 29.3%, Token Triumph 27.2%, Hail, Caesar 22.1%, Goblin Storm 21.4%. Beside it stand the table-level figures of people's games (8.75 rounds, the starting player winning 29.2%, a mulligan in 36% of a player's games).

**Results: the four bots at one table (`league-run` #2: `bots-v1` with every seat under its shipped playbook, 50 cycles = 200 games, each deck in every seat 50 times, seed 20261190, the 11-10 build, five shards, 53 minutes; published as `demo-data/runs/2026-11-11-bots-v1-snapshot-2026-11-10-s20261190-bots/`, the dashboard's league view).** Every game was decided.

| Deck | wins of 200 | win rate (95%) | people's share of this table | first out / second / third | opponents killed a game | attackers received per 100 opponent turns |
|---|---|---|---|---|---|---|
| Token Triumph | 92 | 46.0% (39 to 53%) | 27.2% | 39 / 41 / 28 | 1.21 | 89 |
| Tricky Terrain | 44 | 22.0% (17 to 28%) | 29.3% | 47 / 53 / 56 | 0.46 | 53 |
| Goblin Storm | 32 | 16.0% (12 to 22%) | 21.4% | 68 / 58 / 42 | 0.66 | 54 |
| Hail, Caesar | 32 | 16.0% (12 to 22%) | 22.1% | 46 / 48 / 74 | 0.67 | 72 |

The standings are not people's. Token Triumph takes 46% of the games where people's figures give it 27% (chi-square of the four counts against the rescaled shares: 35.7 on 3 degrees of freedom, where 7.8 is the 5% line), and the other three are each five to seven points under theirs. The spread of win rates is 12.4 points against people's 3.3 for these four: wider than the stock league's two and a half times (§18), not narrower. The table does not leave Token Triumph alone to do it. Every bot sends 80 to 89% of its attackers at the highest life, Token Triumph's lifelink Soldiers keep it there, and it receives the most attackers of the four; it also deals the most damage (90 a game) and strikes the last blow in 46 to 53% of each other deck's losses.

The shape of the game is nearer people's than a stock table's and still not theirs. 41.3 game turns (95% 39.9 to 42.6), 10.3 rounds by turns over four and 11.6 by the winner's own turns, where people play 8.75 and the same seats under stock 13.5 (§23; its twenty local games had 9.75); 72 of the 200 games are over within nine rounds. The starting player wins 28.5% (people 29.2%). A seat takes a mulligan in 21.5% of its games (people 36%): the mulligan is Forge's. Kept hands hold 3.05 lands (2.91).

**What the bots hold while they lose.** The same logs, for the cards in these decks that answer a board: the deck's games in which the card was seen in its hand, the games in which it was cast, and its losses with the card in hand at the start of its last own turn.

| Deck (losses) | card | seen | cast | in hand at a loss |
|---|---|---|---|---|
| Hail, Caesar (168) | Ruinous Ultimatum | 36 | 8 | 18 |
| | Martial Coup | 41 | 11 | 21 |
| | Hour of Reckoning | 35 | 10 | 22 |
| | Vault 75: Middle School | 38 | 16 | 18 |
| Token Triumph (108) | Hour of Reckoning | 51 | 8 | 21 |
| | Citywide Bust | 48 | 19 | 11 |
| Tricky Terrain (156) | Oblivion Stone | 68 | 2 | 42 |
| | Curse of the Swine | 57 | 2 | 39 |
| | Summary Dismissal | 51 | 3 | 27 |
| | Beast Within | 38 | 36 | 2 |
| | Pongify | 62 | 45 | 11 |
| | Evacuation | 42 | 36 | 2 |
| Goblin Storm (168) | Blasphemous Act | 30 | 16 | 5 |

One rule in the four playbooks names any of these: Tricky Terrain's "Beast Within or Pongify when an opponent threatens seven or more", and those two are the cards that get cast. The rest are Forge's to decide, and Forge mostly keeps them: Ruinous Ultimatum, which destroys every nonland permanent the opponents have and nothing of ours, was cast in 8 of the 36 games Hail, Caesar saw it; Oblivion Stone and Curse of the Swine, which Forge's AI is told never to cast (§21), in 2 of 68 and 2 of 57, and Tricky Terrain lost 42 and 39 games with them in hand. Against a deck that wins by going wide, these are the cards a person plays.

Correction (the same day, §25): this table counts a cast from any zone, and "seen" includes the games of such a cast. The Tricky Terrain seat's casts of Oblivion Stone, Curse of the Swine and Summary Dismissal (2, 2 and 3) were all from exile, free casts off its library by its own cascade and discover cards. From hand it cast none of the three, in the 66, 55 and 48 games in which it drew them, which is what "told never to cast" means. Hail, Caesar cast Ruinous Ultimatum from hand in 7 of the 35 games it drew it. §25's table counts drawn cards and casts from hand.

**What it says.** (1) Judged among each other the four bots are not yet the four decks people play: one of them wins nearly half the games. (2) The likely reason is the one §23 measured from the other side. A table where nobody answers a board belongs to the deck that builds the widest one with lifelink behind it, and the answers were in hand: this is a reading of the table above, not yet a result, and the test of it is a candidate that casts them, judged at these tables. (3) The proactive half does carry over: a table of bots plays a game three rounds shorter than the same seats under stock and one and a half longer than people's, and the starting player wins as often as people's does. (4) So for the shipped four, "plays its deck as a competent person would" now means the reactive half: what to answer, when, and with which card. It could not be seen at stock tables, where a seat that never answers still wins its share, and it is the first thing these tables show.

Correction (the same day, §26): (1) and the chi-square above lean on "people's share of this table", and the human figures cannot carry that. The four rates are 20.9% (95% 16 to 27), 26.5% (21 to 33), 21.5% (17 to 26) and 28.6% (24 to 34), each against unknown decks that were on average stronger than a precon, and nothing says how these four fare against each other in people's hands. That Token Triumph wins 46% of these games is a fact about this table of bots; that people's table would look different is not known. What stands needs no human figure: three of the seats lose with their answers unplayed.

**The next batch: four candidates at once (2026-11-11).** Counter Intelligence, Food and Fellowship, Planeswalker Party and Deep Clue Sea, chosen from the decks the league under-rates most against people, among those with a large human sample and a plan that plays out on the seat's own turns (§23). One agent a deck worked the loop of §21 on the session's machine at the same time: the audit of twelve stock goldfish games, a hand-written candidate, tuning on the audit seeds, and 40 validation seeds not looked at before the rules were final. A wrapper held the four to two Forge processes at once. From start to the last report took 72 minutes.

| Deck (people; stock in the league) | candidate | goldfish kill turn, stock | candidate | stock − candidate (95%) | faster / same / slower | what stock left undone |
|---|---|---|---|---|---|---|
| Counter Intelligence (16.4%; 7.3%) | `charge`, 32 rules | 13.45 | 11.62 | +1.82 (+1.23 to +2.42) | 29 / 6 / 5 | Inspirit cast on turn 6.4; Coretapper, Steel Overseer and Hangarback Walker never tapped; Cyberdrive Awakener never cast |
| Deep Clue Sea (19.7%; 13.5%) | `sleuth`, 26 rules, 2 trigger rules | 12.57 | 9.70 | +2.88 (+2.24 to +3.51) | 36 / 3 / 1 | Morska on turn 7.0; 32 of 176 Clues cracked and none on its own turn; four cards never cast; Farewell cast on its own board |
| Food and Fellowship (21.0%; 12.5%) | `eat`, 17 rules, trigger rules | 11.38 | 10.30 | +1.07 (+0.67 to +1.48) | 26 / 12 / 2 | 113 Foods made in twelve games and none eaten, so Frodo's attack trigger never fired |
| Planeswalker Party (33.5%; 26.0%) | `guff`, 17 rules, 2 trigger rules | 13.07 | 10.65 | +2.42 (+1.57 to +3.28) | 32 / 4 / 4 | Guff on turn 7.9; four planeswalkers never used; The Chain Veil, Gideon Jura and Oreskos Explorer never cast |

Every game of every arm finished. The mechanical draft of Counter Intelligence on the same validation seeds: 13.40 turns, +0.05 (§22's finding again). Planeswalker Party with the same rules and Forge's own attack: 11.32 (+1.75, 95% +0.89 to +2.61); goldfish flatters that deck, since nobody attacks its planeswalkers. Its file gained one rule after validation games had been seen, a guard against decking through Chandra, Legacy of Fire, which changed none of the 40 games (the kill turns replay one for one). About a turn of Deep Clue Sea's gain is stock casting Farewell on its own board in 12 of the 40 games: on the other 28 the gain is +1.93 (95% +1.42 to +2.44). The files in `playbook/variants/` hold the rules the validation runs played (checked rule for rule against the runs' own records); the pairs are in `demo-data/goldfish/2026-11-11/`.

What the four agents met that the rule format cannot say, which is the list of §22 with new entries: aiming a trigger (Inspirit's own counter each combat never reached the stack in 48 games: Forge's AI has no targeting for it and drops it); a condition on counters, on loyalty or on how many planeswalkers or Clues there are (so a planeswalker's minus ability cannot be timed, and all Clue cracking stops under Mechanized Production); a cap across tokens ("one Food a turn"); a choice made as an effect resolves (which creature a copy copies, the modes of Farewell, who bears the Ring); anything on another player's turn; and an attack that keeps creatures home for planeswalkers. Activate rules do drive loyalty abilities, a planeswalker deck's first need.

**In flight when this was written.** `ab-run` #18: each of the four shipped bots at 200 tables of the other three, its own seat under stock AI and under its playbook, seed 20261200 (does a playbook earn its place when the table is competent). `ab-run` #19: the four candidates above at 200 tables whose opponents are drawn from the four bot decks, stock pilot against candidate, seed 20261210, with Planeswalker Party's Forge-attack sibling on the same tables.

## 25. Human data: what we hold, what exists, and a card-level yardstick (2026-11-11)

**The question.** The owner had understood the human data to be games, turn by turn, and asked whether what we have is any use for making a seat play the way people play.

**What we hold.** One file, `runner/reference/playgroup-commander.json`, copied from Playgroup's public pages on 2026-11-09 (§16, §18): a win rate for each of 92 stock precons (from 40 to 910 games a deck, 28,726 in all, each against whatever else sat at the table), the win rate by seat, how many mulligans people take, how many lands they keep, and the mean and median length of a game in rounds. Aggregates, a few hundred numbers. No game, no turn, no action. Every turn-by-turn log in this project is the sim's own. So the reference can say whether a table of bots produces outcomes like people's (who wins, how long it takes, who goes first), which is how §18 and §24 use it. It cannot say what a person does with a hand, and it has never been able to.

**What exists at Playgroup** (its about page, its cards page, one precon page and thirteen card pages, read by hand on 2026-11-11). A paper game logged in its app records who sat down, which commander each brought, who won and how it ended: results, not actions. Card-level play is recorded only on Playgroup Live, the site's own online table with virtual cards ("what was cast, when it was cast, and which zone a card moved between is recorded only for Playgroup Live seats"; 26,192 Commander games were finished there in October 2026). Those raw events are not published ("the raw game events themselves are not public; the aggregates are what we publish"; no page exposes one player's games; for anything the site does not publish it says to get in touch). The aggregates are published per card, under CC BY 4.0 with a link back to the card's page: how many tracked games brought the card, in how many it was drawn, in how many it was played ("Drawn → Played"), the turn of its first cast with the quartiles, how often it is cast the turn it is drawn, the win rate when it was cast, left in hand or never drawn, and which commanders play it. No public set of Commander games played out turn by turn turned up in a search; none is known to this project.

**A card-level yardstick.** Those per-card figures are the first human data that describe play and not outcomes: whether and when people play a card they have drawn. `runner/cardplay.py` computes the same figures for a seat from the event logs (the games in which a card was in hand or cast from hand, the games in which it was cast, the seat's own turn of the first cast), and `runner/reference/playgroup-cards.json` holds people's for twelve cards, the board wipes and removal of the four shipped bots, read one page a card. Provisional: they were read through a page reader, not transcribed from saved copies, and each is over every deck that runs the card at every kind of table on Playgroup Live, where the sim's figure is one deck at one table. The four bots against each other (`league-run` #2, §24). `cardplay.py` counts a card as drawn when it was in the seat's hand and as played when it was cast from hand; §24's table counted a cast from any zone, so eight of these rows are one to four casts under it. The difference is cards the seat cast from exile without drawing them: Tricky Terrain's Oblivion Stone and Curse of the Swine, looked up in the logs, came off the top of its library through its own cascade (Apex Devastator) and discover (Hidden Cataract).

| Deck | card | who decides in the sim | people: played when drawn (games drawn) | on turn (quartiles) | bot: played when drawn | on turn |
|---|---|---|---|---|---|---|
| Tricky Terrain | Oblivion Stone | Forge, told never to cast it | 72% (109) | 6 (5 to 8) | 0 of 66 | |
| | Summary Dismissal | Forge, never | 64% (55) | 8 (7 to 10) | 0 of 48 | |
| | Curse of the Swine | Forge, never | 58% (607) | 7 (6 to 9) | 0 of 55 | |
| | Pongify | a rule (an opponent threatens seven) | 70% (2,008) | 7 (5 to 8) | 71% (41 of 58) | 7 |
| | Beast Within | the same rule | 63% (5,106) | 7 (6 to 9) | 94% (33 of 35) | 8 |
| | Evacuation | Forge | 47% (289) | 8 (6 to 9) | 84% (32 of 38) | 8 |
| Hail, Caesar | Ruinous Ultimatum | Forge | 55% (699) | 8 (7 to 9) | 20% (7 of 35) | 11 |
| | Martial Coup | Forge | 57% (703) | 8 (7 to 10) | 27% (11 of 41) | 8 |
| | Vault 75: Middle School | Forge | 69% (48) | 8 (6 to 10) | 42% (16 of 38) | 9.5 |
| | Hour of Reckoning | Forge | 47% (451) | 9 (7 to 11) | 26% (9 of 34) | 9 |
| Token Triumph | Hour of Reckoning | Forge | 47% (451) | 9 (7 to 11) | 16% (8 of 51) | 9.5 |
| | Citywide Bust | Forge | 53% (70) | 8 (6 to 10) | 40% (19 of 48) | 9 |
| Goblin Storm | Blasphemous Act | Forge | 56% (6,455) | 7 (6 to 9) | 53% (16 of 30) | 6 |

People play a wipe or a removal spell in about half to seven tenths of the games in which they draw it, on turn 7 to 9. The bots sit on three levels. What Forge is told never to cast is never cast. What Forge decides is cast in 16 to 42% of the games it is drawn, with two exceptions, one on each side: Blasphemous Act, on which Forge is where people are, and Evacuation, which it casts in five games of six. And the one rule in the four playbooks that names an answer gets Pongify played as often as people play it and Beast Within half again as often: a rule can overshoot. Human-like is a rate to hit from both sides, not "always".

**What it says.** (1) The human data we hold is a scoreboard: it can say that a table's results look like people's, not how a person plays, and no amount of it would teach a seat a line. (2) Per-card figures add one thing that is about play: how often and when a card is played once drawn. That is enough to tell a seat that never uses a card people use in two games of three, and a rule that fires where people would wait. It is not sequences, targets, attacks or blocks, and it is per card over all decks, not per deck or per board. (3) Turn-by-turn human play exists only inside Playgroup, for its Live games, unpublished. What a playbook is written from stays what it was: the cards' text, what a person who knows the deck says about it, and the sim's own games, with people's figures as the check afterwards. (4) Twelve cards read by hand are a first look, and they stay that: §26 is why the figures are not collected further. (This point first proposed asking Playgroup for the table. Withdrawn: the owner writes to nobody, for this or anything else; CLAUDE.md carries it as a hard constraint.)

## 26. What the human figures can carry, and what a bot is measured by (2026-11-11)

**Why.** The owner's objection to §25 and to the reports that leaned on Playgroup's numbers: a win rate means little when nothing is known about the games behind it, not even what the deck was playing against, and a sim win rate against stock seats that play precons badly means little either. Checked here against the reference file and against the site's own pages (its legal page, robots.txt, the about page and the precon tier page, read on 2026-11-11).

**What a precon's human win rate is.** The tier page: "Precons are ranked by win rate across games played with the stock, unmodified decklist"; "a deck counts as stock when its non-basic card list exactly matches the precon"; "win rates are normalized to a 4-player baseline (25% expected)"; at least 20 stock games from 10 pilots. It says nothing about the other three decks, and the figures say they were not precons: the 92 precons average 21.0% (20.8% weighted by games) where a field of their own kind would average 25%, and the page itself notes that "most precons land at or below the 25% line". So each figure is how often people won with that exact list against an unknown field that was on average stronger than a precon. Who played, how well and against what is not known.

**How much of the table is noise.** A deck has 40 to 910 games, 224 at the median, so a typical figure is good to about five points either way (95%: 3.5 points at 520 games, 7 at 133). The 92 rates have a standard deviation of 4.3 points; sampling alone gives 3.2; what is left for real differences between decks is 2.8 points, 43% of the variance. By simulation with those sample sizes (2,000 draws): a second table drawn from the same truth agrees with the first at a rank correlation of 0.45 (95% 0.26 to 0.61), and a simulator that knew every deck's true rate would reach 0.66 (0.52 to 0.77). §18 read the stock league's 0.266 against a ceiling of 1; the ceiling is two thirds, and the human table agrees with a copy of itself at under a half. The ends of the table are real (Planeswalker Party 33.5%, 27 to 40; Counter Intelligence 16.4%, 12 to 22); the order of the middle is not. The four shipped decks are two pairs that cannot be told apart within themselves.

**The table-level figures** (seat win rates from 257,261 games, mulligans and kept lands from 189,535 hands, rounds from 1,608,359 games) are over every Commander deck people track, not tables of precons. How often people mulligan and the first seat's edge are about the players and the format; game length depends on what the decks are, so 8.75 rounds is not a figure a table of precons should hit.

**What follows.**
1. The human win rate does not grade a bot. A bot's rate at our tables is against our opponents and people's is against theirs; equal numbers would prove nothing and unequal ones as little. The "People" column beside the bots' results (§22, §23, CLAUDE.md) records how the decks were picked: the ones the stock league put furthest below people. It is not a target, and the dashboard's bots card no longer shows it.
2. §24's "people's share of this table" and its chi-square claimed more than the figures hold (corrected there).
3. What stands from Phase 2 is coarse: stock Forge AI plays some kinds of deck far below their standing among people (the pattern by archetype over many decks, §18), which is the reason to write bots and a way to choose which. Nothing finer.
4. The per-card figures (§25) are the only public human numbers about play. They showed nothing about the unplayed answers that the logs had not shown already, and a rate over every deck that runs a card is a loose guide for one deck. The file stays; it is not extended.
5. The yardstick for "plays its deck as a competent person would" is built from the project's own games:
   - the paired control at tables of bots (§24): the same deck in the same seat under stock AI, which says what the rules are worth against opponents that punish, and means more as the pool of bots grows;
   - mistakes that need no human to define, counted in the logs: a loss with a castable answer in hand (`losses.py`), mana left unspent beside cards it could have paid for and permanents never activated (`hands.py held`, `abilities`), cards drawn and never played (`cardplay.py`); not written yet: lethal on the table not taken, and the unblocked attack that killed the seat with blockers at home;
   - the owner reading games: `hands.py game` prints one seat's game turn by turn, and it is the one human judgement the project has.

**Access and licence, since the owner asked.** Playgroup's legal page says the aggregated, anonymized game statistics and metagame data it produces are published under a Creative Commons Attribution 4.0 licence, to be credited with a link to the page the figure comes from; it forbids visitors nothing by name. Its robots.txt lets crawlers read the statistics pages (it blocks the links that launch playtests, the guest-lobby links and `/brew`). The legal page mentions a public API, not looked at. Individual games are not published. So reading the public pages and using their figures with credit is allowed. "Nothing in the pipeline fetches playgroup.gg" is this project's own caution, from the session that first copied the table, stricter than anything the site asks; it stays as a fact about the pipeline.

**No contact.** The owner, on being told a request to Playgroup was an option: nobody is written to, nothing is posted, nothing is forked, no one is interacted with. §25's suggestion is withdrawn and CLAUDE.md carries the rule.

## 27. The first exams at tables of bots (2026-11-12)

**Why.** §24 moved the exam: a candidate is judged at tables whose three opponents are bots, with the stock pilot of the same deck in the same seat as the control. The first four candidates written for it (§24, the batch of 2026-11-11) had gained one to three turns in goldfish on seeds they had not seen. `ab-run` #19 is their exam: 200 tables each, opponents drawn from the four bot decks under their shipped playbooks, seed 20261210, snapshot 2026-11-10; rollups in `demo-data/ab/2026-11-11-ab-v12/`.

**Results.**

| Deck, candidate | goldfish gain (turns) | stock pilot | candidate | difference (95%), exact test | game length, stock / candidate (turns) |
|---|---|---|---|---|---|
| Counter Intelligence `charge` | +1.82 | 23 of 200 (11.5%) | 20 (10.0%) | -1.5 (-7 to +4), 0.74 | 43.0 / 41.7 |
| Deep Clue Sea `sleuth` | +2.88 | 52 (26.0%) | 61 (30.5%) | +4.5 (-4 to +13), 0.36 | 45.7 / 40.2 |
| Food and Fellowship `eat` | +1.07 | 28 (14.0%) | 29 (14.5%) | +0.5 (-6 to +7), 1.0 | 44.8 / 42.8 |
| Planeswalker Party `guff` | +2.42 | 57 (28.5%) | 57 (28.5%) | 0.0 (-8 to +8), 1.0 | 48.1 / 41.9 |
| Planeswalker Party `guff-forgeattack` (the same rules, Forge's own attack; playbook arm on the same tables, joined) | +1.75 | 57 (28.5%) | 69 (34.5%) | +6.0 (-2 to +14), 0.20; against `guff`: +6.0 (+1 to +11), 21 discordant pairs against 9, 0.043 | 48.1 / 42.6 |

**What it says.** (1) None of the four clearly beats its stock pilot. At stock tables two turns of goldfish speed bought Goblin Storm eleven points (§22); at tables of bots one to three turns bought these four between minus one and a half and plus four and a half, none distinguishable from nothing. A faster engine does not carry a seat at a table that attacks. The games do get shorter under the candidate (by one to six turns), and the seat is out earlier as well as winning earlier. (2) The one clear difference in the run is the attack. Planeswalker Party's rules with Forge's own attack won twelve tables more than the same rules with the go-wide policy, on the same tables (0.043, one comparison chosen in advance for this deck because go-wide cannot keep creatures home for planeswalkers). `go_wide` was chosen at stock tables (§20, §22), where nothing punished an open board. Whether it still earns its place for the other decks is now a question for the same instrument: `ab-run` #23 plays the Forge-attack sibling of every candidate and of the four shipped playbooks on the tables their go-wide versions played. (3) The stock pilots' own rates at these tables are a first look at the decks among bots: Planeswalker Party 28.5% and Deep Clue Sea 26.0% hold their own under stock AI, Food and Fellowship 14.0% and Counter Intelligence 11.5% do not.

**What a bot needs to join the pool** (the owner's plan of 2026-11-12: twelve bots for a rounded meta first, refinement after). Its playbook arm does at least as well as its stock pilot at tables of bots, and its goldfish gain held on unseen seeds; "confirmed" stays reserved for an interval that excludes zero. By that rule Deep Clue Sea and Planeswalker Party (with Forge's attack) are in on a lean, Food and Fellowship is level, Counter Intelligence is three wins short. Nothing is shipped from this run until #23 says which attack each deck keeps.

**The shipped four among bots (`ab-run` #20: each deck at 200 tables whose three opponents are the other three bots under their shipped playbooks, its own seat once under stock AI and once under its shipped playbook; seed 20261200; `demo-data/ab/2026-11-11-ab-v11/`).**

| Deck | stock pilot | shipped playbook | difference (95%), exact test | at three stock seats (§23) |
|---|---|---|---|---|
| Goblin Storm | 11 of 200 (5.5%) | 30 (15.0%) | +9.5 (+4 to +15), 0.0013 | 9.0% against 24.0%, +15.0 |
| Hail, Caesar | 25 (12.5%) | 36 (18.0%) | +5.5 (-1 to +12), 0.13 | 13.5% against 21.0%, +7.5 |
| Token Triumph | 75 (37.5%) | 83 (41.5%) | +4.0 (-4 to +12), 0.42 | 17.5% against 28.0%, +10.5 |
| Tricky Terrain | 32 (16.0%) | 40 (20.0%) | +4.0 (-4 to +12), 0.37 | 15.0% against 24.0%, +9.0 |

Every playbook is still ahead of its stock pilot, by four to nine and a half points where it was seven and a half to fifteen at stock tables, and only Goblin Storm's lead is clear of noise at 200 tables. Summed over the four decks the playbooks win 189 of 800 tables against 143, so the rules are worth something among bots; deck by deck this run cannot say how much. Token Triumph wins 37.5% of these tables under stock AI: its 46% in the bot league (§24) is mostly the deck at this table, not its pilot. The dashboard's bots card now shows these figures (`playbook/bots.json` keeps the stock-table measurement of each deck as `stock_tables`).

**Answer rules for the shipped four (`ab-run` #21: each deck's `answers` candidate, the shipped rules plus rules that cast its wipes and removal, playbook arm on #20's 200 tables; joined with #20's arms; `demo-data/ab/2026-11-12-ab-v13/`).** The candidates were written from the 200 league games of §24, one agent a deck, and tried at 20 to 39 local bot tables.

| Deck | stock pilot | shipped | answers | answers against shipped (95%), discordant pairs, exact test |
|---|---|---|---|---|
| Hail, Caesar | 25 | 36 | 55 (27.5%) | +9.5 (+5 to +14), 23 against 4, 0.0003 |
| Goblin Storm | 11 | 30 | 38 (19.0%) | +4.0 (+1 to +7), 10 against 2, 0.039 |
| Tricky Terrain | 32 | 40 | 44 (22.0%) | +2.0 (-3 to +7), 17 against 13, 0.58 |
| Token Triumph | 75 | 83 | 80 (40.0%) | -1.5 (-6 to +3), 8 against 11, 0.65 |

Hail, Caesar's answer rules are the largest effect measured at tables of bots so far: nineteen tables more than the shipped version on the same 200, and thirty more than the stock pilot (+15.0 points, +8 to +22). Its agent's thirty local tables had said the casts bought turns and no wins; 200 tables say otherwise, which is §22's lesson about local tables again. Goblin Storm's gained eight tables (0.039, one of four comparisons, so read it as a gain at the edge of noise); its agent had expected little. Tricky Terrain's and Token Triumph's did nothing measurable. Hail, Caesar's and Goblin Storm's candidates became version 4 of their shipped playbooks on 2026-11-12. Tricky Terrain's waits for its games to be read (does the seat still lose with its answers in hand); Token Triumph's is not shipped. The per-game logs of this run were not read for this paragraph: what the rules cast and what the seats still held is the next thing to look at.

A consequence for later runs: from the commit that shipped them, the pool's Hail, Caesar and Goblin Storm play version 4. An arm played before and an arm played after are not on the same tables even with the same seed, and `runner/ab.py join` does not know it.

**Quick Draw and Science! (`ab-run` #22: 200 tables of bots each, stock pilot against candidate, seed 20261220; `demo-data/ab/2026-11-12-ab-v14/`).** Quick Draw `spells` 39 wins against 32 (+3.5 points, 95% -3 to +10, exact test 0.40), the same lean it had at stock tables (§22: 38 against 31). Science! `lab` 4 against 7 (-1.5, -4 to +1): the deck wins two to four tables in a hundred here under either pilot.

**What the answer rules cast (the 800 games of `ab-run` #21, read on 2026-11-12; beside them the 200 league games of §24 and §25, the same pool under the shipped playbooks, on other tables).** Games in which the card was drawn, games in which it was cast from hand, and losses with it in hand at the seat's last own turn.

| Deck | card | shipped bots, the league: cast of drawn | answer rules, #21: cast of drawn | in hand at a loss: league, then #21 |
|---|---|---|---|---|
| Hail, Caesar | Ruinous Ultimatum | 7 of 35 (20%) | 28 of 41 (68%) | 18 of 168 losses, 12 of 145 |
| | Martial Coup | 11 of 41 (27%) | 20 of 32 (62%) | 21, 11 |
| | Hour of Reckoning | 9 of 34 (26%) | 23 of 36 (64%) | 22, 10 |
| | Vault 75: Middle School | 16 of 38 (42%) | 31 of 45 (69%) | 18, 10 |
| | The Nipton Lottery | 8 of 33 (24%) | 30 of 39 (77%) | 20, 6 |
| Token Triumph | Hour of Reckoning | 8 of 51 (16%) | 32 of 43 (74%) | 21 of 108, 8 of 120 |
| | Conclave Tribunal | 26 of 51 (51%) | 53 of 56 (95%) | 12, 4 |
| | Citywide Bust (no rule) | 19 of 48 (40%) | 18 of 49 (37%) | 11, 18 |
| Tricky Terrain | Oblivion Stone | 0 of 66 | 46 of 46 | 42 of 156, 1 of 156 |
| | Propaganda | 40 of 45 (89%) | 52 of 52 | 5, 0 |
| | Evacuation (held for a wide board) | 32 of 38 (84%) | 34 of 47 (72%) | 2, 10 |
| | Curse of the Swine, Summary Dismissal (no rule) | 0 of 55, 0 of 48 | 0 of 57, 0 of 51 | 39 and 27, 39 and 32 |
| Goblin Storm | Blasphemous Act | 16 of 30 (53%) | 24 of 32 (75%) | 5 of 168, 1 of 162 |
| | Goblin Bombardment | 0 of 51 | 42 of 44 | 32, 3 |
| | Grapeshot | 2 of 49 (4%) | 7 of 59 (12%) | 36, 43 |

The rules do what they were written to do: a wipe that was cast in a fifth to two fifths of the games it was drawn is cast in three fifths to three quarters, and the cards Forge never cast are on the table. What that is worth depends on the seat. It carried Hail, Caesar (+9.5 points) and helped Goblin Storm (+4.0); it did nothing for Token Triumph, which casts Hour of Reckoning four and a half times as often and wins as before: the deck that leads this table gains nothing from clearing it. For Tricky Terrain the lean is small (+2.0), but the seat no longer loses with Oblivion Stone in hand, and its candidate was shipped as version 6 on that and on not losing tables: a lean in wins, a clear change in what the games show. Still in hand at the losses: Grapeshot (the rule asks for a storm count the seat seldom reaches), Curse of the Swine and Summary Dismissal (no rule can drive them: X and targets are Forge's, and a counterspell needs another player's turn), Citywide Bust.

