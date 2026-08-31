"""Put Lumen's console variables back to their engine defaults.

WHY THIS FILE EXISTS. Chasing the flicker I set four cvars to 0 one at a time
to eliminate them as causes - TraceMeshSDFs, ScreenProbeGather.ScreenTraces,
SurfaceCache.CardCaptureRefreshFraction, SurfaceCache.MeshCardsUpdateFrequency
Scale - and never put any of them back. Console cvars are session state: they
survive every level load and every save, and they do not show up in any asset
or any diff. The editor ran degraded for the rest of the session and the owner
was judging a crippled renderer.

A diagnostic that changes global state must own restoring it. This is that.
"""
import unreal
import _path  # noqa: F401

DEFAULTS = [
    # (cvar, engine default, what turning it off costs)
    ('r.Lumen.TraceMeshSDFs', 1, 'detail tracing against mesh distance fields'),
    ('r.Lumen.ScreenProbeGather.ScreenTraces', 1, 'screen-space tracing'),
    ('r.LumenScene.SurfaceCache.CardCaptureRefreshFraction', 0.125,
     'surface cache refresh'),
    # r.LumenScene.SurfaceCache.MeshCardsUpdateFrequencyScale was RETIRED
    # from this list 2026-08-29: the 5.8 upgrade REMOVED the cvar entirely
    # (SearchCVars finds nothing), so its verify could never pass, and the
    # assert below stopped the restore BEFORE TemporalFilterProbes - the
    # direct anti-noise term - was reached. The flicker "came back" because
    # this restore half-ran. A restore list must be kept current with the
    # engine or it becomes the fault it exists to fix. (Its old float-read
    # trap note: get_console_variable_int_value reads 0 on any float cvar -
    # verify with the read that matches the type.)
    ('r.Lumen.ScreenProbeGather.TemporalFilterProbes', 1,
     'temporal filtering of screen probes - the direct anti-noise term'),
]

eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = eus.get_editor_world()
S = unreal.SystemLibrary
for name, val, what in DEFAULTS:
    if isinstance(val, int):
        before = S.get_console_variable_int_value(name)
    else:
        before = S.get_console_variable_float_value(name)
    S.execute_console_command(w, '%s %s' % (name, val))
    if isinstance(val, int):
        after = S.get_console_variable_int_value(name)
        ok = after == val
    else:
        after = S.get_console_variable_float_value(name)
        ok = abs(after - val) < 1e-4
    print('  %-58s %s -> %s  %s   (%s)'
          % (name, before, after, 'ok' if ok else '*** NOT SET ***', what))
    assert ok, '%s did not take' % name
print('lumen_defaults: %d cvars restored' % len(DEFAULTS))
