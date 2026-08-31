"""Read or set a console variable. Value arrives in a temp FILE, not argv.

    echo "r.EyeAdaptation.CachedLightingPreExposure 8.9" > $TMPDIR/stacktown_cvar.txt
    ./Tools/rung.sh cvar.py

A bare name with no value just reports it.
"""
import os, tempfile
import unreal

F = os.path.join(tempfile.gettempdir(), 'stacktown_cvar.txt')
if not os.path.exists(F):
    raise SystemExit('cvar: nothing to do')
for line in [l.strip() for l in open(F).read().splitlines() if l.strip()]:
    parts = line.split()
    name = parts[0]
    before = unreal.SystemLibrary.get_console_variable_float_value(name)
    if len(parts) > 1:
        unreal.SystemLibrary.execute_console_command(None, line)
        after = unreal.SystemLibrary.get_console_variable_float_value(name)
        print('  %-46s %.3f -> %.3f' % (name, before, after))
        if abs(after - float(parts[1])) > 1e-3:
            print('     (did not take: asked %s)' % parts[1])
    else:
        print('  %-46s %.3f' % (name, before))
