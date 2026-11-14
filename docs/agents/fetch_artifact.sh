#!/usr/bin/env bash
# fetch_artifact.sh DEST_DIR ARTIFACT_NAME 'DOWNLOAD_URL'
# Downloads one Actions artifact zip from its short-lived URL and unzips it into DEST_DIR/ARTIFACT_NAME/ (its own new directory).
# The URL may be pasted with & in place of &: that is fixed here. Prints "ok NAME <files>" or "FAILED NAME <why>".
set -u
dest=$1; name=$2; url=${3//\\u0026/&}
mkdir -p "$dest"
if [ -d "$dest/$name" ] && [ -n "$(ls -A "$dest/$name" 2>/dev/null)" ]; then echo "ok $name (already there)"; exit 0; fi
zip="$dest/.$name.zip"
if ! curl -sS -L --fail --retry 2 -o "$zip" "$url"; then echo "FAILED $name (download)"; rm -f "$zip"; exit 1; fi
rm -rf "$dest/$name"; mkdir -p "$dest/$name"
if ! unzip -q -o "$zip" -d "$dest/$name"; then echo "FAILED $name (unzip)"; rm -rf "$dest/$name" "$zip"; exit 1; fi
rm -f "$zip"
echo "ok $name $(find "$dest/$name" -type f | wc -l) files"
