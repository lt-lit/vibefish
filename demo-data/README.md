# demo-data

Published benchmark-pod results that the dashboard reads. Written by `runner/publish.sh`; never edit by hand.

```
index.json                      list of runs: id, generated, forge_version, pod, games, path to its rollup
cards/scryfall-cache.json       card name → Scryfall id, set, collector number, scryfall_uri, image URLs (small, normal)
runs/<run-id>/rollup.json       per-deck statistics and per-game summaries (schema in DESIGN.md §6)
runs/<run-id>/shard-N/run.json  the harness's own summary for that shard
runs/<run-id>/shard-N/games/    one gzipped JSONL event stream per game
```

Images are never stored here; the dashboard hotlinks `cards.scryfall.io` URLs from the cache.
