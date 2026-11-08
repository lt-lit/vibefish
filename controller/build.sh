#!/usr/bin/env bash
# Compiles the Vibefish harness against the Forge jar in $FORGE_RUNTIME (default forge/runtime):
#   controller/out/<forge-jar-name>/vibefish-sim.jar   (one build per Forge build, so runtimes can coexist)
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
JAR=$(compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1 || true)
[ -n "$JAR" ] || { echo "Forge runtime not found at $RUNTIME; run forge/fetch-forge.sh first" >&2; exit 2; }
OUT="$HERE/out/$(basename "$JAR" .jar)"
mkdir -p "$OUT"
rm -rf "${OUT:?}/classes"
mkdir -p "$OUT/classes"
find "$HERE/src" -name '*.java' > "$OUT/sources.txt"
javac --release 17 -Xlint:deprecation -Xlint:unchecked -encoding UTF-8 -cp "$JAR" -d "$OUT/classes" @"$OUT/sources.txt"
jar --create --file "$OUT/vibefish-sim.jar" -C "$OUT/classes" .
sha256sum "$JAR" | cut -c1-16 > "$OUT/forge-jar.sha"
echo "built $OUT/vibefish-sim.jar against $(basename "$JAR")"
