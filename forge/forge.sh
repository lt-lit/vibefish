#!/usr/bin/env bash
# Launches the pinned Forge runtime headless. Usage: forge/forge.sh sim <sim args>
# Run forge/fetch-forge.sh first. Env: FORGE_RUNTIME (dir), FORGE_XMX (default 4g), FORGE_JAVA_OPTS.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RUNTIME="${FORGE_RUNTIME:-$HERE/runtime}"
JAR=$(compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1 || true)
if [ -z "$JAR" ]; then
  echo "Forge runtime not found at $RUNTIME. Run forge/fetch-forge.sh first." >&2
  exit 2
fi
# Forge resolves res/ and forge.profile.properties against the working directory.
cd "$RUNTIME"
# shellcheck disable=SC2086
exec java -Xmx"${FORGE_XMX:-4g}" -Djava.awt.headless=true -Dio.netty.tryReflectionSetAccessible=true \
  -Dfile.encoding=UTF-8 ${FORGE_JAVA_OPTS:-} -jar "$(basename "$JAR")" "$@"
