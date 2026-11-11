# demo-data

Published benchmark-pod results that the dashboard reads. Written by `runner/publish.sh`; never edit by hand.

```
index.json                      list of runs: id, generated, forge_version, pod, kind ("league" for league runs), games, path to its rollup
cards/scryfall-cache.json       card name → Scryfall id, set, collector number, scryfall_uri, image URLs (small, normal)
runs/<run-id>/rollup.json       per-deck statistics and per-game summaries (schema in DESIGN.md §6)
runs/<run-id>/scorecard.json    calibration against Playgroup.gg's human references (runner/scorecard.py)
runs/<run-id>/shard-N/run.json  pod runs: the harness's own summary for that shard
runs/<run-id>/shard-N/games/    pod runs: one gzipped JSONL event stream per game
runs/<run-id>/league.json       league runs: seed, cycles, shards, runtime, deck ids and the league file; the schedule and every game's
                                seats and seed are in the rollup, the per-game data stays in the run's workflow artifacts
```

Images are never stored here; the dashboard hotlinks `cards.scryfall.io` URLs from the cache.

League runs so far: `2026-11-09-league-v1-...`, the 91 precons under stock AI (DESIGN.md §18), and
`2026-11-11-bots-v1-...-bots`, the four decks that have a shipped playbook as one table with every seat under its
playbook (`runner/leagues/bots-v1.json`, DESIGN.md §24).
