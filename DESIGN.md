# Vibefish — Design Doc v0.2

*Commander deck playtesting for Magic: The Gathering, built on Forge's headless sim mode.*

Status: Phase 0 complete (2026-11-08); Phase 1 next. Companion project to VibeTutor. What changed from v0.1 is listed at the end of §14.

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
├── forge/                     version pin + checksum, fetch and launch scripts (runtime downloaded, never committed)
├── runner/                    sim orchestration (bash/python): decks in, JSON out; frozen benchmark pod
├── controller/                Java compiled against the released Forge jar: sim harness
│                              (JSON event logger, per-game seeds, turn cap) + PlaybookController
├── playbook/                  playbook schema + validator + examples
├── dashboard/                 vanilla JS static site (GitHub Pages)
├── demo-data/                 results for WotC precons (seed data for public dashboard)
├── .github/workflows/         reusable sim workflow
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

**Runner.** Wraps the Forge launcher (Phase 0) and later the harness (Phase 1). Takes a manifest (which decks, how many games, which opponents, which playbooks), runs Forge headless, captures output, writes structured JSON per game and a rollup per run. Always sets Forge's clock (`-c`, we use 900 s; Forge's own default of 120 s declares longer Commander games a draw) and, from Phase 1, a turn cap. Game counts are multiples of four so the pod rotation in §4.1 stays balanced.

**Forge integration (no fork).** Forge is consumed as a library. The released desktop jar goes on the classpath and `controller/` provides its own entry point that repeats sim mode's ~100 lines of setup (`FModel.initialize`, `RegisteredPlayer.forCommander`, `Match`, `Game`) and then does what sim mode cannot:
- subscribes a `JsonGameLogger` to the game's public event bus (`Game.subscribeToEvents`). Events are Java records carrying the data we need: zone changes with from/to zone, casts with host card and targets, turn began with number and owner, life changes, mulligans, land drops, attackers declared, game outcome with each player's `GameLossReason`;
- seeds `MyRandom` per game and records the seed;
- enforces a turn cap next to Forge's wall-clock cap;
- streams JSONL while the game runs, so a killed job still yields partial data.

Sim mode in 2.0.15 already has an RNG seed (`-s`), per-seat AI profiles (`-a`) and a clock (`-c`), so nothing is patched. If a needed hook ever turns out to be private, the fallback is a build-time patch, declared here. Phase 0 drives Forge through its stock `sim` entry point; the harness arrives in Phase 1.

**PlaybookController.** Java class extending Forge's `PlayerControllerAi`, created by our own `LobbyPlayer` so Forge itself is untouched. On each decision point:
1. Check playbook for a matching rule → execute it.
2. Else fall through to stock Forge AI.

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

Two uses. **Baseline:** the four play each other; expected win share is 25% each and the measured spread is the pod's own power calibration. **Deck under test:** the tested deck takes a seat and the precons rotate out one at a time, so each precon sits out exactly a quarter of the games. Seat order rotates every game. Game counts are therefore multiples of four. "Mirror pods" (your decks vs. each other) stay a secondary view. If the pod ever changes, that is a new pod with a new name and history restarts.

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

## 6. Results schema (sketch)

Per game: `{ forge_version, pod, seed, seat_order[], decks[], winner, turns, end_reason, players[{deck, seat, loss_reason, life_at_end, turn_eliminated}], events[] }` where events are `{ turn, phase, player, type, card?, from?, to?, targets?, life? }`. `loss_reason` is Forge's `GameLossReason` (`LifeReachedZero`, `CommanderDamage`, `Poisoned`, `Milled`, `SpellEffect`, `Conceded`, `OpponentWon`) plus harness values `TurnCap` and `Timeout`.

Per run rollup, per deck: games, wins, avg turn commander first cast, land-drop rate by turn, mulligan rate, cards never cast, avg turn of death, cause of death (combat/commander damage/combo/poison/decking).

## 7. Roadmap

