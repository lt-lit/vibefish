#!/usr/bin/env bash
# playbook_check.sh [RUNTIME_DIR] [FILE...]: parse playbook files with the harness's own loader. A session helper.
#
# Every playbook/precons/*.json and playbook/variants/*.json (or the files named) is read by vibefish.Playbook, the
# class a game reads it with, so a key the format does not know or a value it refuses shows here and not in the
# first game of an Actions run. Run it after a change to controller/src/vibefish/Playbook.java and before a candidate
# goes to the tables. RUNTIME_DIR defaults to forge/runtime-snapshot; the harness jar is built if it is not there.
set -e
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
RT=${1:-$ROOT/forge/runtime-snapshot}; [ $# -gt 0 ] && shift
RT=$(cd "$RT" && pwd)
FJ=$(ls "$RT"/forge-gui-desktop-*-jar-with-dependencies.jar | head -1)
FORGE_RUNTIME="$RT" "$ROOT/controller/build.sh" > /dev/null 2>&1 || true
VJ="$ROOT/controller/out/$(basename "$FJ" .jar)/vibefish-sim.jar"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
javac -cp "$FJ:$VJ" -d "$TMP" "$ROOT/docs/agents/PbCheck.java" 2>&1 | grep -v "^Picked up" || true
cd "$ROOT"
if [ $# -eq 0 ]; then set -- playbook/precons/*.json playbook/variants/*.json; fi
java -cp "$FJ:$VJ:$TMP" PbCheck "$@" 2>&1 | grep -v "^Picked up"
