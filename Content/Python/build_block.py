#!/usr/bin/env python3
"""Build the whole block from the lot table. One entry point.

Ownership-gated: it only ever destroys actors whose label starts with a prefix
this script creates. The reused Stage 1 building (BLD_), the stage (STAGE_),
the cameras and the key/fill rig are never touched.

Run:  python3 build_block.py
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNG = os.path.join(ROOT, 'Tools', 'rung.sh')
sys.path.insert(0, HERE)
from lots import LOTS
# the MCP session id goes stale across an editor restart and every call 404s
for _f in ('.mcp_sid',):
    try: os.remove(os.path.join(HERE,_f))
    except OSError: pass
from genbuild import build as genbuild
import zones

def ue(script, label):
    t = time.time()
    # rung.sh lives in Tools/, not next to these scripts. './rung.sh' resolved
    # to nothing from here, so every step of this build failed before it ran.
    r = subprocess.run([RUNG, script], capture_output=True, text=True, cwd=HERE)
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
    if spec['kind'] == 'gen':
        genbuild(spec)
    elif spec['kind'] != 'av':
        zones.build(spec)
print('  generated in %.0fs' % (time.time() - t))
print('=== 3. Assetsville lot ===');       ue('step_av.py', 'tileset volume')
print('=== 3b. exposed flank elevations ===')
t = time.time()
import step_elevations
step_elevations.run()
print('  flanks in %.0fs' % (time.time() - t))
# step_roles.py, not assign_roles.py: assign_roles carries a hardcoded wall map
# ({'Narrow','Wide','Mid'}) that predates the city table, has a lot in it that
# no longer exists, and knows nothing about block B or the ELEV_ actors.
print('=== 4. materials by role ===');     ue('step_roles.py', 'role sweep')
print('=== 5. cores ===');                 ue('step_cores3.py', 'solid cores')
print('=== 6. practicals ===');            ue('practicals.py', 'practicals')
print('=== 7. props ===');                 ue('fix4_props.py', 'props by rule')
print('=== 8. vehicles + people ===');     ue('place_baked.py', 'baked statics')
# Step 9 named fix6_vehmats2.py, which DOES NOT EXIST in this repository - so
# this step has been reporting FAILED on every run. step_veh2s.py replaces it and
# does what it was presumably for: the baked meshes are open shells, so a
# single-sided card material culls their backfaces and the road shows through.
print('=== 9. vehicle slot binding ==='); ue('step_veh2s.py', 'two-sided vehicles')
# Without this the trees revert to the donor pack's acid-green leaf material on
# every rebuild, because fix4_props.py places them with native=True.
print('=== 9b. card foliage ===');        ue('step_foliage.py', 'foliage by slot name')
# step 10 removed: the tuned intensities now live in practicals.py
print('=== 11. checks ===')
ue('check_block.py', 'geometry + party walls')
ue('gap_check2.py',  'no hollow facades')
# The whole-level invariant suite runs LAST, after every dressing pass, because
# most of what it catches is dressing: lamps in the carriageway, planting that
# does not fit its lot, default material slots. It self-tests before it reports.
ue('invariants.py',  'invariants')
print('\nbuild complete')