| Phase | Deliverable | Done when |
|---|---|---|
| 0 Spike | Forge runs 4-player Commander sim headless on a local machine and in Actions | **Done 2026-11-08** (§14): 11/11 local games completed; first Actions run pending |
| 1 Goldfish | Harness (JSON event logger, seeds, turn cap) + runner + rollup + first dashboard | Consistency stats for one deck visible on Pages with card images |
| 2 Pilot | Per-deck AI profile, then PlaybookController v1 (mulligan, priority, hold) | Measurable improvement vs. the Default profile on same deck/pod |
| 3 Lines | Scripted combo execution + LLM post-mortem loop | Playbook v2 generated from v1 losses beats v1 |
| 4 Lookahead | Evaluate Forge's flat Monte Carlo AI (upstream, expected in the release after 2.0.15) on the pod; else targeted lookahead for combat/targeting | Net positive on benchmark pod |
| 5 Eval model | Small learned board evaluator trained on sim data | Stretch |

Phase 0 and 1 are the prototype. Nothing in Phase 2+ starts until Phase 1 runs end-to-end.

## 8. Decisions made

- **Engine:** Forge. Headless sim mode, Commander format flag, plain multi-deck mode for 4-player pods, GPL, near-complete card coverage.
- **Forge integration:** library-style harness compiled against the released jar; **no fork, no patches.** Decided after reading sim mode's source: the seed and per-seat profile flags exist, and the event bus gives structured data.
- **Forge version:** pinned to `forge-2.0.15` (checksum in `forge/SHA256SUMS`) for Phases 0–1. The next bump is the first exercise of the upgrade pipeline (§11).
- **Pilot strategy:** AI profiles first, PlaybookController for what profiles cannot express, upstream lookahead evaluated before building our own.
- **Benchmark pod:** the four precons in §4.1, frozen.
- **Build tooling:** plain `javac` against the release jar, driven by a shell script. Maven only if the Java grows.
- **Repos:** engine and data split, both public.
- **Images:** Scryfall hotlinks only. No image files in any repo.
- **Dashboard stack:** vanilla JS, no build tools, GitHub Pages.
- **Compute:** local via Claude Code for iteration; GitHub Actions for batch runs. No dedicated server.
- **Replays:** from the recorded event stream. Seeds are for reproducing a single game while debugging.
- **Name:** Vibefish. "MTG"/"Magic" stay out of the name and appear only descriptively.

## 9. Risks

