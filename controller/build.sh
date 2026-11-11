#!/usr/bin/env bash
# Compiles the Vibefish harness against the Forge jar in $FORGE_RUNTIME (default forge/runtime):
#   controller/out/<forge-jar-name>/vibefish-sim.jar   (one build per Forge build, so runtimes can coexist)
#
#   controller/build.sh           builds only when it has to: no jar yet, another Forge jar, or a source newer than the jar
#   controller/build.sh --force   builds regardless
#
# runner/ab.py and runner/league.py call this at the start of every run, and several runs may share one tree (a batch
# of decks worked at once), so a build that is not needed must not touch the jar a running JVM is reading; a build that
# is needed writes the new jar beside the old one and renames it into place.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
JAR=$(compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1 || true)
[ -n "$JAR" ] || { echo "Forge runtime not found at $RUNTIME; run forge/fetch-forge.sh first" >&2; exit 2; }
OUT="$HERE/out/$(basename "$JAR" .jar)"
SIMJAR="$OUT/vibefish-sim.jar"
if [ "${1:-}" != "--force" ] && [ -f "$SIMJAR" ] && [ "$(sha256sum "$JAR" | cut -c1-16)" = "$(cat "$OUT/forge-jar.sha" 2>/dev/null)" ] \
   && [ -z "$(find "$HERE/src" -name '*.java' -newer "$SIMJAR" 2>/dev/null)" ]; then
  echo "up to date: $SIMJAR"
  exit 0
fi
mkdir -p "$OUT"
rm -rf "${OUT:?}/classes"
mkdir -p "$OUT/classes"
find "$HERE/src" -name '*.java' > "$OUT/sources.txt"
javac --release 17 -Xlint:deprecation -Xlint:unchecked -encoding UTF-8 -cp "$JAR" -d "$OUT/classes" @"$OUT/sources.txt"
jar --create --file "$SIMJAR.new" -C "$OUT/classes" .
mv -f "$SIMJAR.new" "$SIMJAR"
sha256sum "$JAR" | cut -c1-16 > "$OUT/forge-jar.sha"
echo "built $SIMJAR against $(basename "$JAR")"
