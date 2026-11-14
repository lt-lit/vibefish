#!/usr/bin/env bash
# slot CMD...: runs CMD while holding one of three machine-wide slots, so that at most three Forge processes play at
# once on this 4-core machine however many agents are working. Goldfish runs queue shortest first (the -n GAMES of the
# command, 50 when it has none), then by arrival, so a 12-game goldfish run in the foreground is not starved by longer
# ones. Table runs (ab.py, league.py) queue behind every goldfish run and among themselves by arrival alone: ordered
# by size, agents that asked for 4 or 6 tables kept jumping ahead of those that asked for 8 (2026-11-14, two agents
# without a game in ninety minutes).
LOCKS=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/locks
Q="$LOCKS/queue"
n=50; prev=""
for a in "$@"; do
  case "$prev" in -n|--games) case "$a" in ''|*[!0-9]*) ;; *) n=$a ;; esac ;; esac
  prev="$a"
done
case "$*" in *ab.py*|*league.py*) n=80 ;; esac   # table runs: one class, first come first served (ordered by size they starved the 8-game runs)
t=$(printf '%04d-%s-%s' "$n" "$(date +%s%N)" "$$")
: > "$Q/$t"
trap 'rm -f "$Q/$t"' EXIT
while :; do
  for f in "$Q"/*; do
    [ -e "$f" ] || continue
    p=${f##*-}; kill -0 "$p" 2>/dev/null || rm -f "$f"
  done
  first=$(ls "$Q" | sort | head -1)
  if [ "$first" = "$t" ]; then
    for s in 1 2 3; do
      exec 9>"$LOCKS/slot-$s.lock"
      if flock -n 9; then
        rm -f "$Q/$t"
        "$@"; rc=$?
        exit $rc
      fi
    done
  fi
  sleep 2
done
