# Vibefish — Claude Code context

Read `DESIGN.md` first. This file is the short version plus hard constraints.

## What this repo is
Commander deck playtesting engine built on Forge's headless `sim` mode. Engine only — decks, playbooks and results live in a separate data repo and are passed in by path.

## Hard constraints
- **Dashboard:** vanilla JS, no build step, no TypeScript, no frameworks. Must work on GitHub Pages and on a phone browser.
- **Images:** never commit card image files. Hotlink `cards.scryfall.io` URLs from the cache only.
- **Scryfall API:** ≥100 ms between requests to `api.scryfall.com`; set `User-Agent: Vibefish/<version>` in scripts; leave browser UA alone in page JS. Never crop/alter images.
- **Forge:** pinned to the tag in `forge/VERSION`. Do not float to `latest` or `daily-snapshots` unless `FORGE_CHANNEL=snapshot` is explicitly set.
- **License:** this repo is GPL v3 because `controller/` compiles against Forge. Don't vendor non-GPL-compatible code.
- **Naming:** project is "Vibefish". "MTG" / "Magic: The Gathering" appear only descriptively, never in the product name, repo name, or logos.
- **Benchmark pod** in `runner/benchmark-pod.json` is frozen. Do not edit it.

## Forge sim mode cheat sheet
```
./forge.sh sim -f Commander -d deck1.dck deck2.dck deck3.dck deck4.dck -n 10
./forge.sh sim -f Commander -D /decks/ -t RoundRobin -p 4 -n 10 -q
```
Flags: `-f` format, `-d` deck list, `-D` deck folder, `-n` games, `-m` matches, `-t` tournament type, `-p` players per game, `-q` quiet. Output goes to stdout and `forge.log` unless patched. Verify multiplayer actually seats 4 in one game — this is unconfirmed (Phase 0).

Forge needs Java 17+. Sim mode does not need card images.

## Key links
- Forge AI / sim flags: https://github.com/Card-Forge/forge/wiki/AI
- Forge releases: https://github.com/Card-Forge/forge/releases
- Forge card scripting (AILogic, RemAIDeck): https://github.com/Card-Forge/forge/wiki/Card-scripting-API
- Forge release/snapshot process: https://github.com/Card-Forge/forge/wiki/Snapshots-and-Releases
- Scryfall API: https://scryfall.com/docs/api
- WotC Fan Content Policy: https://company.wizards.com/en/legal/fancontentpolicy

## Phase 0 checklist (do this before anything else)
1. Download the pinned Forge release, run a 2-player constructed sim, confirm it completes.
2. Run a 4-deck Commander sim with bundled precons. Confirm 4 players are in one game, not paired 1v1.
3. Note what the log output looks like — this informs the `JsonGameLogger` patch.
4. Time 10 games. Record avg seconds/game in `DESIGN.md` §4.2.
5. Try the same in a GitHub Actions workflow on `ubuntu-latest`.

Nothing in Phase 1+ starts until all five pass.

## Required README footer
> Vibefish is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
