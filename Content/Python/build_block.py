#!/usr/bin/env python3
"""Build the whole block from the lot table. One entry point.

Ownership-gated: it only ever destroys actors whose label starts with a prefix
this script creates. The reused Stage 1 building (BLD_), the stage (STAGE_),
the cameras and the key/fill rig are never touched.

Run:  python3 build_block.py
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lots import LOTS
# the MCP session id goes stale across an editor restart and every call 404s
for _f in ('.mcp_sid',):
    try: os.remove(os.path.join(HERE,_f))
    except OSError: pass
from genbuild import build as genbuild

def ue(script, label):
    t = time.time()
    r = subprocess.run(['./rung.sh', script], capture_output=True, text=True, cwd=HERE)
    out = [l[7:] for l in r.stdout.splitlines() if l.startswith('[Info]')]
    ok = 'success: True' in r.stdout
    print('  %-22s %5.1fs  %s' % (label, time.time() - t, 'ok' if ok else 'FAILED'))
    for l in out[1:]:
        if l.strip(): print('      ' + l)
    if not ok:
        print('      ' + (r.stdout[-400:] or r.stderr[-400:]))
    return ok

print('=== 1. wipe owned ===');            ue('wipe_owned.py', 'wipe')
print('=== 2. generated buildings ===')
t = time.time()
for spec in LOTS:
    if spec['kind'] != 'gen': continue
    genbuild(spec)
print('  generated in %.0fs' % (time.time() - t))
print('=== 3. Assetsville lot ===');       ue('step_av.py', 'tileset volume')
print('=== 4. materials by role ===');     ue('assign_roles.py', 'role sweep')
print('=== 5. cores ===');                 ue('step_cores3.py', 'solid cores')
print('=== 6. practicals ===');            ue('practicals.py', 'practicals')
print('=== 7. props ===');                 ue('fix4_props.py', 'props by rule')
print('=== 8. vehicles + people ===');     ue('place_baked.py', 'baked statics')
print('=== 9. vehicle slot binding ===');  ue('fix6_vehmats2.py', 'vehicle slots')
# step 10 removed: the tuned intensities now live in practicals.py
print('=== 11. checks ===')
ue('check_block.py', 'geometry + party walls')
ue('gap_check2.py',  'no hollow facades')
print('\nbuild complete')
