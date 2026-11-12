#!/usr/bin/env bash
# slot CMD...: runs CMD while holding one of two machine-wide slots, so that at most two Forge
# processes play at once on this 4-core machine however many sessions are working. Waits for a free slot.
LOCKS=/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/locks
while :; do
  for n in 1 2; do
    exec 9>"$LOCKS/slot-$n.lock"
    if flock -n 9; then
      "$@"; rc=$?
      exit $rc
    fi
  done
  sleep 3
done
