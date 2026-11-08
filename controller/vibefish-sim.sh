#!/usr/bin/env bash
# Runs the Vibefish harness inside the pinned Forge runtime. Builds it first if needed.
#   controller/vibefish-sim.sh play --out results/x --deck id=file.dck ... [--deck-dir DIR] ...
#   controller/vibefish-sim.sh check [--deck-dir DIR] file.dck ...
# Relative paths are resolved against the directory you run this from.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
RUNTIME="${FORGE_RUNTIME:-$ROOT/forge/runtime}"
JAR=$(compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1 || true)
[ -n "$JAR" ] || { echo "Forge runtime not found at $RUNTIME; run forge/fetch-forge.sh first" >&2; exit 2; }
SIMJAR="$HERE/out/vibefish-sim.jar"
if [ ! -f "$SIMJAR" ] || [ "$(sha256sum "$JAR" | cut -c1-16)" != "$(cat "$HERE/out/forge-jar.sha" 2>/dev/null)" ] \
   || [ -n "$(find "$HERE/src" -name '*.java' -newer "$SIMJAR" 2>/dev/null)" ]; then
  "$HERE/build.sh" >&2
fi
export VIBEFISH_CWD="$PWD"
cd "$RUNTIME"
# shellcheck disable=SC2086
exec java -Xmx"${FORGE_XMX:-4g}" -Djava.awt.headless=true -Dio.netty.tryReflectionSetAccessible=true \
  -Dfile.encoding=UTF-8 ${FORGE_JAVA_OPTS:-} -cp "$JAR:$SIMJAR" vibefish.Sim "$@"