- **Multiplayer sim stability.** *Resolved in Phase 0:* plain mode with four decks seats all four in one Commander game. Tournament mode (`-t`/`-p`) pairs decks 1v1 at 20 life and ignores the deck folder for named decks; never use it for Commander.
- **Forge's default clock.** `-c` defaults to 120 s and declares the game a draw; 3 of 11 Phase 0 games ran longer. The runner always sets it. Forge has no turn cap; the harness adds one.
- **Ordering nondeterminism.** The same seed replays the same game, but the listing order of simultaneous events (declared attackers, their blocks) varies between runs. Diffs and regression comparisons must be order-insensitive; the recorded log is the replay source.
- **Upstream AI churn.** Forge master (Oct–Nov 2026) added flat Monte Carlo, deck-plan detection, combo recognition and plan-aware mulligans. The first bump after 2.0.15 will move every baseline. Never average across `forge_version` (§11 step 4).
- **Forge release churn.** Monthly releases change card scripts and occasionally AI internals. Pin a release; bump deliberately.
- **`.dck` conversion edge cases.** Split/MDFC/adventure cards, set-specific names. The converter emits bare card names (Forge's pinned form is `Name|SET|artIndex`, not collector number); validate every deck with Forge's own conformance check and card database before running.
- **RemAIDeck cards.** Forge marks some cards AI-unplayable (`AI:RemoveDeck:All`, ~7% of scripts). Read the flags off Forge's card rules and report them per deck up front — the pilot will never cast them.
- **Stalled games.** Draw-go forever. Hard turn cap (e.g., 30 turn cycles) plus wall-clock timeout; record as a draw.
- **Signal vs. noise.** Stock AI misplays dominate win rates in Phase 1. Lean on consistency stats until Phase 2 improves the pilot.
- **Scryfall rate limits.** Resolve in the workflow, cache aggressively, never hammer from the browser.

## 10. Licensing and attribution

- Engine repo: GPL v3 (required — PlaybookController compiles against Forge).
- Playbooks and decks: data, licensed separately (CC0 or MIT in data repo).
- README footer: *"Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC."*
- Scryfall attribution per https://scryfall.com/docs/api. Never crop copyright/artist lines, never alter images.
- Forge: https://github.com/Card-Forge/forge — credit in README.

## 11. Keeping up with new sets

Forge does the hard part (scripting every new card). Vibefish's job is to track Forge without breaking.

**How Forge ships:** a tagged release per major set, named after the set (`forge-2.0.13` "Marvel Super Heroes", `forge-2.0.15` "Reality Fracture", etc.), roughly every 1–2 months, plus a rolling `daily-snapshots` pre-release on the same GitHub Releases page rebuilt every day. New-set card scripts land in snapshots during spoiler season, well before the tagged release. The release asset is a single `forge-installer-<version>.tar.bz2` (~283 MB) with no top-level directory; the snapshot asset carries a build date in its name and must be discovered through the releases API.

**Vibefish update cycle (automated, Claude Code does the merge):**

1. **Watch.** A weekly scheduled Actions job hits `https://api.github.com/repos/Card-Forge/forge/releases/latest`. New tag → open a PR bumping `forge/VERSION` and `forge/SHA256SUMS`.
2. **Rebuild.** CI downloads the new release, verifies the checksum, and recompiles `controller/` against the new jar. Compile errors are the only "conflicts" now; Claude Code fixes them in the PR.
3. **Regress.** CI runs the frozen benchmark pod for 50 games on the new build and diffs rollup stats against the previous version. Forge AI changes shift baselines — a big swing means "investigate," not "ship."
4. **Stamp.** Every result file carries `forge_version`. The dashboard segments history by it so pre- and post-upgrade numbers never get averaged together.
5. **Merge.** PR merges, data repo picks up the new engine on its next run.

**Deck-side:** the runner validates every `.dck` against the pinned Forge card database before running. Cards Forge doesn't know yet fail fast with a list. For spoiler-season testing, a `FORGE_CHANNEL=snapshot` flag swaps in the daily snapshot instead of the pinned tag (results get stamped `snapshot-YYYY-MM-DD` and excluded from long-term history by default).

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
- How much of game state does Forge expose cleanly for the post-mortem serializer? **Mostly answered:** the event bus plus direct reads of `Game`/`Player` in the harness. Still open: whether to log hidden information (hands) per turn for post-mortems.
- Playbook expression language: hand-roll, embed a tiny evaluator, or reuse Forge's `Valid`/`Count$` card-script syntax. Decide in Phase 2.
- Pod rotation rule (§4.1, "each precon sits out a quarter of the games"): confirm before Phase 1 results accumulate.
- ~~Squirreled Away: play it as shipped (Hazel of the Rootbloom) or swap the commander to Chatterfang?~~ **Answered:** as shipped, Hazel in the command zone. Chatterfang is the product's alternate commander and stays in the 99.

## 14. Phase 0 results (2026-11-08)

Forge 2.0.15 (release of 28 Sep 2026), Java 21, 4-core / 15 GB container. Scripts: `forge/fetch-forge.sh`, `runner/pod-smoke.sh`.

| Check | Result |
|---|---|
| 2-player constructed sim (two quest precons) | 2 games, 5 s and 11 s |
| 4-deck Commander sim, plain mode | 11 games, all completed; 40 life, commander-damage kills, winner by last standing, no exceptions |
| Tournament mode `-t RoundRobin -p 4 -f Commander` | pairs 1v1 at 20 life; not usable for Commander |
| Seeded determinism | same seed → same 55-turn game and winner; 14 of 3,782 log lines differ, all attacker/blocker listing order |
| Time per 4-player game | avg 98 s over 10, median 66 s, min 44 s, max 247 s; plus ~11 s startup per process |
| Games over Forge's 120 s default clock | 3 of 11 (would have been draws) |
| Download / extract | 283 MB tarball, 13 s download, 30 s extract; trimmed runtime ~190 MB |
| GitHub Actions run | pending first green run of `.github/workflows/phase0.yml` |

Log shape (stock text log, one game ≈ 3,800 lines): `Phase` (~37%), `Mana`, `Add To Stack` / `Resolve Stack`, `Zone Change` (graveyard/exile moves only), `Turn`, `Damage`, `Combat`, `Life`, `Land`, `Mulligan`, `Game Outcome`. Missing: draws, hand contents, the zone a spell was cast from. This is why Phase 1 logs from the event bus instead of parsing text.

Changes from v0.1: dropped the Forge fork/patch (§3.1, §8, §11); four-precon pod with rotation rule (§4.1); measured costs (§4.2); profiles-first pilot and upstream-lookahead evaluation (§3.1, §7); new risks and resolved questions (§9, §13); results schema gains `forge_version`, `seed`, `loss_reason` (§6).
