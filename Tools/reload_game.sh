#!/bin/zsh
# Hot-reload the Python drivers INTO THE RUNNING STANDALONE GAME (Tools/play.sh)
# without relaunching it: unregister the economy and click drivers there,
# re-import init_unreal.py from disk (which re-registers both). Python-side
# fixes land live; Blueprint, material and map changes still need a relaunch.
ROOT="${0:A:h:h}"
S="$(mktemp -t reloadgame).py"
cat > "$S" <<'PY'
import unreal, os, sys, importlib
_have = os.path.abspath(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
assert _have.rstrip('/').endswith('StacktownAlpha'), 'WRONG PROJECT: %s' % _have
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem) is None, 'this is the EDITOR, not the game - refusing'
if os.path.exists(os.path.join(_have, 'Content', 'Python', 'lane_pie.marker')):
    raise SystemExit('ABORT: lane_pie.marker present - the reloaded driver would resolve to the test file')
h = getattr(unreal, '_stacktown_driver_handle', None)
if h is not None:
    unreal.unregister_slate_post_tick_callback(h)
unreal._stacktown_driver_handle = None
unreal._stacktown_driver_registered = False
c = getattr(unreal, '_stacktown_clickdriver_handle', None)
if c is not None:
    unreal.unregister_slate_post_tick_callback(c)
    unreal._stacktown_clickdriver_handle = None
sys.path.insert(0, os.path.join(_have, 'Content', 'Python'))
for m in [n for n, mod in list(sys.modules.items()) if getattr(mod, '__file__', None) and os.path.join(_have, 'Content', 'Python') in str(mod.__file__)]:
    del sys.modules[m]
import init_unreal
print('GAME RELOAD: economy=%s click=%s state=%s' % (
    getattr(unreal, '_stacktown_driver_registered', None),
    getattr(unreal, '_stacktown_clickdriver_handle', None) is not None,
    init_unreal._state_path_source()))
PY
UEPY_WANT_GAME=1 python3 "$ROOT/Tools/measure/uepy.py" "$S"
rc=$?
rm -f "$S"
exit $rc
