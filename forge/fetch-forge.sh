#!/usr/bin/env bash
# Downloads the pinned Forge release and assembles a trimmed headless runtime in forge/runtime/.
#
#   forge/fetch-forge.sh                          # tag from forge/VERSION, checksum-verified
#   FORGE_CHANNEL=snapshot forge/fetch-forge.sh   # daily snapshot, spoiler-season testing only
#   forge/fetch-forge.sh --force                  # rebuild the runtime even if it is current
#
# Nothing here is committed: forge/dl/ and forge/runtime/ are gitignored.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DL="$HERE/dl"
RUNTIME="${FORGE_RUNTIME:-$HERE/runtime}"
CHANNEL="${FORGE_CHANNEL:-pinned}"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

TAG=$(tr -d '[:space:]' < "$HERE/VERSION")
case "$CHANNEL" in
  pinned)
    ASSET="forge-installer-${TAG#forge-}.tar.bz2"
    URL="https://github.com/Card-Forge/forge/releases/download/${TAG}/${ASSET}"
    STAMP="$TAG"
    ;;
  snapshot)
    # The snapshot tarball carries a build date in its name, so it has to be discovered.
    API="https://api.github.com/repos/Card-Forge/forge/releases/tags/daily-snapshots"
    AUTH=()
    [ -n "${GITHUB_TOKEN:-}" ] && AUTH=(-H "Authorization: Bearer $GITHUB_TOKEN")
    JSON=$(curl -fsSL "${AUTH[@]}" -H "Accept: application/vnd.github+json" "$API")
    ASSET=$(jq -r '.assets[] | select(.name | test("^forge-installer-.*\\.tar\\.bz2$")) | .name' <<<"$JSON" | head -1)
    [ -n "$ASSET" ] || { echo "No snapshot tarball found at $API" >&2; exit 1; }
    URL=$(jq -r --arg n "$ASSET" '.assets[] | select(.name == $n) | .browser_download_url' <<<"$JSON")
    STAMP="snapshot-$(jq -r --arg n "$ASSET" '.assets[] | select(.name == $n) | .updated_at[:10]' <<<"$JSON")"
    ;;
  *) echo "FORGE_CHANNEL must be 'pinned' or 'snapshot' (got '$CHANNEL')" >&2; exit 1 ;;
esac

if [ "$FORCE" = 0 ] && [ -f "$RUNTIME/VIBEFISH_FORGE_VERSION" ] \
   && [ "$(head -1 "$RUNTIME/VIBEFISH_FORGE_VERSION")" = "$STAMP" ] \
   && compgen -G "$RUNTIME/forge-gui-desktop-*-jar-with-dependencies.jar" >/dev/null; then
  echo "Forge runtime $STAMP already present at $RUNTIME"
  exit 0
fi

# Refuse to replace a directory that is not a Vibefish runtime (FORGE_RUNTIME could point anywhere).
if [ -e "$RUNTIME" ] && [ ! -f "$RUNTIME/VIBEFISH_FORGE_VERSION" ] && [ -n "$(ls -A "$RUNTIME" 2>/dev/null)" ]; then
  echo "Refusing to replace $RUNTIME: it is not empty and not a Vibefish Forge runtime" >&2
  exit 1
fi

mkdir -p "$DL"
TARBALL="$DL/$ASSET"
if [ ! -s "$TARBALL" ]; then
  echo "Downloading $URL"
  curl -fL --retry 3 --retry-delay 5 -o "$TARBALL.part" "$URL"
  mv "$TARBALL.part" "$TARBALL"
fi

if [ "$CHANNEL" = pinned ]; then
  echo "Verifying checksum against forge/SHA256SUMS"
  (cd "$DL" && grep " $ASSET\$" "$HERE/SHA256SUMS" | sha256sum -c -)
else
  echo "Snapshot build, no pinned checksum. sha256: $(sha256sum "$TARBALL" | cut -d' ' -f1)"
fi

echo "Extracting"
STAGE=$(mktemp -d "$DL/stage.XXXXXX")
tar -xjf "$TARBALL" -C "$STAGE"

# Sim mode needs the desktop jar and res/ (card scripts, editions, formats, AI profiles, lists,
# precons, languages). Everything else is GUI, adventure mode or other launchers.
echo "Trimming to a headless runtime"
for d in adventure music sound skins fonts puzzle tutorial conquest; do
  rm -rf "${STAGE:?}/res/$d"
done
rm -rf "${STAGE:?}/docs"
rm -f "${STAGE:?}"/*.exe "${STAGE:?}"/*.cmd "${STAGE:?}"/*.command "${STAGE:?}"/forge-adventure.* \
      "${STAGE:?}"/adventure-editor* "${STAGE:?}"/gdx-particle-editor.jar "${STAGE:?}"/forge-gui-mobile-dev-*.jar

# Keep Forge's user data inside the runtime instead of ~/.forge and ~/.cache/forge.
# Forge reads this file from its program directory (the launcher cds there); relative paths are
# resolved against it.
cat > "$STAGE/forge.profile.properties" <<'PROPS'
userDir=./profile/user/
cacheDir=./profile/cache/
decksDir=./profile/decks/
PROPS
mkdir -p "$STAGE/profile/user" "$STAGE/profile/cache" "$STAGE/profile/decks"

JAR=$(basename "$(compgen -G "$STAGE/forge-gui-desktop-*-jar-with-dependencies.jar" | head -1)")
printf '%s\n%s\n%s\n' "$STAMP" "$JAR" "$(sha256sum "$TARBALL" | cut -d' ' -f1)" > "$STAGE/VIBEFISH_FORGE_VERSION"

if [ -e "$RUNTIME" ]; then
  OLD=$(mktemp -d "$DL/old.XXXXXX")
  mv "$RUNTIME" "$OLD/runtime"
  rm -rf "${OLD:?}"
fi
mv "$STAGE" "$RUNTIME"
echo "Forge runtime ready: $STAMP ($JAR), $(du -sh "$RUNTIME" | cut -f1) at $RUNTIME"
