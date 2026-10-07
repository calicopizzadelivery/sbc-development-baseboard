#!/bin/sh
# Mirror the reference boards listed in scripts/reference-boards.txt into reference-boards/ (git-ignored).
# Shallow clones and unpacked archives; re-running refreshes nothing already present.
set -e
cd "$(dirname "$0")/.."
mkdir -p reference-boards
grep -v '^#' scripts/reference-boards.txt | while read -r kind name src licence; do
    [ -z "$kind" ] && continue
    dest="reference-boards/$name"
    if [ -e "$dest" ]; then echo "have   $name"; continue; fi
    case "$kind" in
        git) echo "clone  $name"; git clone -q --depth 1 "$src" "$dest" || echo "FAILED $name" ;;
        zip) echo "fetch  $name"; mkdir -p "$dest" && curl -sL --max-time 300 -o "$dest/archive.zip" "$src" && (cd "$dest" && unzip -qo archive.zip && rm archive.zip) || echo "FAILED $name" ;;
    esac
done
