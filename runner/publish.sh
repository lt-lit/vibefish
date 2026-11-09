#!/usr/bin/env bash
# Publishes a finished run into a data directory the dashboard reads:
#   runner/publish.sh RESULTS/RUN_ID DATA_DIR
# Pod run: copies each shard's run.json, gzips the event logs, writes DATA_DIR/runs/RUN_ID/rollup.json.
# League run (league.json present): writes rollup.json and league.json only (see below).
# Both: scorecard.json, upsert of DATA_DIR/index.json, new card names resolved into DATA_DIR/cards/scryfall-cache.json.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
SRC=${1:?results/RUN_ID}
DATA=${2:?data dir, e.g. demo-data}
RUN_ID=$(basename "$(cd "$SRC" && pwd)")
DEST="$DATA/runs/$RUN_ID"
mkdir -p "$DEST" "$DATA/cards"
shopt -s nullglob
if [ -f "$SRC/league.json" ]; then
  # A league run (runner/league.py): thousands of one-game harness directories. The published form is the rollup
  # (per-deck statistics plus every game's seats, seed, first seat, winner and length), the scorecard and the
  # league.json that fixes the schedule; the per-game run.json and event streams stay in results/ (and in the
  # workflow's artifacts), since any game can be replayed from its seed and seats on the same Forge build.
  cp "$SRC/league.json" "$DEST/league.json"
  python3 -I "$HERE/league.py" rollup "$SRC" --out "$DEST" --run-id "$RUN_ID" --index "$DATA/index.json"
else
  shards=("$SRC"/shard-*/)
  [ ${#shards[@]} -gt 0 ] || { echo "no shard-* directories in $SRC" >&2; exit 1; }
  for shard in "${shards[@]}"; do
    name=$(basename "$shard")
    mkdir -p "$DEST/$name/games"
    cp "$shard/run.json" "$DEST/$name/run.json"
    for ev in "$shard"/games/*.events.jsonl; do
      gzip -9 -c "$ev" > "$DEST/$name/games/$(basename "$ev").gz"
    done
  done
  python3 -I "$HERE/rollup.py" "${shards[@]}" --out "$DEST" --run-id "$RUN_ID" --pod "$HERE/benchmark-pod.json" --index "$DATA/index.json"
fi
python3 -I "$HERE/scorecard.py" "$DEST/rollup.json" --out "$DEST/scorecard.json"
python3 -I "$HERE/scryfall.py" --cache "$DATA/cards/scryfall-cache.json" --from "$DEST/rollup.json"
echo "published $RUN_ID -> $DEST ($(du -sh "$DEST" | cut -f1))" >&2
