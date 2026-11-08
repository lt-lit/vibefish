#!/usr/bin/env bash
# Plays the benchmark pod through the Vibefish harness, in parallel shards, then rolls the results up.
#
#   runner/run-pod.sh [-n GAMES] [-j SHARDS] [-s SEED] [-c CLOCK_S] [-t TURN_CAP] [-o RESULTS_DIR] [-i RUN_ID] [-x INDEX_JSON] [-k SHARD]
#
# -k K runs only shard K of the J shards (for one CI job per shard) and skips the rollup.
#
# Output: RESULTS_DIR/RUN_ID/{shard-N/run.json, shard-N/games/*.events.jsonl, shard-N.log, rollup.json}
# Each shard is one JVM (about 4 GB heap, ~1.5 cores while a game runs); keep SHARDS <= cores/1.5.
# A shard that hits the wall clock exits and is resumed from the next game automatically.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
POD="$HERE/benchmark-pod.json"

GAMES=4; SHARDS=1; SEED=$(date -u +%Y%m%d); CLOCK=900; CAP=120; RESULTS="$ROOT/results"; RUN_ID=""; INDEX=""; ONLY=""
while getopts "n:j:s:c:t:o:i:x:k:" opt; do
  case $opt in
    n) GAMES=$OPTARG ;;
    j) SHARDS=$OPTARG ;;
    s) SEED=$OPTARG ;;
    c) CLOCK=$OPTARG ;;
    t) CAP=$OPTARG ;;
    o) RESULTS=$OPTARG ;;
    i) RUN_ID=$OPTARG ;;
    x) INDEX=$OPTARG ;;
    k) ONLY=$OPTARG ;;
    *) echo "usage: $0 [-n GAMES] [-j SHARDS] [-s SEED] [-c CLOCK_S] [-t TURN_CAP] [-o RESULTS_DIR] [-i RUN_ID] [-x INDEX_JSON] [-k SHARD]" >&2; exit 2 ;;
  esac
done
[ -f "$RUNTIME/VIBEFISH_FORGE_VERSION" ] || { echo "No Forge runtime at $RUNTIME; run forge/fetch-forge.sh" >&2; exit 2; }
[ "$SHARDS" -ge 1 ] && [ "$GAMES" -ge 1 ] || { echo "GAMES and SHARDS must be >= 1" >&2; exit 2; }
[ "$SHARDS" -le "$GAMES" ] || SHARDS=$GAMES

FORGE_VERSION=$(head -1 "$RUNTIME/VIBEFISH_FORGE_VERSION")
POD_NAME=$(jq -r .name "$POD")
PRECONS="$RUNTIME/$(jq -r .precon_dir "$POD")"
DECK_ARGS=()
while IFS= read -r spec; do DECK_ARGS+=(--deck "$spec"); done < <(jq -r '.seats[] | "\(.id)=\(.file)"' "$POD")
[ -n "$RUN_ID" ] || RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${POD_NAME}-${FORGE_VERSION}-s${SEED}"
OUT="$RESULTS/$RUN_ID"
mkdir -p "$OUT"

"$ROOT/controller/build.sh" >&2
echo "run $RUN_ID: $GAMES game(s) in $SHARDS shard(s), seed $SEED, clock ${CLOCK}s, turn cap $CAP, $(nproc) cpus" >&2
echo "output: $OUT" >&2

run_shard() {
  local j=$1 n=$2
  local seed=$((SEED + j * 100000))
  local dir="$OUT/shard-$j" log="$OUT/shard-$j.log"
  local start=1 attempts=0 rc=0
  while :; do
    set +e
    "$ROOT/controller/vibefish-sim.sh" play --out "$dir" --deck-dir "$PRECONS" "${DECK_ARGS[@]}" \
      --games "$n" --start "$start" --seed "$seed" --clock "$CLOCK" --turn-cap "$CAP" \
      --forge-version "$FORGE_VERSION" >>"$log" 2>&1
    rc=$?
    set -e
    if [ "$rc" -eq 3 ] && [ -f "$dir/run.json" ]; then
      attempts=$((attempts + 1))
      start=$(jq '[.games[].index] | max + 1' "$dir/run.json")
      if [ "$start" -gt "$n" ]; then rc=0; break; fi
      if [ "$attempts" -gt 10 ]; then echo "shard $j: too many timeouts, giving up at game $start" >&2; break; fi
      echo "shard $j: wall clock hit, resuming at game $start" >&2
      continue
    fi
    break
  done
  echo "$rc" > "$OUT/shard-$j.rc"
}

if [ -n "$ONLY" ]; then
  n=$((GAMES / SHARDS)); [ "$ONLY" -le $((GAMES % SHARDS)) ] && n=$((n + 1))
  echo "running shard $ONLY of $SHARDS only ($n games), no rollup" >&2
  run_shard "$ONLY" "$n"
  rc=$(cat "$OUT/shard-$ONLY.rc")
  [ "$rc" -eq 0 ] || { echo "shard $ONLY exited with $rc (see $OUT/shard-$ONLY.log)" >&2; exit 1; }
  exit 0
fi

pids=()
for ((j = 1; j <= SHARDS; j++)); do
  n=$((GAMES / SHARDS)); [ "$j" -le $((GAMES % SHARDS)) ] && n=$((n + 1))
  run_shard "$j" "$n" &
  pids+=($!)
done
fail=0
for pid in "${pids[@]}"; do wait "$pid" || fail=1; done
for ((j = 1; j <= SHARDS; j++)); do
  rc=$(cat "$OUT/shard-$j.rc" 2>/dev/null || echo 99)
  [ "$rc" -eq 0 ] || { echo "shard $j exited with $rc (see $OUT/shard-$j.log)" >&2; fail=1; }
done

shopt -s nullglob
python3 -I "$HERE/rollup.py" "$OUT"/shard-*/ --out "$OUT" --run-id "$RUN_ID" --pod "$POD" ${INDEX:+--index "$INDEX"}
[ "$fail" -eq 0 ] || { echo "run finished with shard failures" >&2; exit 1; }
echo "done: $OUT/rollup.json" >&2
