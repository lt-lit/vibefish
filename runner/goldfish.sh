#!/usr/bin/env bash
# Goldfish run: one deck against three do-nothing opponents (lands only), to measure the deck's own speed and
# consistency without interaction: own turn of the win ("kill turn"), commander turn, land drops, cast counts.
#
#   runner/goldfish.sh DECK.dck [-n GAMES] [-s SEED] [-c CLOCK_S] [-t TURN_CAP] [-o RESULTS_DIR] [-i RUN_ID]
#                      [-R RUNTIME_DIR] [-m off|on|max] [-p PROFILE] [-P PLAYBOOK.json] [-D DATA.json]
#
# DECK.dck is a path (absolute or relative to the current directory). Output as run-pod.sh: results/<run-id>/
# with shard-1/, rollup.json and goldfish.json (kill-turn distribution). -P plays the deck under its playbook
# (the playbook object of a playbook/precons/<id>.json file), -D gives it that file's data; the same seed with and
# without -P is the paired comparison a playbook's cast rules are tuned on (runner/hands.py compare).
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
DECK=${1:?deck file}; shift
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
GAMES=8; SEED=$(date -u +%Y%m%d); CLOCK=900; CAP=80; RESULTS="$ROOT/results"; RUN_ID=""; MC="off"; PROFILE=""; PLAYBOOK=""; DATA=""
while getopts "n:s:c:t:o:i:R:m:p:P:D:" opt; do
  case $opt in
    n) GAMES=$OPTARG ;; s) SEED=$OPTARG ;; c) CLOCK=$OPTARG ;; t) CAP=$OPTARG ;; o) RESULTS=$OPTARG ;; i) RUN_ID=$OPTARG ;;
    R) RUNTIME=$(cd "$OPTARG" && pwd) ;; m) MC=$OPTARG ;; p) PROFILE=$OPTARG ;;
    P) PLAYBOOK=$(cd "$(dirname "$OPTARG")" && pwd)/$(basename "$OPTARG") ;; D) DATA=$(cd "$(dirname "$OPTARG")" && pwd)/$(basename "$OPTARG") ;;
    *) echo "usage: $0 DECK.dck [-n GAMES] [-s SEED] [-c CLOCK_S] [-t TURN_CAP] [-o RESULTS_DIR] [-i RUN_ID] [-R RUNTIME] [-m MC] [-p PROFILE] [-P PLAYBOOK.json] [-D DATA.json]" >&2; exit 2 ;;
  esac
done
[ -f "$DECK" ] || { echo "deck not found: $DECK" >&2; exit 2; }
[ -f "$RUNTIME/VIBEFISH_FORGE_VERSION" ] || { echo "No Forge runtime at $RUNTIME; run forge/fetch-forge.sh" >&2; exit 2; }
export FORGE_RUNTIME="$RUNTIME"
FORGE_VERSION=$(head -1 "$RUNTIME/VIBEFISH_FORGE_VERSION")
DECK_ABS=$(cd "$(dirname "$DECK")" && pwd)/$(basename "$DECK")
ID=$(basename "$DECK" .dck | tr 'A-Z' 'a-z' | sed -E 's/\[[^]]*\]//g; s/[^a-z0-9]+/-/g; s/(^-|-$)//g')
[ -n "$RUN_ID" ] || RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-goldfish-${ID}-${FORGE_VERSION}-s${SEED}$([ "$MC" != off ] && echo "-mc$MC")$([ -n "$PLAYBOOK" ] && echo "-playbook")$([ -n "$DATA" ] && echo "-data")"
OUT="$RESULTS/$RUN_ID"
mkdir -p "$OUT/shard-1"
PLAINS="$HERE/goldfish/Goldfish-Plains.dck"
EXTRA=(--mc "$MC")
if [ -n "$PROFILE" ]; then EXTRA+=(--profile "$PROFILE"); fi
if [ -n "$PLAYBOOK" ]; then EXTRA+=(--playbook "$ID=$PLAYBOOK"); fi
if [ -n "$DATA" ]; then EXTRA+=(--data "$ID=$DATA"); fi
echo "goldfish $RUN_ID: $ID vs 3x do-nothing, $GAMES game(s), seed $SEED, clock ${CLOCK}s, turn cap $CAP, runtime $(basename "$RUNTIME")$([ -n "$PLAYBOOK" ] && echo ", playbook $(basename "$PLAYBOOK")")$([ -n "$DATA" ] && echo ", data $(basename "$DATA")")" >&2
# A game that runs into the clock ends the harness process (exit 3); pick the run up at the next game, as run-pod.sh does.
START=1; ATTEMPTS=0
while :; do
  rc=0
  "$ROOT/controller/vibefish-sim.sh" play --out "$OUT/shard-1" --deck "$ID=$DECK_ABS" \
    --deck "goldfish-1=$PLAINS" --deck "goldfish-2=$PLAINS" --deck "goldfish-3=$PLAINS" \
    --games "$GAMES" --start "$START" --seed "$SEED" --clock "$CLOCK" --turn-cap "$CAP" --forge-version "$FORGE_VERSION" "${EXTRA[@]}" \
    >>"$OUT/shard-1.log" 2>&1 || rc=$?
  [ "$rc" -eq 3 ] && [ -f "$OUT/shard-1/run.json" ] || break
  ATTEMPTS=$((ATTEMPTS + 1))
  START=$(jq '[.games[].index] | max + 1' "$OUT/shard-1/run.json")
  [ "$START" -le "$GAMES" ] || { rc=0; break; }
  [ "$ATTEMPTS" -le 10 ] || { echo "too many games on the clock, stopping at game $START" >&2; break; }
  echo "clock hit, resuming at game $START" >&2
done
[ "$rc" -eq 0 ] || [ "$rc" -eq 3 ] || { echo "harness exited $rc (see $OUT/shard-1.log)" >&2; exit "$rc"; }
python3 -I "$HERE/rollup.py" "$OUT/shard-1/" --out "$OUT" --run-id "$RUN_ID" --pod "$HERE/benchmark-pod.json" 2>/dev/null >/dev/null
python3 -I - "$OUT/shard-1/run.json" "$OUT/goldfish.json" <<'PY'
import json, sys, statistics, collections
run = json.load(open(sys.argv[1]))
kills, caps, cmdr = [], 0, []
for g in run["games"]:
    me = next(p for p in g["players"] if p["seat"] == 0)
    if g.get("winner") == 0:
        kills.append(me["turns_played"])
    else:
        caps += 1
dist = collections.Counter(kills)
out = {"run_id": run.get("forge_version") and sys.argv[2].split("/")[-2], "deck": run["decks"][0]["id"], "games": len(run["games"]),
       "wins": len(kills), "not_finished": caps, "kill_turn_mean": round(statistics.fmean(kills), 2) if kills else None,
       "kill_turn_median": statistics.median(kills) if kills else None, "kill_turn_min": min(kills) if kills else None,
       "kill_turn_max": max(kills) if kills else None, "kill_turn_distribution": {str(k): dist[k] for k in sorted(dist)}}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(f"goldfish {out['deck']}: {out['wins']}/{out['games']} wins, kill turn mean {out['kill_turn_mean']} median {out['kill_turn_median']} "
      f"(min {out['kill_turn_min']}, max {out['kill_turn_max']}), not finished {out['not_finished']}", file=sys.stderr)
print(f"  distribution {out['kill_turn_distribution']}", file=sys.stderr)
PY
echo "done: $OUT" >&2
