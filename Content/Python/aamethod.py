"""Switch the viewport anti-aliasing method. Reads stacktown_aa.json {method}.

0 none, 1 FXAA, 2 TAA, 4 TSR. The project runs TSR (4). TSR resolves a moving
image beautifully and is the usual suspect for SHIMMER on thin geometry held
still - and this catalogue is built almost entirely from 4-8 uu members, which
is the worst case for it.
"""
import unreal
import _path  # noqa: F401
import json
import os
import tempfile

NAMES = {0: 'none', 1: 'FXAA', 2: 'TAA', 3: 'MSAA', 4: 'TSR'}
job = json.load(open(os.path.join(tempfile.gettempdir(), 'stacktown_aa.json')))
m = int(job['method'])
eus = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = eus.get_editor_world()
S = unreal.SystemLibrary
before = S.get_console_variable_int_value('r.AntiAliasingMethod')
S.execute_console_command(w, 'r.AntiAliasingMethod %d' % m)
after = S.get_console_variable_int_value('r.AntiAliasingMethod')
print('  r.AntiAliasingMethod  %s (%s) -> %s (%s)  %s'
      % (before, NAMES.get(before, '?'), after, NAMES.get(after, '?'),
         'ok' if after == m else '*** NOT SET ***'))
assert after == m, 'anti-aliasing method did not take'
