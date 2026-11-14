#!/usr/bin/env bash
# shards.sh EXAM_DIR ENTRY: the shard artifacts of one ab-run request as one run directory. A session helper.
#
# EXAM_DIR holds unzipped shard artifacts of an ab-run workflow run, each in a directory of its artifact's name
# (ab-ENTRY-N; ENTRY is `deck` or `deck@variant`, as in the run's request; fetch_artifact.sh puts them there). They are
# copied together into EXAM_DIR/results/ab-ENTRY, which is what `runner/ab.py play` would have written locally, and rolled
# up. `runner/playtest.py EXAM_DIR/results/ab-ENTRY --arm stock|playbook --json OUT.json` reads that directory.
set -e
D=$1; E=$2
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mkdir -p "$D/results/ab-$E"
n=0
for a in "$D"/ab-"$E"-[0-9]*; do
  case "$a" in *-log) continue;; esac
  [ -d "$a" ] || continue
  cp -r --update=none "$a"/. "$D/results/ab-$E"/; n=$((n + 1))
done
[ "$n" -gt 0 ] || { echo "no shard directories $D/ab-$E-N" >&2; exit 1; }
(cd "$ROOT" && python3 -I runner/ab.py rollup "$D/results/ab-$E" > /dev/null 2>&1) || echo "rollup failed for $D/results/ab-$E" >&2
echo "$D/results/ab-$E: $n shards"
