#!/bin/zsh
# Package Stacktown for Mac (universal) - the invocation that first succeeded
# on 2026-09-06 (Docs/HANDOFF.md §5). Output: Saved/Packaged/Mac/StacktownAlpha.app
#
# -skipbuildeditor: UAT would otherwise rebuild the editor target; with the
#   editor open that leaves a -000N hot-reload dylib and a stale .modules.
# -DisablePlugins for the cook: the MCP plugins bind port 8000, which the open
#   editor holds; the cook treats that logged error as a failure.
# -package: on Mac the archive step copies only the .app; without -package the
#   bundle's Contents/UE (engine + project payload, TBB dylibs) is left behind
#   in Saved/StagedBuilds and the app dies at launch on libtbb.12.dylib.
# Architecture comes from [/Script/MacTargetPlatform.MacTargetSettings] in
# Config/DefaultEngine.ini (universal, owner's word).
set -e
ROOT="${0:A:h:h}"
UE="/Users/Shared/Epic Games/UE_5.8"
CONFIG="${1:-Development}"
LOG="$ROOT/Saved/Logs/package.log"
mkdir -p "$ROOT/Saved/Packaged" "$ROOT/Saved/Logs"
"$UE/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$ROOT/StacktownAlpha.uproject" -platform=Mac -clientconfig="$CONFIG" \
  -build -skipbuildeditor -cook -stage -package -pak -archive -archivedirectory="$ROOT/Saved/Packaged" \
  -additionalcookeroptions="-DisablePlugins=ModelContextProtocol,EditorToolset,AutomationTestToolset" \
  -unattended -noP4 -utf8output > "$LOG" 2>&1 || { echo "PACKAGE FAILED - see $LOG"; grep -n "Error\|BUILD FAILED" "$LOG" | grep -v "Missing cached shadermap" | head -10; exit 1; }
APP="$ROOT/Saved/Packaged/Mac/StacktownAlpha.app"
echo "PACKAGED: $APP ($(du -sh "$APP" | cut -f1), archs: $(lipo -archs "$APP/Contents/MacOS/StacktownAlpha"))"
