#!/bin/zsh
# Play Stacktown as its own window, outside the editor (2026-09-04).
#
# Launches the uncooked editor binary with -game on TestCity: the Python
# plugin loads, init_unreal.py runs, the economy and click drivers register,
# and the city restores from Content/Python/citystate.json - the owner's real
# save. The editor can stay open; lanes keep editing there. What the game
# shows is what was ON DISK when it launched: relaunch to see new work.
# Quit with Cmd-Q. Log: Saved/Logs/standalone.log
set -e
ROOT="${0:A:h:h}"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
MAP="${1:-/Game/Maps/TestCity}"
mkdir -p "$ROOT/Saved/Logs"
exec "$UE" "$ROOT/StacktownAlpha.uproject" "$MAP" -game -windowed -ResX=1600 -ResY=900 -log -ABSLOG="$ROOT/Saved/Logs/standalone.log"
