#!/usr/bin/env bash
# slot CMD...: runs CMD while holding one of three machine-wide slots, so that at most three Forge processes play at
# once on this 4-core machine however many agents are working. Waiters queue shortest job first (the -n GAMES of the
# command, 50 when it has none; table games through ab.py or league.py count ten times), then by arrival, so a
# 12-game goldfish run in the foreground is not starved by longer runs.
LOCKS=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/locks
Q="$LOCKS/queue"
n=50; prev=""
for a in "$@"; do
  case "$prev" in -n|--games) case "$a" in ''|*[!0-9]*) ;; *) n=$a ;; esac ;; esac
  prev="$a"
done
case "$*" in *ab.py*|*league.py*) n=$((n * 10)) ;; esac   # a table game takes about ten goldfish games
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
