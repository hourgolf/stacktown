#!/bin/zsh
# Run a UE python script inside the live editor with the project/level guard
# prepended. Use this for ANYTHING that mutates.
#
# Resolves its own location rather than hardcoding a path. The previous copy of
# this script (Saved/Stage2/data/rung.sh) cd'd into an agent scratchpad under
# /private/tmp that no longer belongs to anyone, which meant it silently ran a
# DIFFERENT _guard.py than the one in the repository - and the repo's guard had
# gone stale and still refused any level but Stage1_Building.
set -e
HERE="${0:A:h}"
ROOT="${HERE:h}"
SCRIPT="$1"
[ -n "$SCRIPT" ] || { echo "usage: rung.sh <script.py> [more args]"; exit 2; }
[ -f "$SCRIPT" ] || SCRIPT="$ROOT/Content/Python/$1"
[ -f "$SCRIPT" ] || { echo "no such script: $1"; exit 2; }
TMP="$(mktemp -t rung).py"
{ cat "$ROOT/Content/Python/_guard.py"; echo ""; cat "$SCRIPT"; } > "$TMP"
python3 "$ROOT/Tools/measure/uepy.py" "$TMP"
rc=$?
rm -f "$TMP"
exit $rc
