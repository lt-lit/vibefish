# Vibefish — Design Doc v0.1

*Commander deck playtesting for Magic: The Gathering, built on Forge's headless sim mode.*

Status: pre-prototype. Companion project to VibeTutor.

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
├── forge/                     pinned Forge release jar + launcher scripts
├── runner/                    sim orchestration (bash/python): decks in, JSON out
├── controller/                Java: PlaybookController extends Forge AI controller
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

**Runner.** Wraps `forge.sh sim`. Takes a manifest (which decks, how many games, which opponents, which playbooks), runs Forge headless, captures output, writes structured JSON per game and a rollup per run. Also enforces a turn cap and wall-clock timeout per game (AI-vs-AI Commander can stall).

**Forge fork / patch.** Forge's log output is unstructured text. Decision: fork Forge (GPL permits), add a `JsonGameLogger` that emits one JSON line per game event (zone changes, spells cast, combat, life totals, mulligans, game end). Also expose RNG seed as a CLI flag for reproducible replays. Keep the patch small and rebase on monthly Forge releases.

**PlaybookController.** Java class extending Forge's AI `PlayerController`. On each decision point:
1. Check playbook for a matching rule → execute it.
2. Else fall through to stock Forge AI.
Phase 1 handles mulligans, card priority, and hold/cast rules. Phase 2 adds scripted combo lines. Phase 3 optionally calls Forge's experimental simulation AI for targeting and combat only.

**Playbook.** JSON, one per deck. Human-readable, LLM-writable. See §5.

**Scryfall resolver.** Workflow step: for every unique card name in decks + results, resolve once via `api.scryfall.com/cards/named?exact=` (≥100 ms between calls, proper User-Agent), cache `scryfall_id` and `image_uris` in the data repo. Dashboard hotlinks `cards.scryfall.io` — no image files in git.

**Dashboard.** Vanilla JS, no build step, GitHub Pages. Reads JSON over `raw.githubusercontent.com` (or local path). Views: deck overview, run history, matchup grid, per-game timeline, board-state viewer, "cards that never got cast" list, playbook diff.

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

Win rates are meaningless without a fixed opponent pool. Define a standard pod of three Forge-bundled precons spanning power levels, and always report results against that pod. Add "mirror pods" (your decks vs. each other) as a secondary view.

### 4.2 Sample size

Four-player games have a 25% baseline. Expect to need ~200+ games per deck for win-rate signal; consistency stats (land drops, commander turn) stabilize much faster (~50 games).

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

Conditions use a tiny expression language evaluated against a flat game-state view. Keep it boring and greppable.

## 6. Results schema (sketch)

Per game: `{ seed, decks[], winner, turns, events[] }` where events are `{ turn, phase, player, type, card?, targets?, life? }`.

Per run rollup, per deck: games, wins, avg turn commander first cast, land-drop rate by turn, mulligan rate, cards never cast, avg turn of death, cause of death (combat/commander damage/combo/poison/decking).

## 7. Roadmap

| Phase | Deliverable | Done when |
|---|---|---|
| 0 Spike | Forge runs 4-player Commander sim headless on a local machine and in Actions | A precon pod completes 10 games with no crashes |
| 1 Goldfish | Runner + JSON logger + rollup + first dashboard | Consistency stats for one deck visible on Pages with card images |
| 2 Pilot | PlaybookController v1 (mulligan, priority, hold) | Measurable improvement vs. stock AI on same deck/pod |
| 3 Lines | Scripted combo execution + LLM post-mortem loop | Playbook v2 generated from v1 losses beats v1 |
| 4 Lookahead | Forge simulation AI for targeting/combat only | Net positive on benchmark pod |
| 5 Eval model | Small learned board evaluator trained on sim data | Stretch |

Phase 0 and 1 are the prototype. Nothing in Phase 2+ starts until Phase 1 runs end-to-end.

## 8. Decisions made

- **Engine:** Forge. Headless sim mode, Commander format flag, multiplayer tournament mode, GPL, near-complete card coverage.
- **Repos:** engine and data split, both public.
- **Images:** Scryfall hotlinks only. No image files in any repo.
- **Dashboard stack:** vanilla JS, no build tools, GitHub Pages.
- **Compute:** local via Claude Code for iteration; GitHub Actions for batch runs. No dedicated server.
- **Forge integration:** fork + small patch (JSON logger, seed flag) rather than log scraping.
- **Name:** Vibefish. "MTG"/"Magic" stay out of the name and appear only descriptively.

## 9. Risks

- **Multiplayer sim stability.** Forge's wiki flags non-constructed formats as possibly not working in sim mode. Phase 0 exists to find out.
- **Forge release churn.** Monthly releases change card scripts and occasionally AI internals. Pin a release; rebase the patch deliberately.
- **`.dck` conversion edge cases.** Split/MDFC/adventure cards, set-specific names. Validate every deck against Forge's card database before running.
- **RemAIDeck cards.** Forge marks some cards AI-unplayable. Detect and report them per deck up front — the pilot will never cast them.
- **Stalled games.** Draw-go forever. Hard turn cap (e.g., 30) plus wall-clock timeout; record as a draw.
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

**How Forge ships:** a tagged release per major set, named after the set (`forge-2.0.13` "Marvel Super Heroes", etc.), roughly every 1–2 months, plus a rolling `daily-snapshots` pre-release on the same GitHub Releases page rebuilt every day. New-set card scripts land in snapshots during spoiler season, well before the tagged release.

**Vibefish update cycle (automated, Claude Code does the merge):**

1. **Watch.** A weekly scheduled Actions job hits `https://api.github.com/repos/Card-Forge/forge/releases/latest`. New tag → open a PR bumping `forge/VERSION`.
2. **Rebase.** CI applies `forge/patches/*.patch` (JSON logger, seed flag) to the new tag and builds. Patch is small and touches stable classes, so it usually applies clean; if not, the PR fails and Claude Code fixes the conflict.
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

- Does Forge's tournament mode seat 4 players in one game, or pair them 1v1? Verify in Phase 0.
- Can the Forge AI be given a per-player profile in sim mode, or is it global? Affects whether PlaybookController is needed for Phase 2 basics.
- How much of game state does Forge expose cleanly for the post-mortem serializer?
- Playbook expression language: hand-roll or embed a tiny existing evaluator?
