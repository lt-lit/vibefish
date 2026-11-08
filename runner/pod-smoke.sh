#!/usr/bin/env bash
# Phase 0 smoke run: the benchmark pod (four bundled precons) plays itself in plain 4-player
# Commander mode, and the script checks that every game completed.
#
#   runner/pod-smoke.sh [-n GAMES] [-s SEED] [-c CLOCK_SECONDS] [-o OUTDIR] [-q]
#
# -q prints results only (Forge's quiet flag); without it the full game log is kept.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
POD="$HERE/benchmark-pod.json"

GAMES=3; SEED=$(date -u +%Y%m%d); CLOCK=900; OUTDIR="$ROOT/results"; QUIET=0
while getopts "n:s:c:o:q" opt; do
  case $opt in
    n) GAMES=$OPTARG ;;
    s) SEED=$OPTARG ;;
    c) CLOCK=$OPTARG ;;
    o) OUTDIR=$OPTARG ;;
    q) QUIET=1 ;;
    *) echo "usage: $0 [-n GAMES] [-s SEED] [-c CLOCK_SECONDS] [-o OUTDIR] [-q]" >&2; exit 2 ;;
  esac
done

[ -f "$RUNTIME/VIBEFISH_FORGE_VERSION" ] || { echo "No Forge runtime at $RUNTIME; run forge/fetch-forge.sh" >&2; exit 2; }
PRECONS="$RUNTIME/$(jq -r .precon_dir "$POD")"
mapfile -t DECKS < <(jq -r '.seats[].file' "$POD")
for d in "${DECKS[@]}"; do
  [ -f "$PRECONS/$d" ] || { echo "Missing precon in runtime: $PRECONS/$d" >&2; exit 1; }
done

mkdir -p "$OUTDIR"
STAMP=$(head -1 "$RUNTIME/VIBEFISH_FORGE_VERSION")
LOG="$OUTDIR/pod-smoke-$(date -u +%Y%m%dT%H%M%SZ)-seed${SEED}.log"
echo "Pod $(jq -r .name "$POD") on $STAMP: $GAMES game(s), seed $SEED, clock ${CLOCK}s, $(nproc) cpus"
echo "Log: $LOG"

QFLAG=()
[ "$QUIET" = 1 ] && QFLAG=(-q)
START=$(date +%s)
set +e
"$ROOT/forge/forge.sh" sim -f Commander -D "$PRECONS" -d "${DECKS[@]}" -n "$GAMES" -s "$SEED" -c "$CLOCK" "${QFLAG[@]}" >"$LOG" 2>&1
RC=$?
set -e
WALL=$(( $(date +%s) - START ))

COMPLETED=$(grep -c '^Game Result: Game [0-9]* ended in [0-9]* ms\. .* has won' "$LOG" || true)
DRAWS=$(grep -c 'ended in a Draw\|Stopping slow match as draw' "$LOG" || true)
ERRORS=$(grep -c 'Exception\|StackOverflowError' "$LOG" || true)

echo
echo "== pod-smoke summary =="
echo "forge $STAMP | requested $GAMES | completed $COMPLETED | draws $DRAWS | exceptions $ERRORS | exit $RC | wall ${WALL}s"
grep -oE 'ended in [0-9]+ ms' "$LOG" | grep -oE '[0-9]+' \
  | awk '{s+=$1; if(min==""||$1<min)min=$1; if($1>max)max=$1} END{if(NR>0) printf "per game: avg %.0fs  min %.0fs  max %.0fs\n", s/NR/1000, min/1000, max/1000}'
echo "winners:"
grep -E '^Game Result' "$LOG" | sed -E 's/.*ms\. (.*) has won!/  \1/' | sort | uniq -c | sort -rn
echo "loss reasons:"
grep -E '^Game Outcome: .* has lost' "$LOG" | sed -E 's/.* has lost (.*)/  \1/' | sort | uniq -c | sort -rn | head -8

if [ "$RC" -ne 0 ] || [ "$COMPLETED" -ne "$GAMES" ] || [ "$ERRORS" -ne 0 ]; then
  echo "FAIL: not every game completed cleanly (see $LOG)" >&2
  exit 1
fi
echo "OK: all $GAMES games completed"
