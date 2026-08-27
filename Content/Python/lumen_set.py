"""Set arbitrary Lumen cvars for a test. Reads stacktown_lumen.json {cvars:{}}."""
import unreal
import _path  # noqa: F401
import json
import os
import tempfile

job = json.load(open(os.path.join(tempfile.gettempdir(),
                                  'stacktown_lumen.json')))
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = eus.get_editor_world()
S = unreal.SystemLibrary
for k, v in job['cvars'].items():
    S.execute_console_command(w, '%s %s' % (k, v))
    got = (S.get_console_variable_float_value(k) if isinstance(v, float)
           else S.get_console_variable_int_value(k))
    print('  %-56s -> %s (read %s)' % (k, v, got))
